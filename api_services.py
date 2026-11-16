# =============================================================================
#  API SERVICES — Real soil & climate data fetchers
#  - SoilGrids API: Soil properties (N, P, K estimates, pH)
#  - Open-Meteo API: Weather (rainfall, temperature, humidity, wind)
#  Both APIs are FREE and require NO API KEY.
# =============================================================================

import requests
import streamlit as st
import numpy as np
import random
from datetime import datetime, timedelta

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL   = "https://archive-api.open-meteo.com/v1/archive"

SOIL_FALLBACK_RANGES = {
    'N':  (20, 140), 'P':  (10, 145), 'K':  (15, 205), 'ph': (5.5, 8.0),
}


# =============================================================================
#  SOIL DATA
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_soil_data(lat: float, lon: float) -> dict:
    """
    Fetches soil properties from SoilGrids API.
    Derives N, P, K estimates from raw soil chemistry properties.
    """
    try:
        params = {
            'lon': lon, 'lat': lat,
            'property': ['phh2o', 'nitrogen', 'soc', 'cec'],
            'depth': '0-5cm', 'value': 'mean'
        }
        response = requests.get(SOILGRIDS_URL, params=params, timeout=8)

        if response.status_code != 200:
            return _soil_fallback("API timeout / non-200")

        data       = response.json()
        properties = data.get('properties', {}).get('layers', [])

        soil_values = {}
        for layer in properties:
            name   = layer.get('name')
            depths = layer.get('depths', [])
            if depths and depths[0].get('values', {}).get('mean') is not None:
                soil_values[name] = depths[0]['values']['mean']

        if not soil_values:
            return _soil_fallback("Empty API response")

        # Derive Model 1 features from raw soil chemistry
        ph_val = soil_values.get('phh2o', 65) / 10
        ph_val = round(np.clip(ph_val, 3.5, 9.0), 2)

        n_raw  = soil_values.get('nitrogen', 1500)  # cg/kg
        n_val  = round(np.clip(n_raw / 10, 5, 200), 1)

        cec    = soil_values.get('cec', 200) / 10
        soc    = soil_values.get('soc', 200) / 10
        p_val  = round(np.clip(cec * 1.5 + 10, 5, 200), 1)
        k_val  = round(np.clip(soc * 4.0 + 20, 5, 250), 1)

        return {
            'N': n_val, 'P': p_val, 'K': k_val, 'ph': ph_val,
            'source':  'SoilGrids API',
            'success': True,
        }
    except Exception as e:
        return _soil_fallback(f"Exception: {e}")


def _soil_fallback(reason: str) -> dict:
    return {
        'N':  round(random.uniform(*SOIL_FALLBACK_RANGES['N']), 1),
        'P':  round(random.uniform(*SOIL_FALLBACK_RANGES['P']), 1),
        'K':  round(random.uniform(*SOIL_FALLBACK_RANGES['K']), 1),
        'ph': round(random.uniform(*SOIL_FALLBACK_RANGES['ph']), 2),
        'source':  f'Fallback ({reason})',
        'success': False,
    }


# =============================================================================
#  WEATHER DATA
# =============================================================================

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_current_weather(lat: float, lon: float) -> dict:
    """Fetch current weather from Open-Meteo + 30-day rainfall to extrapolate annual."""
    try:
        params = {
            'latitude': lat, 'longitude': lon,
            'current':   'temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation',
            'daily':     'precipitation_sum,temperature_2m_max,temperature_2m_min',
            'past_days': 30,
            'timezone':  'auto'
        }
        response = requests.get(OPENMETEO_URL, params=params, timeout=8)
        if response.status_code != 200:
            return _weather_fallback("API non-200")

        data    = response.json()
        current = data.get('current', {})
        daily   = data.get('daily', {})

        precip_30d = [p for p in daily.get('precipitation_sum', []) if p is not None]
        annual_rainfall_est = sum(precip_30d) * 12 if precip_30d else 800

        return {
            'temperature': round(current.get('temperature_2m', 20), 2),
            'humidity':    round(current.get('relative_humidity_2m', 60), 1),
            'wind_speed':  round(current.get('wind_speed_10m', 5), 1),
            'rainfall_mm': round(np.clip(annual_rainfall_est, 50, 4000), 1),
            'source':      'Open-Meteo API',
            'success':     True,
        }
    except Exception as e:
        return _weather_fallback(f"Exception: {e}")


def _weather_fallback(reason: str) -> dict:
    return {
        'temperature': round(random.uniform(15, 28), 2),
        'humidity':    round(random.uniform(40, 85), 1),
        'wind_speed':  round(random.uniform(3, 15), 1),
        'rainfall_mm': round(random.uniform(400, 1800), 1),
        'source':      f'Fallback ({reason})',
        'success':     False,
    }


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_historical_climate_avg(lat: float, lon: float, years: int = 5) -> dict:
    """Fetch historical climate averages (used as Model 2 baseline for past-year predictions)."""
    try:
        end   = datetime.now() - timedelta(days=2)
        start = end - timedelta(days=365 * years)
        params = {
            'latitude':   lat,  'longitude':  lon,
            'start_date': start.strftime("%Y-%m-%d"),
            'end_date':   end.strftime("%Y-%m-%d"),
            'daily':      'precipitation_sum,temperature_2m_mean',
            'timezone':   'auto'
        }
        response = requests.get(ARCHIVE_URL, params=params, timeout=15)
        if response.status_code != 200:
            return None

        daily  = response.json().get('daily', {})
        precip = [p for p in daily.get('precipitation_sum', []) if p is not None]
        temps  = [t for t in daily.get('temperature_2m_mean', []) if t is not None]
        if not precip or not temps:
            return None

        return {
            'avg_annual_rainfall_mm': round((sum(precip) / len(precip)) * 365, 1),
            'avg_temperature_c':      round(sum(temps) / len(temps), 2),
            'years_covered':          years,
        }
    except Exception:
        return None


# =============================================================================
#  IoT SENSOR DRIFT SIMULATION
# =============================================================================

def apply_iot_drift(value: float, drift_pct: float = 0.05) -> float:
    """Adds ±drift_pct random variation to mimic live sensor readings."""
    delta = value * drift_pct * (random.random() * 2 - 1)
    return round(value + delta, 2)


def get_iot_simulated_weather(api_data: dict, with_drift: bool = True) -> dict:
    """Apply IoT drift to API weather. with_drift=False returns clean API values."""
    if not with_drift:
        return api_data
    return {
        'temperature': apply_iot_drift(api_data['temperature'], 0.03),
        'humidity':    apply_iot_drift(api_data['humidity'],    0.05),
        'wind_speed':  apply_iot_drift(api_data['wind_speed'],  0.10),
        'rainfall_mm': apply_iot_drift(api_data['rainfall_mm'], 0.02),
        'source':      api_data.get('source', '') + ' + IoT drift',
        'success':     api_data.get('success', False),
    }


# =============================================================================
#  COUNTRY CENTERS — for map initialization
# =============================================================================

COUNTRY_CENTERS = {
    'Algeria':   (28.0339,   1.6596),
    'France':    (46.6034,   1.8883),
    'India':     (20.5937,  78.9629),
    'Brazil':    (-14.2350, -51.9253),
    'Nigeria':   ( 9.0820,   8.6753),
    'Kenya':     (-0.0236,  37.9062),
    'China':     (35.8617, 104.1954),
    'USA':       (37.0902, -95.7129),
    'Argentina': (-38.4161, -63.6167),
    'Australia': (-25.2744, 133.7751),
    'Germany':   (51.1657,  10.4515),
    'Spain':     (40.4637,  -3.7492),
    'Egypt':     (26.8206,  30.8025),
    'Ethiopia':  ( 9.1450,  40.4897),
    'Mexico':    (23.6345, -102.5528),
    'Pakistan':  (30.3753,  69.3451),
    'Indonesia': (-0.7893, 113.9213),
    'Morocco':   (31.7917,  -7.0926),
    'Tunisia':   (33.8869,   9.5375),
    'Turkey':    (38.9637,  35.2433),
    'Italy':     (41.8719,  12.5674),
    'Canada':    (56.1304, -106.3468),
}
