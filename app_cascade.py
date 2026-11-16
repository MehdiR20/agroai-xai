# =============================================================================
#  AGROAI — SMART FARMING DASHBOARD
#  - Interactive map (Folium): farmer clicks farm location
#  - SoilGrids API:    auto-fetches soil N, P, K, pH for that location
#  - Open-Meteo API:   auto-fetches temperature, humidity, wind, rainfall
#  - 5-year yield forecast per chosen year
#  - Multilingual: English / French / Arabic
#  - Modern, minimal design — built for farmers, not engineers
#
#  Run:  streamlit run app_cascade.py
# =============================================================================

import shap
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
import random
from datetime import datetime

from api_services import (
    fetch_soil_data,
    fetch_current_weather,
    get_iot_simulated_weather,
    COUNTRY_CENTERS,
)
from translations import t, get_text_direction, translate_crop


# =============================================================================
#  PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="AgroAI — Smart Farming Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =============================================================================
#  GLOBAL STATE INIT
# =============================================================================

DEFAULT_LANG = 'en'

for k, default in [
    ('lang',         DEFAULT_LANG),
    ('clicked_lat',  None),
    ('clicked_lon',  None),
    ('country',      'Algeria'),
    ('soil_data',    None),
    ('weather_data', None),
    ('manual_mode',  False),
    ('prediction',   None),
    ('soil_loaded',  False),
]:
    if k not in st.session_state:
        st.session_state[k] = default

LANG = st.session_state['lang']
DIR  = get_text_direction(LANG)


# =============================================================================
#  CUSTOM CSS — modern, clean, farmer-friendly
# =============================================================================

st.markdown(f"""
<style>
    /* Hide default Streamlit chrome */
    #MainMenu, header, footer {{visibility: hidden;}}
    .block-container {{padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1280px;}}

    /* RTL support for Arabic */
    {'.main-content { direction: rtl; text-align: right; }' if DIR == 'rtl' else ''}

    /* Hero */
    .hero {{
        background: linear-gradient(135deg, #16a34a 0%, #15803d 50%, #166534 100%);
        color: white;
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(22, 163, 74, 0.2);
    }}
    .hero h1 {{
        font-size: 2.5rem; font-weight: 800;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }}
    .hero p {{
        font-size: 1.1rem; opacity: 0.95;
        margin: 0; font-weight: 400;
    }}
    .hero-icon {{font-size: 3rem; margin-bottom: 0.5rem;}}

    /* Step cards */
    .step-card {{
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .step-number {{
        display: inline-block;
        background: #16a34a;
        color: white;
        width: 32px; height: 32px;
        border-radius: 50%;
        text-align: center;
        line-height: 32px;
        font-weight: 700;
        margin-right: 0.75rem;
    }}
    .step-title {{
        display: inline-block;
        font-size: 1.4rem;
        font-weight: 700;
        color: #1f2937;
        vertical-align: middle;
    }}
    .step-help {{
        color: #6b7280;
        font-size: 0.95rem;
        margin: 0.5rem 0 1.25rem 0;
    }}

    /* Sensor card */
    .sensor-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }}
    .sensor-tile {{
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #86efac;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: transform 0.15s;
    }}
    .sensor-tile:hover {{transform: translateY(-2px);}}
    .sensor-icon {{font-size: 1.8rem; margin-bottom: 0.3rem;}}
    .sensor-value {{
        font-size: 1.5rem;
        font-weight: 800;
        color: #15803d;
    }}
    .sensor-label {{
        font-size: 0.78rem;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.2rem;
    }}

    /* Prediction Card (THE KEY OUTPUT) */
    .prediction-hero {{
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 2px solid #f59e0b;
        border-radius: 24px;
        padding: 2.5rem;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 24px rgba(245, 158, 11, 0.25);
    }}
    .crop-emoji {{font-size: 5rem; margin-bottom: 0.5rem;}}
    .crop-name {{
        font-size: 3rem;
        font-weight: 900;
        color: #78350f;
        margin: 0;
        letter-spacing: -0.02em;
    }}
    .crop-label {{
        font-size: 1rem;
        color: #92400e;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}

    .yield-display {{
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1.5rem;
        display: flex;
        justify-content: space-around;
        gap: 1rem;
        flex-wrap: wrap;
    }}
    .yield-stat {{text-align: center;}}
    .yield-value {{
        font-size: 2.2rem;
        font-weight: 800;
        color: #15803d;
        margin: 0;
    }}
    .yield-label {{
        font-size: 0.85rem;
        color: #6b7280;
        margin-top: 0.2rem;
    }}

    /* Buttons */
    .stButton button {{
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.85rem 2rem;
        font-weight: 700;
        font-size: 1.05rem;
        transition: all 0.2s;
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.25);
        width: 100%;
    }}
    .stButton button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(22, 163, 74, 0.35);
        background: linear-gradient(135deg, #15803d 0%, #166534 100%);
    }}

    /* Tips */
    .tip-row {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.85rem 1rem;
        background: #f9fafb;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }}
    .tip-icon {{font-size: 1.5rem;}}
    .tip-content strong {{color: #1f2937;}}
    .tip-content span {{color: #6b7280; font-size: 0.9rem;}}

    /* Mode toggle */
    .mode-badge {{
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    .mode-auto {{background: #dcfce7; color: #15803d;}}
    .mode-manual {{background: #fef3c7; color: #92400e;}}

    /* Map container */
    .map-wrapper {{
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid #e5e7eb;
    }}

    /* Pesticides slider note */
    .input-note {{
        font-size: 0.85rem;
        color: #6b7280;
        margin-top: -0.5rem;
        margin-bottom: 0.75rem;
    }}

    /* Footer */
    .footer {{
        text-align: center;
        color: #9ca3af;
        font-size: 0.85rem;
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e5e7eb;
    }}

    /* XAI Explanation box */
    .xai-box {{
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1.5px solid #86efac;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0 0.5rem 0;
    }}
    .xai-title {{
        font-size: 1rem;
        font-weight: 700;
        color: #15803d;
        margin-bottom: 0.75rem;
    }}
    .xai-reason {{
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        margin-bottom: 0.45rem;
        font-size: 0.92rem;
        color: #1f2937;
    }}
    .xai-icon {{ font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }}
</style>
""", unsafe_allow_html=True)


# =============================================================================
#  LANGUAGE SELECTOR (top-right)
# =============================================================================

lang_col1, lang_col2 = st.columns([6, 1])
with lang_col2:
    selected_lang = st.selectbox(
        "🌐",
        options=['en', 'fr', 'ar'],
        format_func=lambda x: {'en': '🇬🇧 English', 'fr': '🇫🇷 Français', 'ar': '🇸🇦 العربية'}[x],
        index=['en', 'fr', 'ar'].index(LANG),
        label_visibility="collapsed",
        key="lang_selector"
    )
    if selected_lang != st.session_state['lang']:
        st.session_state['lang'] = selected_lang
        st.rerun()

LANG = st.session_state['lang']
DIR  = get_text_direction(LANG)


# =============================================================================
#  HERO
# =============================================================================

st.markdown(f"""
<div class="hero">
    <div class="hero-icon">🌾</div>
    <h1>{t('app_title', LANG)}</h1>
    <p>{t('app_subtitle', LANG)}</p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
#  LOAD MODELS
# =============================================================================

@st.cache_resource
def load_models():
    base = os.path.dirname(os.path.abspath(__file__))
    paths_m1 = [
        os.path.join(base, "models", "model1_crop_recommendation.pkl"),
        os.path.join(base, "model1_crop_recommendation.pkl"),
        os.path.join(base, "systeme_complet_xai.pkl"),
    ]
    paths_m2 = [
        os.path.join(base, "models", "model2_yield_system.pkl"),
        os.path.join(base, "model2_yield_system.pkl"),
    ]
    m1 = next((joblib.load(p) for p in paths_m1 if os.path.exists(p)), None)
    m2 = next((joblib.load(p) for p in paths_m2 if os.path.exists(p)), None)
    return m1, m2

m1_data, m2_data = load_models()


# =============================================================================
#  PREDICTION FUNCTIONS
# =============================================================================

def predict_crop_with_xai(N, P, K, temp, humidity, ph, rainfall):

    scaler = m1_data['scaler']
    encoder = m1_data['encoder']
    model = m1_data['best_model']

    input_data = np.array([[N, P, K, temp, humidity, ph, rainfall]])

    input_scaled = scaler.transform(input_data)

    prediction = model.predict(input_scaled)[0]

    crop = encoder.inverse_transform([prediction])[0]

    probabilities = model.predict_proba(input_scaled)[0]
    confidence = np.max(probabilities) * 100

    # SHAP explanation
    top_features = []

    try:
        if hasattr(model, 'feature_importances_'):
            explainer = shap.TreeExplainer(model)
            shap_out  = explainer.shap_values(input_scaled)

            feature_names = m1_data['feature_names']

            # shap_out can be:
            #   • list of arrays  [n_classes]  each (1, n_features)  — older SHAP / sklearn RF
            #   • 3-D numpy array (1, n_features, n_classes)          — newer SHAP + XGBoost
            #   • 2-D numpy array (1, n_features)                     — binary / regression
            if isinstance(shap_out, list):
                # list[class_idx] → (1, n_features) → take row 0
                class_index = int(prediction)
                values = np.array(shap_out[class_index][0])
            else:
                shap_arr = np.array(shap_out)
                if shap_arr.ndim == 3:
                    # shape (1, n_features, n_classes) → slice sample 0, then class
                    class_index = int(prediction)
                    values = shap_arr[0, :, class_index]
                else:
                    # shape (1, n_features) → take row 0
                    values = shap_arr[0]

            importance_pairs = sorted(
                zip(feature_names, values.tolist()),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            top_features = importance_pairs[:3]

    except Exception as e:
        print("SHAP error:", e)

    return {
        'crop': crop,
        'confidence': confidence,
        'top_features': top_features
    }


def generate_crop_explanation_shap(top_features, lang='en'):
    """
    Build the XAI explanation block directly from SHAP values returned by
    predict_crop_with_xai().  top_features is a list of (feature_name, shap_value)
    pairs, already sorted by |shap_value| descending (top-3).
    """
    # Per-feature display metadata
    FEAT_META = {
        'N':           {'en': 'Nitrogen (N)',    'fr': 'Azote (N)',        'ar': 'النيتروجين (N)',   'icon': '🟦'},
        'P':           {'en': 'Phosphorus (P)',  'fr': 'Phosphore (P)',    'ar': 'الفوسفور (P)',     'icon': '🟧'},
        'K':           {'en': 'Potassium (K)',   'fr': 'Potassium (K)',    'ar': 'البوتاسيوم (K)',   'icon': '🟪'},
        'temperature': {'en': 'Temperature',     'fr': 'Température',      'ar': 'درجة الحرارة',     'icon': '🌡️'},
        'humidity':    {'en': 'Humidity',        'fr': 'Humidité',         'ar': 'الرطوبة',          'icon': '💧'},
        'ph':          {'en': 'Soil pH',         'fr': 'pH du sol',        'ar': 'حموضة التربة',     'icon': '⚗️'},
        'rainfall':    {'en': 'Rainfall',        'fr': 'Précipitations',   'ar': 'الأمطار',          'icon': '🌧️'},
    }
    POS_PHRASE = {
        'en': 'pushed the model strongly toward this crop',
        'fr': 'a fortement orienté le modèle vers cette culture',
        'ar': 'دفع النموذج بقوة نحو هذا المحصول',
    }
    NEG_PHRASE = {
        'en': 'was a key differentiating factor for this crop',
        'fr': 'a été un facteur différenciateur clé pour cette culture',
        'ar': 'كان عاملاً تمييزياً رئيسياً لهذا المحصول',
    }
    WHY_TITLE = {
        'en': '🔍 Why this crop? (SHAP explanation)',
        'fr': '🔍 Pourquoi cette culture ? (explication SHAP)',
        'ar': '🔍 لماذا هذا المحصول؟ (تفسير SHAP)',
    }

    reasons = []
    for feat_name, shap_val in top_features:
        meta   = FEAT_META.get(feat_name, {'en': feat_name, 'fr': feat_name, 'ar': feat_name, 'icon': '📊'})
        icon   = meta['icon']
        label  = meta.get(lang, meta.get('en', feat_name))
        phrase = POS_PHRASE.get(lang, POS_PHRASE['en']) if shap_val >= 0 else NEG_PHRASE.get(lang, NEG_PHRASE['en'])
        direction = '▲' if shap_val >= 0 else '▼'
        reasons.append((icon, f"{label} {direction} (SHAP={shap_val:+.3f}) — {phrase}"))

    return WHY_TITLE.get(lang, WHY_TITLE['en']), reasons


def predict_yield(crop_name, country, rainfall, pesticides, temp, year):
    """Use Model 2 to predict yield for a single year."""
    if m2_data is None:
        return None

    try:
        crop_mapping = m2_data['crop_mapping']
        direct_crops = m2_data['direct_crops']
        mapped       = crop_mapping.get(crop_name.lower().strip(), "Maize")
        is_direct    = crop_name.lower() in direct_crops

        le_crop      = m2_data['le_crop']
        le_country   = m2_data['le_country']
        scaler       = m2_data['scaler']
        model        = m2_data['best_model']

        crop_enc    = le_crop.transform([mapped])[0] if mapped in le_crop.classes_ else 0
        country_enc = le_country.transform([country])[0] if country in le_country.classes_ else 0

        inp     = np.array([[crop_enc, country_enc, year, rainfall, pesticides, temp]])
        inp_sc  = scaler.transform(inp)
        yield_kg = max(0, float(model.predict(inp_sc)[0]))
        mae      = m2_data['metrics']['test']['mae']
        return {
            'yield_kg_ha':     round(yield_kg, 2),
            'yield_tonnes_ha': round(yield_kg / 1000, 3),
            'ci_low':          max(0, yield_kg - mae),
            'ci_high':         yield_kg + mae,
            'mapped_crop':     mapped,
            'is_direct':       is_direct,
            'year':            year,
        }
    except Exception as e:
        st.error(f"Model 2 error: {e}")
        return None


def predict_yield_5_years(crop_name, country, rainfall, pesticides, temp, base_year):
    """Forecast yield for base_year and the next 5 years."""
    forecasts = []
    for offset in range(6):    # year 0, 1, 2, 3, 4, 5 → 6 points total
        y         = base_year + offset
        # Slight climate trend adjustment per year (subtle realistic variation)
        rain_y    = rainfall + np.random.normal(0, rainfall * 0.02)
        temp_y    = temp + offset * 0.05      # +0.05°C/year warming trend
        result    = predict_yield(crop_name, country, rain_y, pesticides, temp_y, y)
        if result:
            result['year'] = y
            forecasts.append(result)
    return forecasts


# =============================================================================
#  MAIN UI — STEP-BY-STEP FLOW
# =============================================================================

# ──────────────────────────────────────────────
# STEP 1: COUNTRY + MAP
# ──────────────────────────────────────────────
st.markdown(f"""
<div class="step-card">
    <span class="step-number">1</span>
    <span class="step-title">{t('step1_title', LANG)}</span>
    <p class="step-help">{t('step1_help', LANG)}</p>
</div>
""", unsafe_allow_html=True)

col_country, col_status = st.columns([2, 3])

with col_country:
    country = st.selectbox(
        t('country', LANG),
        options=sorted(COUNTRY_CENTERS.keys()),
        index=sorted(COUNTRY_CENTERS.keys()).index(st.session_state['country'])
              if st.session_state['country'] in COUNTRY_CENTERS else 0,
        key="country_select"
    )
    if country != st.session_state['country']:
        st.session_state['country']      = country
        st.session_state['clicked_lat']  = None
        st.session_state['clicked_lon']  = None
        st.session_state['soil_data']    = None
        st.session_state['weather_data'] = None
        st.session_state['soil_loaded']  = False
        st.rerun()

# ── Map ──
country_center = COUNTRY_CENTERS.get(country, (28.0, 1.6))
default_zoom   = 5

# Use clicked location if available, else country center
map_center = (
    [st.session_state['clicked_lat'], st.session_state['clicked_lon']]
    if st.session_state['clicked_lat'] is not None
    else list(country_center)
)

m = folium.Map(location=map_center, zoom_start=default_zoom, tiles='OpenStreetMap')

# Add marker for clicked location
if st.session_state['clicked_lat'] is not None:
    folium.Marker(
        [st.session_state['clicked_lat'], st.session_state['clicked_lon']],
        popup=f"📍 {t('map_selected', LANG)}",
        icon=folium.Icon(color='green', icon='leaf', prefix='fa')
    ).add_to(m)

st.markdown('<div class="map-wrapper">', unsafe_allow_html=True)
map_data = st_folium(
    m,
    width=None,
    height=400,
    returned_objects=["last_clicked"],
    key=f"map_{country}"
)
st.markdown('</div>', unsafe_allow_html=True)

# Process click
if map_data and map_data.get("last_clicked"):
    new_lat = map_data["last_clicked"]["lat"]
    new_lon = map_data["last_clicked"]["lng"]
    if (st.session_state['clicked_lat'] != new_lat or
        st.session_state['clicked_lon'] != new_lon):
        st.session_state['clicked_lat'] = new_lat
        st.session_state['clicked_lon'] = new_lon
        st.session_state['soil_data']   = None    # Trigger refresh
        st.session_state['weather_data'] = None
        st.session_state['soil_loaded'] = False
        st.rerun()


# ──────────────────────────────────────────────
# Once a location is clicked → fetch sensor data
# ──────────────────────────────────────────────

has_location = (st.session_state['clicked_lat'] is not None
                and st.session_state['clicked_lon'] is not None)

if not has_location:
    st.info(f"👆 {t('click_map_first', LANG)}")
    st.markdown(f"""
    <div class="footer">
        {t('powered_by', LANG)}
    </div>
    """, unsafe_allow_html=True)
    st.stop()

lat = st.session_state.get("clicked_lat")
lon = st.session_state.get("clicked_lon")

if lat is None or lon is None:
    st.warning("Click the map again to select location.")
    st.stop()
# Show selected coordinates
st.success(
    f"📍 **{t('map_selected', LANG)}** — "
    f"{t('lat', LANG)}: `{float(lat):.4f}` · "
    f"{t('lon', LANG)}: `{float(lon):.4f}`"
)
# Fetch sensor data once
if st.session_state['soil_data'] is None:
    with st.spinner("🌍 Fetching real-time soil & weather data..."):
        st.session_state['soil_data']    = fetch_soil_data(lat, lon)
        weather_raw                       = fetch_current_weather(lat, lon)
        # Apply small IoT drift to mimic live sensors
        st.session_state['weather_data']  = get_iot_simulated_weather(weather_raw, with_drift=True)
        st.session_state['soil_loaded']   = True


# ──────────────────────────────────────────────
# STEP 2: SOIL & CLIMATE DATA
# ──────────────────────────────────────────────

st.markdown(f"""
<div class="step-card">
    <span class="step-number">2</span>
    <span class="step-title">{t('step2_title', LANG)}</span>
    <p class="step-help">{t('step2_help', LANG)}</p>
</div>
""", unsafe_allow_html=True)

# Mode toggle (auto vs manual)
mode_col, refresh_col = st.columns([3, 1])
with mode_col:
    mode = st.radio(
        t('data_mode', LANG),
        options=['auto', 'manual'],
        format_func=lambda x: t(f'data_{x}', LANG),
        horizontal=True,
        key="data_mode"
    )
with refresh_col:
    if st.button("🔄 " + t('fetch_data', LANG), use_container_width=True):
        st.session_state['soil_data']    = None
        st.session_state['weather_data'] = None
        st.rerun()

# Get current sensor values
soil    = st.session_state['soil_data']    or {}
weather = st.session_state['weather_data'] or {}

# Mode badge
mode_class = "mode-auto" if mode == 'auto' else "mode-manual"
mode_label = t('live_iot' if mode == 'auto' else 'manual_test', LANG)
st.markdown(f"""
<span class="mode-badge {mode_class}">📡 {mode_label}</span>
""", unsafe_allow_html=True)

# ── Soil section ──
st.markdown(f"#### 🌱 {t('soil_section', LANG)}")
sc1, sc2, sc3, sc4 = st.columns(4)

if mode == 'auto':
    # Read-only display of API values
    with sc1:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">🟦</div>
            <div class="sensor-value">{soil.get('N', 0):.0f}</div>
            <div class="sensor-label">{t('nitrogen', LANG)}</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">🟧</div>
            <div class="sensor-value">{soil.get('P', 0):.0f}</div>
            <div class="sensor-label">{t('phosphorus', LANG)}</div>
        </div>""", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">🟪</div>
            <div class="sensor-value">{soil.get('K', 0):.0f}</div>
            <div class="sensor-label">{t('potassium', LANG)}</div>
        </div>""", unsafe_allow_html=True)
    with sc4:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">⚗️</div>
            <div class="sensor-value">{soil.get('ph', 0):.1f}</div>
            <div class="sensor-label">{t('soil_ph', LANG)}</div>
        </div>""", unsafe_allow_html=True)

    N_val  = soil.get('N',  60)
    P_val  = soil.get('P',  60)
    K_val  = soil.get('K',  60)
    ph_val = soil.get('ph', 6.5)
else:
    # Manual sliders
    with sc1:
        N_val = st.slider(t('nitrogen', LANG), 0, 200, int(soil.get('N', 60)))
    with sc2:
        P_val = st.slider(t('phosphorus', LANG), 0, 200, int(soil.get('P', 60)))
    with sc3:
        K_val = st.slider(t('potassium', LANG), 0, 250, int(soil.get('K', 60)))
    with sc4:
        ph_val = st.slider(t('soil_ph', LANG), 3.0, 9.0, float(soil.get('ph', 6.5)), step=0.1)

# ── Weather section ──
st.markdown(f"#### 🌤️ {t('weather_section', LANG)}")
wc1, wc2, wc3, wc4 = st.columns(4)

if mode == 'auto':
    with wc1:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">🌡️</div>
            <div class="sensor-value">{weather.get('temperature', 0):.1f}°C</div>
            <div class="sensor-label">{t('temperature', LANG)}</div>
        </div>""", unsafe_allow_html=True)
    with wc2:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">💧</div>
            <div class="sensor-value">{weather.get('humidity', 0):.0f}%</div>
            <div class="sensor-label">{t('humidity', LANG)}</div>
        </div>""", unsafe_allow_html=True)
    with wc3:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">🌧️</div>
            <div class="sensor-value">{weather.get('rainfall_mm', 0):.0f}<small>mm</small></div>
            <div class="sensor-label">{t('rainfall', LANG)}</div>
        </div>""", unsafe_allow_html=True)
    with wc4:
        st.markdown(f"""
        <div class="sensor-tile">
            <div class="sensor-icon">💨</div>
            <div class="sensor-value">{weather.get('wind_speed', 0):.1f}<small>km/h</small></div>
            <div class="sensor-label">{t('wind', LANG)}</div>
        </div>""", unsafe_allow_html=True)

    temp_val     = weather.get('temperature', 22.0)
    humidity_val = weather.get('humidity',    65.0)
    rainfall_val = weather.get('rainfall_mm', 800.0)
    wind_val     = weather.get('wind_speed',  8.0)
else:
    with wc1:
        temp_val = st.slider(t('temperature', LANG) + " (°C)",
                             0.0, 45.0, float(weather.get('temperature', 22.0)), step=0.5)
    with wc2:
        humidity_val = st.slider(t('humidity', LANG) + " (%)",
                                 0, 100, int(weather.get('humidity', 65)))
    with wc3:
        rainfall_val = st.slider(t('rainfall', LANG) + " (mm)",
                                 0, 4000, int(weather.get('rainfall_mm', 800)))
    with wc4:
        wind_val = st.slider(t('wind', LANG) + " (km/h)",
                             0.0, 50.0, float(weather.get('wind_speed', 8.0)), step=0.5)


# ──────────────────────────────────────────────
# STEP 3: PESTICIDES (always manual)
# ──────────────────────────────────────────────

st.markdown(f"""
<div class="step-card">
    <span class="step-number">3</span>
    <span class="step-title">{t('step3_title', LANG)}</span>
    <p class="step-help">{t('pesticides_help', LANG)}</p>
</div>
""", unsafe_allow_html=True)

pesticides_val = st.slider(
    t('pesticides', LANG),
    min_value=0.0, max_value=1000.0,
    value=80.0, step=5.0,
    label_visibility="collapsed"
)


# ──────────────────────────────────────────────
# STEP 4: YEAR
# ──────────────────────────────────────────────

st.markdown(f"""
<div class="step-card">
    <span class="step-number">4</span>
    <span class="step-title">{t('step4_title', LANG)}</span>
</div>
""", unsafe_allow_html=True)

current_year = datetime.now().year
selected_year = st.slider(
    t('year_select', LANG),
    min_value=current_year,
    max_value=current_year + 5,
    value=current_year
)


# ──────────────────────────────────────────────
# STEP 5: PREDICT
# ──────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
predict_clicked = st.button(
    f"🌾 {t('predict_btn', LANG)}",
    use_container_width=True,
    type="primary"
)

if predict_clicked:
    with st.spinner(t('predicting', LANG)):
        time.sleep(0.8)

        # ── Run Model 1 ──
        result = predict_crop_with_xai(
            N_val, P_val, K_val, temp_val, humidity_val, ph_val, rainfall_val
        )

        recommended_crop = result['crop']
        m1_conf = result['confidence']
        top_features = result['top_features']

        # ── Run Model 2 for selected year + 5-year forecast ──
        selected_year_pred = predict_yield(
            recommended_crop, country, rainfall_val,
            pesticides_val, temp_val, selected_year
        )

        forecast_5y = predict_yield_5_years(
            recommended_crop, country, rainfall_val,
            pesticides_val, temp_val, current_year
        )

        xai_title, xai_reasons = generate_crop_explanation_shap(
            top_features, LANG
        )

        st.session_state['prediction'] = {
            'crop':            recommended_crop,
            'conf':            m1_conf,
            'selected_year':   selected_year,
            'selected_pred':   selected_year_pred,
            'forecast_5y':     forecast_5y,
            'xai_title':       xai_title,
            'xai_reasons':     xai_reasons,
        }


# =============================================================================
#  RESULTS DISPLAY
# =============================================================================

if st.session_state.get('prediction'):
    pred         = st.session_state['prediction']
    crop         = pred['crop']
    crop_label   = translate_crop(crop, LANG)
    selected     = pred['selected_pred']
    forecast     = pred['forecast_5y']

    # Crop emoji map (simple mapping for visual delight)
    CROP_EMOJI = {
        'rice': '🌾', 'maize': '🌽', 'wheat': '🌾', 'potato': '🥔',
        'banana': '🍌', 'mango': '🥭', 'apple': '🍎', 'orange': '🍊',
        'grapes': '🍇', 'watermelon': '🍉', 'muskmelon': '🍈',
        'papaya': '🍈', 'coconut': '🥥', 'cotton': '🌱', 'jute': '🌿',
        'coffee': '☕', 'sugarcane': '🎋', 'tomato': '🍅',
        'pomegranate': '🌳', 'chickpea': '🫘', 'kidneybeans': '🫘',
        'pigeonpeas': '🫘', 'mothbeans': '🫘', 'mungbean': '🫘',
        'blackgram': '🫘', 'lentil': '🫘',
    }
    emoji = CROP_EMOJI.get(crop.lower(), '🌱')

    # ── Prediction Hero (crop name only) ──
    st.markdown(f"""<div class="prediction-hero">
<div class="crop-label">{t('recommended_crop', LANG)}</div>
<div class="crop-emoji">{emoji}</div>
<div class="crop-name">{crop_label}</div>
</div>""", unsafe_allow_html=True)

    # ── Yield stats below the hero using native Streamlit metrics ──
    if selected:
        yc1, yc2, yc3 = st.columns(3)
        with yc1:
            st.metric(t('tons_per_hectare', LANG), f"{selected['yield_tonnes_ha']:.2f}")
        with yc2:
            st.metric(t('kg_per_hectare', LANG), f"{selected['yield_kg_ha']:,.0f}")
        with yc3:
            st.metric(t('this_year', LANG), str(pred['selected_year']))
        if not selected['is_direct']:
            st.caption(f"ℹ️ {t('crop_mapping_note', LANG)}")

    # ── XAI Explanation ──
    xai_title   = pred.get('xai_title', '')
    xai_reasons = pred.get('xai_reasons', [])
    if xai_reasons:
        reasons_html = ''.join(
            f'<div class="xai-reason"><span class="xai-icon">{icon}</span><span>{text}</span></div>'
            for icon, text in xai_reasons
        )
        st.markdown(f"""
        <div class="xai-box">
            <div class="xai-title">{xai_title}</div>
            {reasons_html}
        </div>
        """, unsafe_allow_html=True)

    # ── 5-Year Forecast Chart ──
    if forecast:
        st.markdown(f"### 📈 {t('next_5_years', LANG)}")
        st.caption(t('forecast_help', LANG))

        years      = [f['year'] for f in forecast]
        yields_t   = [f['yield_tonnes_ha'] for f in forecast]
        yields_kg  = [f['yield_kg_ha'] for f in forecast]

        # Modern matplotlib chart
        fig, ax = plt.subplots(figsize=(10, 4.5))
        fig.patch.set_facecolor('#ffffff')

        # Filled area + line
        ax.fill_between(years, yields_t, alpha=0.25, color='#16a34a')
        ax.plot(years, yields_t, color='#15803d', linewidth=3, marker='o',
                markersize=10, markerfacecolor='white', markeredgewidth=2.5,
                markeredgecolor='#15803d')

        # Annotate each point
        for x, y in zip(years, yields_t):
            ax.text(x, y + max(yields_t) * 0.05, f'{y:.2f}',
                    ha='center', fontsize=10, fontweight='bold', color='#15803d')

        ax.set_xlabel(t('year_select', LANG), fontsize=11, color='#374151')
        ax.set_ylabel(t('tons_per_hectare', LANG), fontsize=11, color='#374151')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#d1d5db')
        ax.spines['bottom'].set_color('#d1d5db')
        ax.tick_params(colors='#6b7280')
        ax.grid(True, axis='y', linestyle='--', alpha=0.3)
        ax.set_ylim(bottom=0, top=max(yields_t) * 1.25)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Summary stats
        best_idx  = int(np.argmax(yields_t))
        avg_yield = sum(yields_t) / len(yields_t)
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"""
            <div class="sensor-tile">
                <div class="sensor-icon">🏆</div>
                <div class="sensor-value">{years[best_idx]}</div>
                <div class="sensor-label">{t('best_year', LANG)}</div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div class="sensor-tile">
                <div class="sensor-icon">📊</div>
                <div class="sensor-value">{avg_yield:.2f}<small> t/ha</small></div>
                <div class="sensor-label">{t('avg_yield', LANG)}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Farming Tips ──
    st.markdown(f"### 💡 {t('tips_title', LANG)}")

    # Generate tips based on conditions
    tips = []
    if rainfall_val > 1500:
        tips.append(('🌧️', t('tip_water', LANG), t('high', LANG)))
    elif rainfall_val < 600:
        tips.append(('🌧️', t('tip_water', LANG), t('low', LANG)))
    else:
        tips.append(('🌧️', t('tip_water', LANG), t('optimal', LANG)))

    if 6.0 <= ph_val <= 7.5:
        tips.append(('⚗️', t('tip_soil', LANG), t('optimal', LANG)))
    else:
        tips.append(('⚗️', t('tip_soil', LANG), t('medium', LANG)))

    # Best planting month (rough heuristic from temp)
    if temp_val > 25:
        season = 'Spring / Summer' if LANG == 'en' else 'Printemps / Été' if LANG == 'fr' else 'الربيع / الصيف'
    elif temp_val > 15:
        season = 'Spring / Autumn' if LANG == 'en' else 'Printemps / Automne' if LANG == 'fr' else 'الربيع / الخريف'
    else:
        season = 'Autumn / Winter' if LANG == 'en' else 'Automne / Hiver' if LANG == 'fr' else 'الخريف / الشتاء'
    tips.append(('📅', t('tip_planting', LANG), season))

    for icon, label, value in tips:
        st.markdown(f"""
        <div class="tip-row">
            <span class="tip-icon">{icon}</span>
            <div class="tip-content">
                <strong>{label}:</strong> <span>{value}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
#  FOOTER
# =============================================================================

