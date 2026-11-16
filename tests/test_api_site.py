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

def test_mock_mask_azimuth_convention_reproduces_fractions() -> None:
    # per D-20261116-pj-b43a: the mask read through the stated convention at each Sun azimuth
    # must reproduce the payload's own sun_fraction (this is what every view draws).
    import math

    p = client.get("/site?mock=1").json()
    mask = p["mask"]
    assert mask["azimuth_zero_deg"] == 180.0 and mask["azimuth_sign"] == -1
    elev = mask["elevation_deg"]

    def mask_at_geo(az: float) -> float:
        f = ((mask["azimuth_sign"] * (az - mask["azimuth_zero_deg"])) % 360.0) * len(elev) / 360.0
        i = int(f) % len(elev)
        t = f - int(f)
        return elev[i] * (1 - t) + elev[(i + 1) % len(elev)] * t

    fracs = p["series"]["sun_fraction"]
    assert 0.0 in fracs and 1.0 in fracs and any(0.05 < f < 0.95 for f in fracs)  # didactic mock
    for s, frac in zip(p["sky"], fracs, strict=True):
        x = max(-1.0, min(1.0, (s["sun_el_deg"] - mask_at_geo(s["sun_az_deg"])) / 0.2665))
        want = 1.0 - (math.acos(x) - x * math.sqrt(1.0 - x * x)) / math.pi
        assert frac == pytest.approx(want, abs=2e-3)


def test_mock_local_search_block_has_real_shape_and_order() -> None:
    # per D-20261116-pj-4902: mock ships a leaderboard so the top-N UI can be checked.
    from lunar_eval.search.local import _sort_key

    p = client.get("/site?mock=1&local_search=1").json()
    assert p["data_source"] == "mock"
    ls = p["local_search"]
    board = ls["leaderboard"]
    assert len(board) == 2 * (len(p["sky"]) - 1) + 1  # hourly slide a-h .. a+h (D-9cc5)
    for row in board:
        assert {
            "site", "window_start", "window_hours", "feasible", "score",
            "companion_score", "hazard_gap_star", "distance_hours", "distance_km",
        } <= row.keys()
        if not row["feasible"]:
            assert row["score"] == 0
    assert board == sorted(board, key=_sort_key)
    assert ls["pick"] == board[0]
    assert any(not r["feasible"] for r in board) and any(r["hazard_gap_star"] for r in board)


def test_site_without_local_search_flag_has_no_local_search_block() -> None:
    # per D-ecc9: flag off skips the search.
    payload = client.get("/site?mock=1").json()
    assert payload.get("local_search") is None


@pytest.mark.skipif(not real_data_available(), reason="Site01 DEM or kernels not present")
def test_site_local_search_flag_returns_pick_and_leaderboard() -> None:
    # per D-ecc9: GET /site?local_search=1 returns local_search {pick, leaderboard}.
    r = client.get(
        "/site",
        params={
            "start": "2027-01-01T00:00:00Z",
            "end": "2027-01-01T23:00:00Z",
            "hazards_enabled": "false",
            "local_search": 1,
        },
    )
    assert r.status_code == 200, r.text
    ls = r.json()["local_search"]
    assert {"pick", "leaderboard"} <= ls.keys()
    assert isinstance(ls["leaderboard"], list) and ls["leaderboard"]
    row = ls["leaderboard"][0]
    assert {"site", "window_start", "feasible", "score", "companion_score", "hazard_gap_star"} <= row.keys()
    off = client.get(
        "/site",
        params={"start": "2027-01-01T00:00:00Z", "end": "2027-01-01T23:00:00Z", "hazards_enabled": "false"},
    ).json()
    assert off.get("local_search") is None
