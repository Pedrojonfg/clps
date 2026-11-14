"""S8 contract tests for GET /site (mock-friendly)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import app
from lunar_eval.site01 import real_data_available

client = TestClient(app)
REPO = Path(__file__).resolve().parents[1]

SITE01_LAT = -89.46316
SITE01_LON = 222.51045


def test_health_ok() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_site_response_contract() -> None:
    r = client.get("/site?mock=1")
    assert r.status_code == 200
    payload = r.json()

    mask = payload["mask"]
    assert len(mask["elevation_deg"]) == 720
    assert "schedule_version" in mask
    assert "lat" in mask and "lon" in mask

    sky = payload["sky"]
    assert isinstance(sky, list) and len(sky) >= 1
    sample = sky[0]
    for key in ("time_utc", "sun_az_deg", "sun_el_deg", "earth_az_deg", "earth_el_deg"):
        assert key in sample

    series = payload["series"]
    for key in (
        "sun_fraction",
        "earth_fraction",
        "longest_night_h",
        "longest_no_earth_h",
        "any_both",
    ):
        assert key in series
    assert len(series["sun_fraction"]) == len(sky)
    assert len(series["earth_fraction"]) == len(sky)

    score = payload["score"]
    assert {"score", "feasible", "breakdown", "provenance"} <= score.keys()
    prov = score["provenance"]
    assert {"score_formula", "schedule_version"} <= prov.keys()
    if score["feasible"] is False:
        assert score["score"] == 0

    needs = payload["needs"]
    assert "max_night_h" in needs and "max_no_earth_h" in needs
    assert payload.get("data_source") in ("mock", "real")


def test_site_without_mock_and_no_data_returns_503() -> None:
    if real_data_available():
        pytest.skip("real data present")
    r = client.get("/site")
    assert r.status_code == 503
    assert r.json()["detail"]["error"] in ("kernels_missing", "dem_missing", "planner_failed")


def test_mission_templates_ten() -> None:
    r = client.get("/mission-templates")
    assert r.status_code == 200
    assert len(r.json()["templates"]) == 10


@pytest.mark.skipif(not real_data_available(), reason="Site01 DEM or kernels not present")
def test_site_real_mask_not_mock_ridge() -> None:
    r = client.get(
        "/site",
        params={
            "start": "2027-01-01T00:00:00Z",
            "end": "2027-01-01T23:00:00Z",
            "hazards_enabled": "false",
        },
    )
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["data_source"] == "real"
    ptp = max(payload["mask"]["elevation_deg"]) - min(payload["mask"]["elevation_deg"])
    assert ptp > 1.0
    assert payload["score"]["provenance"]["schedule_version"] == "D-f369-v1"
    assert len(payload["sky"]) == 24