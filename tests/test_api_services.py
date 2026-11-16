import itertools

import pytest

import api_services
from api_services import SOIL_FALLBACK_RANGES, apply_iot_drift, get_iot_simulated_weather

_coords = itertools.count(1)


def _fresh_coords():
    # fetch_soil_data is cached by Streamlit: use unique coordinates per call.
    n = next(_coords)
    return 10.0 + n / 1000, 3.0 + n / 1000


class _Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


def _layer(name, mean):
    return {"name": name, "depths": [{"values": {"mean": mean}}]}


def test_soil_data_is_derived_from_soilgrids(monkeypatch):
    payload = {"properties": {"layers": [
        _layer("phh2o", 68), _layer("nitrogen", 1200), _layer("cec", 150), _layer("soc", 100),
    ]}}
    monkeypatch.setattr(api_services.requests, "get", lambda *a, **k: _Resp(200, payload))

    soil = api_services.fetch_soil_data(*_fresh_coords())

    assert soil["success"] is True
    assert soil["ph"] == pytest.approx(6.8)
    assert soil["N"] == pytest.approx(120.0)
    assert soil["P"] == pytest.approx(15 * 1.5 + 10)
    assert soil["K"] == pytest.approx(10 * 4.0 + 20)


@pytest.mark.parametrize("response", [
    _Resp(500, {}),
    _Resp(200, {"properties": {"layers": []}}),
])
def test_soil_data_falls_back_within_ranges(monkeypatch, response):
    monkeypatch.setattr(api_services.requests, "get", lambda *a, **k: response)

    soil = api_services.fetch_soil_data(*_fresh_coords())

    assert soil["success"] is False
    assert soil["source"].startswith("Fallback")
    for key in ("N", "P", "K", "ph"):
        low, high = SOIL_FALLBACK_RANGES[key]
        assert low <= soil[key] <= high


def test_soil_data_falls_back_on_network_error(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("offline")

    monkeypatch.setattr(api_services.requests, "get", boom)
    assert api_services.fetch_soil_data(*_fresh_coords())["success"] is False


def test_iot_drift_stays_within_bounds():
    for _ in range(500):
        assert 95.0 <= apply_iot_drift(100.0, 0.05) <= 105.0


def test_simulated_weather_without_drift_is_unchanged():
    data = {"temperature": 20.0, "humidity": 50.0, "wind_speed": 3.0, "rainfall_mm": 400.0}
    assert get_iot_simulated_weather(data, with_drift=False) == data


def test_simulated_weather_with_drift_marks_source():
    data = {"temperature": 20.0, "humidity": 50.0, "wind_speed": 3.0,
            "rainfall_mm": 400.0, "source": "Open-Meteo", "success": True}
    out = get_iot_simulated_weather(data)
    assert out["source"] == "Open-Meteo + IoT drift"
    assert 19.4 <= out["temperature"] <= 20.6
