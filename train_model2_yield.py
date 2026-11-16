# =============================================================================
#  MODEL 2 — CROP YIELD PREDICTION
#  Cascade pipeline: Model 1 (crop) → Model 2 (yield prediction)
#  Compares Random Forest vs XGBoost — auto-selects best
# =============================================================================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import joblib
import os
import sys
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_score, KFold, learning_curve
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
    print("✅ XGBoost available")
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not installed — pip install xgboost")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

print("=" * 70)
print("MODEL 2 — CROP YIELD PREDICTION SYSTEM")
print("=" * 70)


# =============================================================================
#  PATHS
# =============================================================================
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "datasets", "yield_df.csv")
MODELS_DIR   = os.path.join(BASE_DIR, "models")
FIGURES_DIR  = os.path.join(BASE_DIR, "figures")
os.makedirs(MODELS_DIR,  exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

fig_counter = [0]
def save_fig(name):
    fig_counter[0] += 1
    path = os.path.join(FIGURES_DIR, f"m2_{fig_counter[0]:02d}_{name}.png")
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close('all')
    print(f"  [Figure saved] {path}")


# =============================================================================
#  CROP MAPPING — bridges Model 1's 22 crops → yield dataset's 10 crops
#  Mapping rationale: botanical family + climate similarity
# =============================================================================

CROP_MAPPING = {
    # Direct matches
    "rice": "Rice, paddy", "maize": "Maize", "wheat": "Wheat", "potato": "Potatoes",
    # Legumes → Soybeans
    "chickpea": "Soybeans", "kidneybeans": "Soybeans", "pigeonpeas": "Soybeans",
    "mothbeans": "Soybeans", "mungbean": "Soybeans", "blackgram": "Soybeans",
    "lentil": "Soybeans",
    # Tropical fruits → Plantains
    "banana": "Plantains and others", "mango": "Plantains and others",
    "papaya": "Plantains and others", "coconut": "Plantains and others",
    "pomegranate": "Plantains and others", "orange": "Plantains and others",
    # Temperate fruits → Sweet potatoes
    "grapes": "Sweet potatoes", "watermelon": "Sweet potatoes",
    "muskmelon": "Sweet potatoes", "apple": "Sweet potatoes",
    # Cash crops & others
    "sugarcane": "Cassava", "cotton": "Cassava", "jute": "Sorghum",
    "tomato": "Potatoes", "coffee": "Sorghum",
}

DIRECT_CROPS = {"rice", "maize", "wheat", "potato"}


def map_crop(crop_name: str):
    """Map a Model 1 crop to its closest Model 2 yield crop."""
    crop_lower = crop_name.lower().strip()
    mapped = CROP_MAPPING.get(crop_lower, "Maize")
    is_direct = crop_lower in DIRECT_CROPS
    return mapped, is_direct


# =============================================================================
#  1. LOAD & PREPROCESS
# =============================================================================

print("\n[1] Loading yield dataset...")
df = pd.read_csv(DATASET_PATH)

if 'Unnamed: 0' in df.columns:
    df.drop(columns=['Unnamed: 0'], inplace=True)

df.rename(columns={
    'Area':                          'country',
    'Item':                          'crop',
    'Year':                          'year',
    'hg/ha_yield':                   'yield_hg_ha',
    'average_rain_fall_mm_per_year': 'rainfall_mm',
    'pesticides_tonnes':             'pesticides_tonnes',
    'avg_temp':                      'avg_temp_c',
}, inplace=True)

# Convert hg/ha → kg/ha
df['yield_kg_ha'] = df['yield_hg_ha'] / 10
print(f"  Rows: {df.shape[0]} | Crops: {df['crop'].nunique()} | "
      f"Countries: {df['country'].nunique()} | Years: {df['year'].min()}-{df['year'].max()}")
print(f"  Yield range: {df['yield_kg_ha'].min():.0f} – {df['yield_kg_ha'].max():.0f} kg/ha")

# Outlier removal (top 0.5%)
q995 = df['yield_kg_ha'].quantile(0.995)
df = df[df['yield_kg_ha'] <= q995].reset_index(drop=True)
print(f"  After outlier removal: {df.shape[0]} rows (cap = {q995:.0f} kg/ha)")


# =============================================================================
#  2. FEATURE ENGINEERING  (analytics aggregates only — no model fitting here)
# =============================================================================

print("\n[2] Feature engineering (analytics aggregates — full dataset, no model fitting)...")
# NOTE: These encoded columns on the full df are used ONLY for computing
#       country/yield averages saved as lookup artifacts.  All model
#       fitting happens exclusively on the training split below.
_le_crop_all    = LabelEncoder().fit(df['crop'])
_le_country_all = LabelEncoder().fit(df['country'])
df['crop_encoded']    = _le_crop_all.transform(df['crop'])
df['country_encoded'] = _le_country_all.transform(df['country'])

print(f"  Crops in dataset:    {df['crop'].nunique()}")
print(f"  Countries in dataset: {df['country'].nunique()}")


# =============================================================================
#  3. SPLIT (70/15/15) first — then encode to prevent data leakage
# =============================================================================

print("\n[3] Splitting Train/Val/Test (70/15/15) before encoding...")

# Split on raw (unencoded) features to avoid leakage
FEATURES_RAW = ['crop', 'country', 'year', 'rainfall_mm', 'pesticides_tonnes', 'avg_temp_c']
TARGET        = 'yield_kg_ha'

X_raw = df[FEATURES_RAW]
y     = df[TARGET]

X_train_raw, X_temp_raw, y_train, y_temp = train_test_split(
    X_raw, y, test_size=0.30, random_state=42
)
X_val_raw, X_test_raw, y_val, y_test = train_test_split(
    X_temp_raw, y_temp, test_size=0.50, random_state=42
)
print(f"  Train: {X_train_raw.shape[0]} | Val: {X_val_raw.shape[0]} | Test: {X_test_raw.shape[0]}")

# Fit encoders ONLY on training data (no leakage from val/test)
le_crop    = LabelEncoder()
le_country = LabelEncoder()

le_crop.fit(X_train_raw['crop'])
le_country.fit(X_train_raw['country'])

def safe_encode(encoder, series):
    """Encode series; unseen labels (in val/test but not train) map to 0."""
    known = set(encoder.classes_)
    return series.map(lambda v: encoder.transform([v])[0] if v in known else 0)

def encode_split(X_raw_split):
    X_enc = X_raw_split.copy()
    X_enc['crop_encoded']    = safe_encode(le_crop,    X_enc['crop'])
    X_enc['country_encoded'] = safe_encode(le_country, X_enc['country'])
    return X_enc[FEATURES]

FEATURES = ['crop_encoded', 'country_encoded', 'year',
            'rainfall_mm', 'pesticides_tonnes', 'avg_temp_c']

X_train = encode_split(X_train_raw)
X_val   = encode_split(X_val_raw)
X_test  = encode_split(X_test_raw)

print(f"  Crops in encoder (train): {le_crop.classes_.tolist()}")
print(f"  Countries in encoder (train): {len(le_country.classes_)}")

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)   # fit on train only
X_val_sc   = scaler.transform(X_val)
X_test_sc  = scaler.transform(X_test)


# =============================================================================
#  4. TRAINING — Random Forest vs XGBoost
# =============================================================================

print("\n[4] Training models...")

def evaluate(model, X_tr, y_tr, X_te, y_te, name):
    model.fit(X_tr, y_tr)
    y_pred_train = model.predict(X_tr)
    y_pred_test  = model.predict(X_te)
    def m(t, p):
        return (mean_absolute_error(t, p),
                np.sqrt(mean_squared_error(t, p)),
                r2_score(t, p))
    tr = m(y_tr, y_pred_train)
    te = m(y_te, y_pred_test)
    print(f"\n  [{name}]")
    print(f"  {'Metric':<8} {'Train':>12} {'Test':>12}")
    print(f"  {'MAE':<8} {tr[0]:>12.2f} {te[0]:>12.2f}  kg/ha")
    print(f"  {'RMSE':<8} {tr[1]:>12.2f} {te[1]:>12.2f}  kg/ha")
    print(f"  {'R²':<8} {tr[2]:>12.4f} {te[2]:>12.4f}")
    return {
        'model': model, 'name': name,
        'train': {'mae': tr[0], 'rmse': tr[1], 'r2': tr[2]},
        'test':  {'mae': te[0], 'rmse': te[1], 'r2': te[2]},
        'y_pred_test': y_pred_test,
    }

# Random Forest
rf_result = evaluate(
    RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1),
    X_train_sc, y_train, X_test_sc, y_test, "Random Forest"
)
candidates = [rf_result]

# XGBoost
if XGBOOST_AVAILABLE:
    xgb_result = evaluate(
        xgb.XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6,
                         subsample=0.8, colsample_bytree=0.8,
                         random_state=42, verbosity=0, n_jobs=-1),
        X_train_sc, y_train, X_test_sc, y_test, "XGBoost"
    )
    candidates.append(xgb_result)


# =============================================================================
#  5. CROSS-VALIDATION (K=10)
# =============================================================================

print("\n[5] Cross-validation (K=10)...")
kf = KFold(n_splits=10, shuffle=True, random_state=42)
for r in candidates:
    cv_r2  = cross_val_score(r['model'], X_train_sc, y_train, cv=kf,
                             scoring='r2', n_jobs=-1)
    cv_mae = -cross_val_score(r['model'], X_train_sc, y_train, cv=kf,
                              scoring='neg_mean_absolute_error', n_jobs=-1)
    r['cv_r2_mean']  = cv_r2.mean()
    r['cv_r2_std']   = cv_r2.std()
    r['cv_mae_mean'] = cv_mae.mean()
    print(f"  [{r['name']}] CV-10 R² = {cv_r2.mean():.4f} ± {cv_r2.std():.4f} | "
          f"MAE = {cv_mae.mean():.2f} kg/ha")


# =============================================================================
#  6. SELECT BEST + EVALUATION PLOTS
# =============================================================================

best_result = max(candidates, key=lambda r: r['cv_r2_mean'])
best_model  = best_result['model']
best_name   = best_result['name']
print(f"\n🏆 BEST: {best_name} (R²={best_result['test']['r2']:.4f}, "
      f"MAE={best_result['test']['mae']:.0f} kg/ha)")

# Plots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(f"Model 2 — {best_name}", fontsize=14, fontweight='bold')
y_pred_best = best_result['y_pred_test']

ax = axes[0, 0]
ax.scatter(y_test, y_pred_best, alpha=0.3, color='#2ecc71', s=10)
lims = [min(y_test.min(), y_pred_best.min()), max(y_test.max(), y_pred_best.max())]
ax.plot(lims, lims, 'r--', linewidth=1.5)
ax.set_xlabel("Actual (kg/ha)"); ax.set_ylabel("Predicted (kg/ha)")
ax.set_title("Actual vs Predicted")
ax.text(0.05, 0.92, f"R²={best_result['test']['r2']:.4f}",
        transform=ax.transAxes, fontsize=10, color='darkgreen', fontweight='bold')

ax = axes[0, 1]
residuals = np.array(y_test) - y_pred_best
ax.scatter(y_pred_best, residuals, alpha=0.3, color='#3498db', s=10)
ax.axhline(0, color='red', linestyle='--')
ax.set_xlabel("Predicted"); ax.set_ylabel("Residual"); ax.set_title("Residuals")

ax = axes[1, 0]
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    sorted_idx  = np.argsort(importances)
    ax.barh([FEATURES[i] for i in sorted_idx],
            importances[sorted_idx], color='#9b59b6', alpha=0.85)
    ax.set_title(f"Feature Importance — {best_name}")

ax = axes[1, 1]
names  = [r['name'] for r in candidates]
scores = [r['test']['r2'] for r in candidates]
colors = ['#2ecc71' if n == best_name else '#95a5a6' for n in names]
bars = ax.bar(names, scores, color=colors, alpha=0.85)
ax.set_ylim(0, 1); ax.set_ylabel("R² (Test)"); ax.set_title("Model Comparison")
for bar, val in zip(bars, scores):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.01,
            f'{val:.4f}', ha='center', fontweight='bold')
plt.tight_layout()
save_fig("evaluation")


# =============================================================================
#  7. SAVE MODEL 2 ARTIFACTS
# =============================================================================

print("\n[6] Saving Model 2...")

# Compute country yield averages — useful for sanity-checking predictions
country_yield_avg = (
    df.groupby(['country', 'crop'])['yield_kg_ha']
      .agg(['mean', 'std', 'min', 'max'])
      .reset_index()
)

# Rainfall/temp averages per country — useful as fallback if API fails
country_climate_avg = (
    df.groupby('country')[['rainfall_mm', 'avg_temp_c', 'pesticides_tonnes']]
      .mean()
      .reset_index()
)

artifacts = {
    'best_model':           best_model,
    'best_name':            best_name,
    'scaler':               scaler,
    'le_crop':              le_crop,
    'le_country':           le_country,
    'features':             FEATURES,
    'crop_mapping':         CROP_MAPPING,
    'direct_crops':         DIRECT_CROPS,
    'yield_crops':          le_crop.classes_.tolist(),
    'metrics':              best_result,
    'all_results':          candidates,
    'country_yield_avg':    country_yield_avg,
    'country_climate_avg':  country_climate_avg,
    'min_year':             int(df['year'].min()),
    'max_year':             int(df['year'].max()),
}

save_file = os.path.join(MODELS_DIR, "model2_yield_system.pkl")
joblib.dump(artifacts, save_file)
print(f"✅ Saved: {save_file}")


# =============================================================================
#  8. CASCADE PREDICTION FUNCTION (for testing)
# =============================================================================

def predict_yield_cascade(crop_from_model1, country, rainfall_mm,
                          pesticides_tonnes, avg_temp_c, year=2024, verbose=True):
    """Cascade prediction: Model 1 crop → Model 2 yield."""
    mapped_crop, is_direct = map_crop(crop_from_model1)
    crop_enc    = (le_crop.transform([mapped_crop])[0]
                   if mapped_crop in le_crop.classes_ else 0)
    country_enc = (le_country.transform([country])[0]
                   if country in le_country.classes_ else 0)

    inp     = np.array([[crop_enc, country_enc, year,
                         rainfall_mm, pesticides_tonnes, avg_temp_c]])
    inp_sc  = scaler.transform(inp)
    yield_kg = max(0, float(best_model.predict(inp_sc)[0]))
    mae      = best_result['test']['mae']

    if verbose:
        print(f"\n{'─'*60}")
        print(f"  Crop: {crop_from_model1} → {mapped_crop} | Country: {country} | Year: {year}")
        print(f"  IoT: temp={avg_temp_c}°C rain={rainfall_mm}mm pest={pesticides_tonnes}t")
        print(f"  📊 Yield: {yield_kg:,.0f} kg/ha = {yield_kg/1000:.2f} t/ha")
        print(f"  CI: [{max(0, yield_kg-mae):,.0f} — {yield_kg+mae:,.0f}] kg/ha")
        print(f"{'─'*60}")

    return {
        'mapped_crop':     mapped_crop,
        'is_direct_match': is_direct,
        'yield_kg_ha':     round(yield_kg, 2),
        'yield_tonnes_ha': round(yield_kg / 1000, 4),
        'ci_low':          max(0, yield_kg - mae),
        'ci_high':         yield_kg + mae,
        'year':            year,
    }


# Demo tests
print("\n[7] Demo cascade predictions:")
test_cases = [
    ("rice",     "India",   2034, 150.5, 26.5),
    ("coffee",   "Kenya",    900,  12.0, 22.0),
    ("wheat",    "France",   650, 200.0, 12.0),
    ("chickpea", "Algeria",  350,   5.0, 18.0),
]
for crop, country, rain, pest, temp in test_cases:
    predict_yield_cascade(crop, country, rain, pest, temp)

print("\n" + "=" * 70)
print(f"✅ MODEL 2 READY — {best_name}")
print(f"   R²={best_result['test']['r2']:.4f} | "
      f"MAE={best_result['test']['mae']:.0f} kg/ha")
print("=" * 70)


# =============================================================================
# LEARNING CURVE
# =============================================================================
try:
    print('\n[Learning Curve]')
    train_sizes, train_scores, val_scores = learning_curve(
        best_model, X_train_sc, y_train,
        cv=5, scoring='r2', n_jobs=-1,
        train_sizes=np.linspace(0.1,1.0,10)
    )
    plt.figure(figsize=(8,5))
    plt.plot(train_sizes, train_scores.mean(axis=1), marker='o', label='Training R2')
    plt.plot(train_sizes, val_scores.mean(axis=1), marker='s', label='Validation R2')
    plt.xlabel('Training Samples')
    plt.ylabel('R2')
    plt.title(f'Learning Curve - {best_name}')
    plt.legend()
    plt.grid(True)
    save_fig('learning_curve')
except Exception as e:
    print('Learning curve error',e)
