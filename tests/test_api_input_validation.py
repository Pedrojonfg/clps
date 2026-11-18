"""Structural input validation for the planner API: bad input is a 4xx with a message, never a generic 503.

Validation must run before any kernel/DEM/cap-index access, so these tests need no data on disk.
503 is reserved for missing data ({"error", "message"}); a client mistake must never surface as 5xx.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from moonpark.api.app import app

# raise_server_exceptions=False: an unhandled crash must show up as a 500 assertion failure, not a raised exception
client = TestClient(app, raise_server_exceptions=False)

WINDOW = {"start": "2027-01-01T00:00:00Z", "end": "2027-01-01T03:00:00Z"}
ENERGY = {"battery_wh": "100", "array_w": "10", "dark_w": "1"}


def _text(r) -> str:
    try:
        return str(r.json()).lower()
    except ValueError:
        return r.text.lower()


def _assert_client_error(r, status: int | None = None) -> None:
    assert 400 <= r.status_code < 500, f"expected 4xx, got {r.status_code}: {r.text[:200]}"
    if status is not None:
        assert r.status_code == status, f"expected {status}, got {r.status_code}: {r.text[:200]}"
    assert _text(r).strip(), "error response must carry a message"


def _site(**params):
    return client.get("/site", params={**WINDOW, **params})


@pytest.mark.parametrize("lat", ["90.0001", "91", "-91", "nan", "inf", "-inf"])
def test_site_rejects_bad_lat(lat: str) -> None:
    _assert_client_error(_site(lat=lat, lon="0"), 422)


@pytest.mark.parametrize("lon", ["nan", "inf", "-inf"])
def test_site_rejects_non_finite_lon(lon: str) -> None:
    _assert_client_error(_site(lat="-89.4", lon=lon), 422)


@pytest.mark.parametrize(
    "start,end",
    [
        ("2027-01-02T00:00:00Z", "2027-01-01T00:00:00Z"),
        ("2027-01-01T00:00:00Z", "2027-01-01T00:00:00Z"),  # end must be strictly after start
        ("2027-01-01T00:00:00", "2026-12-31T00:00:00Z"),  # naive start vs UTC end
        ("2027-01-02T00:00:00Z", "2027-01-01T00:00:00"),  # UTC start vs naive end
    ],
)
def test_site_rejects_end_not_after_start(start: str, end: str) -> None:
    r = client.get("/site", params={"start": start, "end": end})
    _assert_client_error(r, 422)
    msg = _text(r)
    assert "end" in msg and "start" in msg, f"message should mention the start/end order: {msg}"


def test_site_unparseable_time_is_client_error() -> None:
    _assert_client_error(client.get("/site", params={"start": "garbage", "end": "2027-01-02T00:00:00Z"}), 422)


def test_site_rejects_inverted_temperature_limits() -> None:
    r = _site(max_temperature_k="100", min_temperature_k="200")
    _assert_client_error(r, 422)
    assert "temperature" in _text(r)


@pytest.mark.parametrize("key", ["max_temperature_k", "min_temperature_k", "min_soil_resistance"])
@pytest.mark.parametrize("val", ["nan", "inf", "-inf"])
def test_site_rejects_non_finite_hazard_limits(key: str, val: str) -> None:
    _assert_client_error(_site(**{key: val}), 422)


def test_site_rejects_negative_soil_resistance() -> None:
    _assert_client_error(_site(min_soil_resistance="-1"), 422)


@pytest.mark.parametrize("key", ["battery_wh", "array_w", "dark_w", "lit_w", "endurance_h"])
@pytest.mark.parametrize("val", ["-1", "nan", "inf", "-inf"])
def test_site_rejects_bad_energy_values(key: str, val: str) -> None:
    params = {**ENERGY, key: val}
    if key == "endurance_h":
        params.pop("dark_w")
    _assert_client_error(_site(**params), 422)


@pytest.mark.parametrize("key", ["max_night_h", "max_no_earth_h"])
def test_site_rejects_negative_hour_limits(key: str) -> None:
    _assert_client_error(_site(**{key: "-1"}), 422)


def test_site_rejects_non_finite_min_total_lit_h() -> None:
    _assert_client_error(_site(min_total_lit_h="inf"), 422)


def test_site_rejects_unknown_template() -> None:
    r = _site(template_id="no-such-template")
    _assert_client_error(r)
    assert "template" in _text(r)


@pytest.mark.parametrize("step", ["7", "45", "90", "120"])  # engine windows assume the step divides an hour
def test_site_rejects_unsupported_step_min(step: str) -> None:
    r = _site(step_min=step)
    _assert_client_error(r, 422)
    assert "step" in _text(r)


@pytest.mark.parametrize("lat,lon", [("95", "0"), ("-95", "0"), ("nan", "0"), ("0", "inf")])
def test_terrain_rejects_bad_coordinates(lat: str, lon: str) -> None:
    _assert_client_error(client.get("/terrain", params={"lat": lat, "lon": lon}), 422)


DEEP = {
    "lat_min": -89.6, "lat_max": -89.3, "lon_min": 222.0, "lon_max": 223.0,
    "start": "2027-01-01T00:00:00Z", "end": "2027-01-03T00:00:00Z", "window_hours": 24,
}


@pytest.mark.parametrize(
    "change",
    [
        {"lat_min": -95.0},
        {"lat_max": 95.0},
        {"lat_min": -89.3, "lat_max": -89.6},  # min > max
        {"lon_min": 223.0, "lon_max": 222.0},
        {"template_id": "no-such-template"},
        {"step_min": 7},
        {"step_min": 45},
    ],
    ids=lambda c: ",".join(f"{k}={v}" for k, v in c.items()),
)
def test_deep_search_rejects_structurally_bad_body(change: dict) -> None:
    _assert_client_error(client.post("/deep-search", json={**DEEP, **change}))


def test_deep_search_end_before_start_message_mentions_order() -> None:
    r = client.post("/deep-search", json={**DEEP, "start": "2027-01-03T00:00:00Z", "end": "2027-01-01T00:00:00Z"})
    _assert_client_error(r)
    assert "end" in _text(r) and "start" in _text(r)
