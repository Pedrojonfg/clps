"""S9 contract tests for POST /region-map (pure transform, no kernels).

per D-20261115-pj-85bf, D-20261115-pj-8acb, D-20261115-pj-7227.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

LAT, LON = -89.46316, 222.51045


def _row(lon=LON, score=0.8, feasible=True, companion=None, **extra):
    return {
        "lat_deg": LAT,
        "lon_deg": lon,
        "score": score,
        "feasible": feasible,
        "companion_score": score if companion is None else companion,
        **extra,
    }


def test_region_map_total_coverage():
    body = {
        "rows": [_row(lon=10.0), _row(lon=100.0, score=0.0, feasible=False, companion=0.3)],
        "search_partial": False,
        "best": None,
    }
    r = client.post("/region-map", json=body)
    assert r.status_code == 200
    p = r.json()
    assert p["score_ceiling"] == 1.4  # per D-7227 D-48ee
    assert p["search_partial"] is False
    assert p["n_evaluated"] == 2 and p["n_induced"] == 0
    assert len(p["samples"]) == 2
    for s in p["samples"]:
        assert {
            "lat_deg", "lon_deg", "score", "feasible", "companion_score",
            "induced", "rgba", "is_best",
        } <= s.keys()
        assert s["induced"] is False
        assert len(s["rgba"]) == 4
    black = [s for s in p["samples"] if not s["feasible"]][0]
    assert black["rgba"][:3] == [0, 0, 0]  # per D-8acb


def test_region_map_partial_induces_and_marks_best():
    row = _row()
    r = client.post(
        "/region-map",
        json={"rows": [row], "search_partial": True, "best": row},
    )
    assert r.status_code == 200
    p = r.json()
    assert p["search_partial"] is True
    assert p["n_evaluated"] == 1 and p["n_induced"] == 4  # per D-85bf
    assert len(p["samples"]) == 5
    assert sum(s["is_best"] for s in p["samples"]) == 1
    induced = [s for s in p["samples"] if s["induced"]]
    assert all(s["rgba"][3] == 0.45 for s in induced)
    assert all(s["rgba"][3] == 1.0 for s in p["samples"] if not s["induced"])


def test_region_map_clamps_out_of_range_score_to_green():
    # per D-7227: score 2.0 must not crash; same colour as ceiling
    hi = client.post(
        "/region-map",
        json={"rows": [_row(score=2.0)], "search_partial": False, "best": None},
    ).json()["samples"][0]["rgba"]
    ceil = client.post(
        "/region-map",
        json={"rows": [_row(score=1.4)], "search_partial": False, "best": None},
    ).json()["samples"][0]["rgba"]
    assert hi == ceil


def test_region_map_empty_rows():
    r = client.post("/region-map", json={"rows": [], "search_partial": False, "best": None})
    assert r.status_code == 200
    p = r.json()
    assert p["samples"] == [] and p["n_evaluated"] == 0
