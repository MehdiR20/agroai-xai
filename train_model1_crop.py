# =============================================================================
# ADVANCED MODEL 1 — CROP RECOMMENDATION SYSTEM
# FINAL YEAR PROJECT VERSION
# WITH SHAP + LIME + FULL ML PIPELINE
# =============================================================================

import warnings
warnings.filterwarnings('ignore')

import os
import sys
import joblib
import shap
import lime
import lime.lime_tabular

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from scipy.stats import randint

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_val_score,
    GridSearchCV,
    RandomizedSearchCV
)

from sklearn.preprocessing import (
    LabelEncoder,
    StandardScaler
)

from sklearn.feature_selection import SelectKBest, f_classif

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.svm import SVC

import xgboost as xgb


# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(BASE_DIR, 'datasets', 'Crop_recommendation_augmented.csv')

MODELS_DIR = os.path.join(BASE_DIR, 'models')
FIGURES_DIR = os.path.join(BASE_DIR, 'figures')
XAI_DIR = os.path.join(BASE_DIR, 'xai')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(XAI_DIR, exist_ok=True)


# =============================================================================
# FIGURE SAVE FUNCTION
# =============================================================================

fig_counter = [0]


def save_fig(name):
    fig_counter[0] += 1
    path = os.path.join(FIGURES_DIR, f'{fig_counter[0]:02d}_{name}.png')
    plt.savefig(path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'[Saved Figure] {path}')

# =============================================================================
# LOAD DATASET
# =============================================================================

print('=' * 80)
print('ADVANCED CROP RECOMMENDATION SYSTEM')
print('=' * 80)

print('\n[1] Loading dataset...')

df = pd.read_csv(DATASET_PATH)


# =============================================================================
# BASIC CLEANING
# =============================================================================

print('\n[2] Data Cleaning...')

# Remove unnamed column if exists
if 'Unnamed: 0' in df.columns:
    df.drop(columns=['Unnamed: 0'], inplace=True)

# Standardize labels
if 'label' in df.columns:
    target_col = 'label'
elif 'Crop' in df.columns:
    target_col = 'Crop'
else:
    raise Exception('Target column not found.')


df[target_col] = df[target_col].astype(str).str.lower().str.strip()

# Remove duplicates
before = len(df)
df.drop_duplicates(inplace=True)
after = len(df)

print(f'Removed duplicates: {before - after}')

# Missing values
print('\nMissing values:')
print(df.isnull().sum())

# Fill missing values
for col in df.columns:
    if df[col].dtype != 'object':
        df[col].fillna(df[col].median(), inplace=True)

# =============================================================================
# OUTLIER REMOVAL USING IQR
# =============================================================================

print('\n[3] Removing outliers using IQR...')

numeric_cols = [c for c in df.columns if c != target_col]

for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    df = df[(df[col] >= lower) & (df[col] <= upper)]

print(f'Dataset shape after outlier removal: {df.shape}')


# =============================================================================
# EXPLORATORY DATA ANALYSIS
# =============================================================================

print('\n[4] Generating EDA graphs...')

# Class distribution
plt.figure(figsize=(14, 6))
sns.countplot(x=df[target_col], order=df[target_col].value_counts().index)
plt.xticks(rotation=90)
plt.title('Crop Class Distribution')
plt.tight_layout()
save_fig('class_distribution')


# Correlation heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='viridis')
plt.title('Feature Correlation Heatmap')
save_fig('correlation_heatmap')


# Histograms
for col in numeric_cols:
    plt.figure(figsize=(6, 4))
    sns.histplot(df[col], kde=True)
    plt.title(f'{col} Distribution')
    save_fig(f'{col}_distribution')


# Boxplots
for col in numeric_cols:
    plt.figure(figsize=(6, 4))
    sns.boxplot(x=df[col])
    plt.title(f'{col} Boxplot')
    save_fig(f'{col}_boxplot')

# =============================================================================

# Encode labels
encoder = LabelEncoder()
df['crop_encoded'] = encoder.fit_transform(df[target_col])

# Features / target
X = df.drop(columns=[target_col, 'crop_encoded'])
y = df['crop_encoded']

feature_names = X.columns.tolist()


# =============================================================================
# DATA SPLIT  (must happen BEFORE feature selection to prevent data leakage)
# =============================================================================

print('\n[6] Train / Validation / Test Split...')

# 70 train / 15 validation / 15 test
X_train, X_temp, y_train, y_temp = train_test_split(
    X,
    y,
    test_size=0.30,
    stratify=y,
    random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.50,
    stratify=y_temp,
    random_state=42
)

print(f'Train: {X_train.shape}')
print(f'Validation: {X_val.shape}')
print(f'Test: {X_test.shape}')

# =============================================================================
# FEATURE SELECTION  (fit ONLY on training data — no leakage from val/test)
# =============================================================================

print('\n[7] Feature Selection (fit on training set only)...')

selector = SelectKBest(score_func=f_classif, k='all')
selector.fit(X_train, y_train)          # <-- training data only

feature_scores = pd.DataFrame({
    'Feature': feature_names,
    'Score': selector.scores_
}).sort_values(by='Score', ascending=False)

print(feature_scores)

# Plot feature scores
plt.figure(figsize=(8, 5))
sns.barplot(data=feature_scores, x='Score', y='Feature')
plt.title('Feature Importance Scores (Training Set)')
save_fig('feature_selection_scores')

# =============================================================================
# DATASET AUGMENTATION  (training set ONLY — applied after split to avoid leakage)
# Gaussian noise injection: doubles the training set by adding slightly
# perturbed copies of every training sample, preserving class balance.
# Val / Test sets are left completely untouched.
# =============================================================================

print('\n[8] Dataset Augmentation (training set only)...')

rng = np.random.default_rng(seed=42)

X_train_arr = X_train.values.astype(float)
y_train_arr = y_train.values

# Add Gaussian noise scaled to 2 % of each feature's training std
noise_scale = 0.02
col_stds    = X_train_arr.std(axis=0)
noise       = rng.normal(0, noise_scale * col_stds, size=X_train_arr.shape)
X_aug       = X_train_arr + noise
y_aug       = y_train_arr.copy()

# Stack original + augmented → doubled training set
X_train_aug = np.vstack([X_train_arr, X_aug])
y_train_aug = np.concatenate([y_train_arr, y_aug])

# Shuffle combined set
shuffle_idx = rng.permutation(len(X_train_aug))
X_train_aug = X_train_aug[shuffle_idx]
y_train_aug = y_train_aug[shuffle_idx]

print(f'Training set before augmentation : {X_train.shape}')
print(f'Training set after  augmentation : {X_train_aug.shape}')
print('(Validation and Test sets unchanged)')

# Convert back to DataFrame so downstream code keeps feature names
X_train = pd.DataFrame(X_train_aug, columns=feature_names)
y_train = pd.Series(y_train_aug, name=y.name)

# =============================================================================
# NORMALIZATION
# =============================================================================

print('\n[9] Feature Scaling...')

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# =============================================================================
# MODELS
# =============================================================================

print('\n[9] Building Models...')

models = {
    'Decision Tree': DecisionTreeClassifier(random_state=42),

    'KNN': KNeighborsClassifier(),

    'Random Forest': RandomForestClassifier(
        random_state=42,
        n_jobs=-1
    ),

    'SVM': SVC(
        probability=True,
        random_state=42
    ),

    'XGBoost': xgb.XGBClassifier(
        random_state=42,
        verbosity=0,
        n_jobs=-1
    )
}

# =============================================================================
# HYPERPARAMETER TUNING
# =============================================================================
print('\n[10] Hyperparameter Optimization...')

# Random Forest
rf_search = RandomizedSearchCV(
    RandomForestClassifier(random_state=42),
    {
        'n_estimators': randint(100, 400),
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': randint(2, 10)
    },
    n_iter=15,
    cv=5,
    n_jobs=-1,
    scoring='accuracy',
    random_state=42
)

rf_search.fit(X_train_scaled, y_train)
models['Random Forest'] = rf_search.best_estimator_

# SVM
svm_search = GridSearchCV(
    SVC(probability=True),
    {
        'C': [0.1, 1, 10],
        'kernel': ['rbf', 'linear'],
        'gamma': ['scale', 'auto']
    },
    cv=5,
    n_jobs=-1,
    scoring='accuracy'
)

svm_search.fit(X_train_scaled, y_train)
models['SVM'] = svm_search.best_estimator_

# XGBoost
xgb_search = RandomizedSearchCV(
    xgb.XGBClassifier(random_state=42, verbosity=0),
    {
        'n_estimators': randint(100, 300),
        'max_depth': randint(3, 10),
        'learning_rate': [0.01, 0.05, 0.1, 0.2]
    },
    n_iter=10,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    random_state=42
)

xgb_search.fit(X_train_scaled, y_train)
models['XGBoost'] = xgb_search.best_estimator_


# =============================================================================
# MODEL EVALUATION
# =============================================================================

print('\n[11] Training + Evaluation...')

results = {}

best_model = None
best_name = None
best_accuracy = 0
best_predictions = None

kfold = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

for name, model in models.items():

    print(f'\nTraining {name}...')

    # Cross validation
    cv_scores = cross_val_score(
        model,
        X_train_scaled,
        y_train,
        cv=kfold,
        scoring='accuracy',
        n_jobs=-1
    )

    # Train
    model.fit(X_train_scaled, y_train)

    # Validation predictions
    val_pred = model.predict(X_val_scaled)

    val_acc = accuracy_score(y_val, val_pred)
    val_f1 = f1_score(y_val, val_pred, average='weighted')

    # Test predictions
    test_pred = model.predict(X_test_scaled)

    test_acc = accuracy_score(y_test, test_pred)
    test_f1 = f1_score(y_test, test_pred, average='weighted')
    test_precision = precision_score(y_test, test_pred, average='weighted')
    test_recall = recall_score(y_test, test_pred, average='weighted')

    results[name] = {
        'validation_accuracy': val_acc,
        'test_accuracy': test_acc,
        'f1_score': test_f1,
        'precision': test_precision,
        'recall': test_recall,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std()
    }

    print(f'Validation Accuracy: {val_acc:.4f}')
    print(f'Test Accuracy: {test_acc:.4f}')
    print(f'F1 Score: {test_f1:.4f}')
    print(f'CV10 Accuracy: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}')

    if test_acc > best_accuracy:
        best_accuracy = test_acc
        best_model = model
        best_name = name
        best_predictions = test_pred

# =============================================================================
# BEST MODEL
# =============================================================================

print('\n' + '=' * 80)
print(f'BEST MODEL: {best_name}')
print(f'BEST ACCURACY: {best_accuracy * 100:.2f}%')
print('=' * 80)

# =============================================================================
# CLASSIFICATION REPORT
# =============================================================================

print('\nClassification Report:')
print(classification_report(y_test, best_predictions))

# =============================================================================
# MODEL COMPARISON GRAPH
# =============================================================================

comparison_df = pd.DataFrame(results).T

plt.figure(figsize=(10, 6))
sns.barplot(x=comparison_df.index, y=comparison_df['test_accuracy'])
plt.xticks(rotation=20)
plt.ylabel('Accuracy')
plt.title('Model Comparison')
save_fig('model_comparison')

# =============================================================================
# CONFUSION MATRIX
# =============================================================================

all_labels = encoder.transform(encoder.classes_)
 
cm = confusion_matrix(y_test, best_predictions, labels=all_labels)
 
plt.figure(figsize=(14, 12))
sns.heatmap(
    cm,
    cmap='Blues',
    xticklabels=encoder.classes_,
    yticklabels=encoder.classes_
)
 
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title(f'Confusion Matrix — {best_name}')
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.tight_layout()
save_fig('confusion_matrix')

# =============================================================================
# SHAP EXPLAINABILITY
# =============================================================================
print('\n[12] SHAP Explainability...')

if best_name in ['Random Forest', 'XGBoost']:
    # FIX: Use scaled data for SHAP to match model training
    X_sample_scaled = X_test_scaled[:200]
    X_sample_df = pd.DataFrame(X_sample_scaled, columns=feature_names)

    # TreeExplainer is optimized for RF/XGBoost
    explainer = shap.TreeExplainer(best_model)
    shap_values = explainer(X_sample_df)

    mean_abs_shap = np.abs(shap_values.values).mean(axis=(0, 2))

    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': mean_abs_shap
    }).sort_values('Importance', ascending=False)

    plt.figure(figsize=(8,5))
    sns.barplot(data=importance_df, x='Importance', y='Feature')
    plt.title('Global SHAP Feature Importance')
    save_fig('shap_bar')
    
    # Reassign X_sample so metrics in block 15 use the scaled dataframe
    X_sample = X_sample_df

else:
    X_sample_scaled = X_test_scaled[:200]
    X_sample_df = pd.DataFrame(X_sample_scaled, columns=feature_names)
    
    explainer = shap.KernelExplainer(best_model.predict_proba, X_train_scaled[:100])
    shap_values = explainer.shap_values(X_sample_df)

    shap.summary_plot(shap_values, X_sample_df, feature_names=feature_names, show=False)
    save_fig('shap_summary')
    
    X_sample = X_sample_df
# =============================================================================
# LIME EXPLAINABILITY
# =============================================================================

print('\n[13] LIME Explainability...')

lime_explainer = lime.lime_tabular.LimeTabularExplainer(
    training_data=X_train_scaled,
    feature_names=feature_names,
    class_names=list(encoder.classes_),
    mode='classification'
)

exp = lime_explainer.explain_instance(
    X_test_scaled[0],
    best_model.predict_proba,
    num_features=len(feature_names)
)

fig = exp.as_pyplot_figure()
plt.tight_layout()
save_fig('lime_explanation')

# =============================================================================
# SAVE EVERYTHING
# =============================================================================

print('\n[14] Saving system...')

save_data = {

    'best_model': best_model,
    'best_model_name': best_name,

    'all_models': models,

    'scaler': scaler,
    'encoder': encoder,

    'feature_names': feature_names,

    'results': results,

    'X_train': X_train,
    'X_train_scaled': X_train_scaled,

    'accuracy': best_accuracy
}

save_path = os.path.join(
    MODELS_DIR,
    'model1_crop_recommendation.pkl'
)

joblib.dump(save_data, save_path)

print(f'System saved to: {save_path}')

print('\nSYSTEM READY.')


# =============================================================================
# [15] XAI METRICS & PREMIUM VISUALIZATIONS
# =============================================================================
try:
    print('\n[15] XAI Metrics & Advanced Visualizations...')
    if 'shap_values' in locals():
        # 1. Safely extract the underlying numpy array
        shap_array = shap_values.values if hasattr(shap_values, 'values') else np.array(shap_values)
        
        # 2. Compute Global Importance across all classes if multiclass
        if shap_array.ndim == 3:
            global_importance = np.abs(shap_array).mean(axis=(0, 2))
        else:
            global_importance = np.abs(shap_array).mean(axis=0)

        # ---------------------------------------------------------
        # A. AGREEMENT (SHAP vs LIME - Local Instance 0)
        # ---------------------------------------------------------
        print("Calculating Agreement...")
        instance_index = 0
        
        # Extract local SHAP importance for instance 0
        if shap_array.ndim == 3:
            local_shap_importance = np.abs(shap_array[instance_index]).mean(axis=1)
        else:
            local_shap_importance = np.abs(shap_array[instance_index])
            
        shap_top_local = pd.DataFrame({
            'Feature': feature_names, 
            'Importance': local_shap_importance
        }).sort_values('Importance', ascending=False)
        
        # Clean and parse LIME output text strings back into base feature names
        lime_features_raw = dict(exp.as_list())
        lime_top3_raw = [x[0] for x in sorted(lime_features_raw.items(), key=lambda z: abs(z[1]), reverse=True)[:3]]
        
        lime_top3_clean = []
        for raw_str in lime_top3_raw:
            for feat in feature_names:
                if feat in raw_str:
                    lime_top3_clean.append(feat)
                    break
                    
        comparison = pd.DataFrame({
            'SHAP_Top3': shap_top_local['Feature'].head(3).tolist(),
            # Prevent dimensional padding error if an extraction rule is missed
            'LIME_Top3': lime_top3_clean + [None] * (3 - len(lime_top3_clean)) 
        })
        
        comparison.to_csv(os.path.join(XAI_DIR, 'shap_lime_top3_premium.csv'), index=False)
        
        agreement = len(set(comparison['SHAP_Top3']).intersection(set(comparison['LIME_Top3']))) / 3.0
        print(f'Agreement (Top 3 Local) = {agreement:.2f}')

        # ---------------------------------------------------------
        # B. SPARSITY
        # ---------------------------------------------------------
        print("Calculating Sparsity...")
        total_importance = global_importance.sum() + 1e-9
        sparsity = np.sort(global_importance)[::-1][:3].sum() / total_importance
        print(f'Sparsity (Top 3 Features) = {sparsity:.4f}')

        # ---------------------------------------------------------
        # C. CONSISTENCY
        # ---------------------------------------------------------
        print("Calculating Consistency...")
        if shap_array.ndim == 3:
            shap_matrix_cons = shap_array.reshape(shap_array.shape[0], -1)
        else:
            shap_matrix_cons = shap_array

        nbrs = NearestNeighbors(n_neighbors=min(5, len(X_sample))).fit(X_sample)
        idx = nbrs.kneighbors(return_distance=False)
        
        sims = []
        for i, row in enumerate(idx):
            for j in row[1:]: 
                vec_i = shap_matrix_cons[i].reshape(1, -1)
                vec_j = shap_matrix_cons[j].reshape(1, -1)
                
                if np.linalg.norm(vec_i) > 0 and np.linalg.norm(vec_j) > 0:
                    sim = cosine_similarity(vec_i, vec_j)[0][0]
                    sims.append(sim)
                    
        if sims:
            consistency = np.mean(sims)
            print(f'Consistency = {consistency:.4f}')
        else:
            print('Consistency = Could not be calculated (empty similarities)')

        # ---------------------------------------------------------
        # PREMIUM VISUALIZATIONS FOR THESIS REPORT
        # ---------------------------------------------------------
        print("Generating Premium Figures...")
        import copy
        
        # Slice original unscaled dataframe matching the SHAP evaluation set size
        X_unscaled_sample = X_test.iloc[:200]
        
        # 1. Premium Summary Bar Plot with Crop Names mapped to colors
        try:
            shap_plot_obj = copy.deepcopy(shap_values)
            shap_plot_obj.data = X_unscaled_sample.values
            
            plt.figure(figsize=(11, 7))
            shap.summary_plot(
                shap_plot_obj, 
                X_unscaled_sample, 
                class_names=encoder.classes_,
                show=False
            )
            plt.title("Global Feature Contribution Across All Crops", fontsize=14, pad=20)
            plt.tight_layout()
            save_fig('shap_summary_premium')
            plt.close()
        except Exception as e_vis1:
            print("Notice: Premium Summary Plot fall-back executed:", e_vis1)
            try:
                plt.figure(figsize=(10, 6))
                shap.summary_plot(
                    shap_values,
                    X_sample,
                    class_names=encoder.classes_,
                    show=False
                )
                save_fig('shap_summary_fixed')
                plt.close()
            except Exception:
                pass
            
            
        # 2. Premium Dependence Plot targeting the top agricultural feature
        try:
            top_feature_idx = np.argmax(global_importance)
            top_feature_name = feature_names[top_feature_idx]
            
            # Map Class Index 0 back to its human-readable crop name
            target_class_idx = 0 
            target_crop_name = LabelEncoder.classes_[target_class_idx]
            
            plt.figure(figsize=(8, 5))
            shap.dependence_plot(
                top_feature_name, 
                shap_array[:, :, target_class_idx] if shap_array.ndim == 3 else shap_array, 
                X_unscaled_sample, 
                show=False
            )
            plt.title(f"Dependence Plot: How {top_feature_name} Impacts {target_crop_name.upper()} Predictions", fontsize=12, pad=15)
            plt.tight_layout()
            save_fig('shap_dependence_premium')
            plt.close()
        except Exception as e_vis2:
            print("Notice: Premium Dependence Plot fall-back executed:", e_vis2)
            try:
                top_feature = feature_names[np.argmax(global_importance)]
                plot_vals = shap_array[:, :, 0] if shap_array.ndim == 3 else shap_array
                shap.dependence_plot(top_feature, plot_vals, X_sample, show=False)
                save_fig('shap_dependence_fixed')
                plt.close()
            except Exception:
                pass

except Exception as e:
    print('XAI metrics error:', e)  