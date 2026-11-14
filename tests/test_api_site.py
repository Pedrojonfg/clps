"""S8 contract tests for GET /site (mock-friendly)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

SITE01_LAT = -89.46316
SITE01_LON = 222.51045


def test_health_ok() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_site_response_contract() -> None:
    r = client.get("/site")
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