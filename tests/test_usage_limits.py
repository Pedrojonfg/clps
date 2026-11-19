"""Usage limits measured per D-20261118-pj-cd33 (docs/limits.md, scripts/bench_limits.py).

Requests just inside each limit pass validation; just above it they get 422 naming the field and the limit.
The heavy compute is replaced by stubs (validation runs before it), so these tests are cheap and need no
kernels, cap index or hazard data. The values are read from moonpark.api.app, so re-measuring and changing a
limit does not need test edits.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import moonpark.api.app as app_mod
from moonpark.providers import Site

client = TestClient(app_mod.app)
T0 = datetime(2027, 1, 1, tzinfo=timezone.utc)


def _iso(hours: float) -> str:
    return f"{T0 + timedelta(hours=hours):%Y-%m-%dT%H:%M:%S}Z"


# ------------------------------------------------------------------------------------------------ /site


@pytest.fixture
def site_stub(monkeypatch):
    """GET /site with the payload builder stubbed: records the sample count it was given."""
    import moonpark.planner_payload as pp

    seen: dict = {}

    def fake_build(site, times, **kw):
        seen["n"] = len(times)
        return {"stub": True}

    monkeypatch.setattr(pp, "build_planner_payload", fake_build)
    monkeypatch.setattr(pp, "kernels_available", lambda: True)
    return seen


def _site(hours: float, **params):
    p = {"start": _iso(0), "end": _iso(hours), "step_min": 60, "hazards_enabled": "false", **params}
    return client.get("/site", params=p)


def _assert_limit(r, field: str, limit) -> None:
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["field"] == field
    assert detail["error"] == "limit_exceeded"
    assert f"{limit:g}" in detail["message"] if isinstance(limit, float) else str(limit) in detail["message"]


def test_site_window_hours_limit(site_stub) -> None:
    lim = app_mod.SITE_MAX_WINDOW_H
    assert lim is not None and lim >= 743  # never narrower than the old 744 hourly steps
    r = _site(lim)
    assert r.status_code == 200, r.text
    assert site_stub["n"] == lim + 1
    _assert_limit(_site(lim + 1), "start/end", lim)


def test_site_samples_limit(site_stub) -> None:
    lim = app_mod.SITE_MAX_SAMPLES
    h_in = (lim - 1) // 60  # at step_min 1: h_in*60 + 1 samples <= lim < (h_in+1)*60 + 1
    assert h_in + 1 <= app_mod.SITE_MAX_WINDOW_H  # the hours limit must not fire first
    r = _site(h_in, step_min=1)
    assert r.status_code == 200, r.text
    assert site_stub["n"] == h_in * 60 + 1
    _assert_limit(_site(h_in + 1, step_min=1), "step_min", lim)


def test_site_hazards_window_limit(site_stub) -> None:
    lim = app_mod.HAZARD_MAX_SPAN_H
    assert lim is not None and float(lim).is_integer()
    assert _site(lim, hazards_enabled="true").status_code == 200
    r = _site(lim + 1, hazards_enabled="true")
    _assert_limit(r, "start/end", lim)
    assert "hazards_enabled=false" in r.json()["detail"]["message"]
    assert _site(lim + 1).status_code == 200  # hazards off: only the general limits apply


def test_site_local_search_window_limit(site_stub) -> None:
    lim = app_mod.LOCAL_SEARCH_MAX_WINDOW_H
    assert _site(lim, local_search=1).status_code == 200
    _assert_limit(_site(lim + 1, local_search=1), "local_search", lim)


def test_site_local_search_with_hazards_counts_three_windows(site_stub) -> None:
    lim = app_mod.HAZARD_MAX_SPAN_H
    h_in = int(lim // 3)
    assert h_in + 1 <= app_mod.LOCAL_SEARCH_MAX_WINDOW_H
    assert _site(h_in, local_search=1, hazards_enabled="true").status_code == 200
    _assert_limit(_site(h_in + 1, local_search=1, hazards_enabled="true"), "start/end", lim)


# ----------------------------------------------------------------------------------------- /deep-search


@pytest.fixture
def deep_stub(monkeypatch):
    """POST /deep-search with n fake cap cells and the engine stubbed; returns a setter for the cell count."""
    import moonpark.hazards as hz
    import moonpark.horizon.cap_index as ci
    import moonpark.planner_payload as pp
    from moonpark.search import deep as deep_mod

    state = {"n": 1, "called": False}

    def fake_cells(*a, **k):
        return [(Site(lat_deg=-87.0, lon_deg=float(i % 360), observer_height_m=2.0), 1000.0 * i, 0.0, 0, 0, i)
                for i in range(state["n"])]

    def fake_deep(sites, starts, wh, needs, **kw):
        state["called"] = True
        return {"mode": kw.get("mode", "optimized"), "claim": "best_seen", "best": None, "leaderboard": [],
                "export_rows": [], "rows_evaluated": 0, "runtime_s": 0.0, "eta_s": None, "n_starts": 0,
                "state": "complete", "checkpoint": None, "dropped_cells": 0}

    monkeypatch.setattr(ci, "sites_in_latlon_rect", fake_cells)
    monkeypatch.setattr(ci, "cap_index_available", lambda: True)
    monkeypatch.setattr(pp, "kernels_available", lambda: True)
    monkeypatch.setattr(deep_mod, "deep_search", fake_deep)
    monkeypatch.setattr(hz, "default_moon_hazards", lambda: object())
    return state


def _deep(state, n_cells: int, span_h: int, **body):
    state["n"] = n_cells
    state["called"] = False
    b = {"lat_min": -88.0, "lat_max": -86.0, "lon_min": 220.0, "lon_max": 224.0, "start": _iso(0),
         "end": _iso(span_h), "window_hours": 1, "mode": "optimized", "step_min": 60, "hazards_enabled": False,
         **body}
    return client.post("/deep-search", json=b)


def test_deep_cells_limit(deep_stub) -> None:
    lim = app_mod.DEEP_MAX_CELLS
    r = _deep(deep_stub, lim, 1)
    assert r.status_code == 200, r.text
    assert deep_stub["called"]
    r = _deep(deep_stub, lim + 1, 1)
    _assert_limit(r, "lat_min/lat_max/lon_min/lon_max", lim)
    assert not deep_stub["called"]


def test_deep_total_coverage_evaluations_limit(deep_stub) -> None:
    lim = app_mod.DEEP_MAX_EVALUATIONS
    cells = 100
    starts = lim // cells  # window_hours 1: n_starts = span hours
    assert cells * (starts + 1) > lim
    # the sky-sample limit (cells x (span + 1) at step 60) must not fire first
    assert app_mod.DEEP_MAX_SKY_SAMPLES is None or cells * (starts + 2) <= app_mod.DEEP_MAX_SKY_SAMPLES
    assert _deep(deep_stub, cells, starts, mode="total_coverage").status_code == 200
    r = _deep(deep_stub, cells, starts + 1, mode="total_coverage")
    _assert_limit(r, "start/end", lim)
    assert "optimized" in r.json()["detail"]["message"]
    # optimized evaluates only from its start points: the same size is accepted
    assert _deep(deep_stub, cells, starts + 1).status_code == 200


def test_deep_total_coverage_sky_samples_limit(deep_stub) -> None:
    lim = app_mod.DEEP_MAX_SKY_SAMPLES
    cells = 1000
    per_cell = lim // cells  # samples per cell = span_min / step_min + 1 at step_min 1
    span_h_in = (per_cell - 1) // 60
    assert cells * (span_h_in * 60 + 1) <= lim < cells * ((span_h_in + 1) * 60 + 1)
    assert cells * (span_h_in + 1) <= app_mod.DEEP_MAX_EVALUATIONS  # evaluations limit must not fire first
    assert _deep(deep_stub, cells, span_h_in, mode="total_coverage", step_min=1).status_code == 200
    _assert_limit(_deep(deep_stub, cells, span_h_in + 1, mode="total_coverage", step_min=1), "step_min", lim)


def test_deep_hazards_span_limit_counts_longitude_width(deep_stub) -> None:
    lim = app_mod.HAZARD_MAX_SPAN_H
    narrow = {"lon_min": 222.0, "lon_max": 222.0}
    assert _deep(deep_stub, 3, int(lim), hazards_enabled=True, **narrow).status_code == 200
    r = _deep(deep_stub, 3, int(lim) + 1, hazards_enabled=True, **narrow)
    _assert_limit(r, "start/end", lim)
    assert "hazards_enabled=false" in r.json()["detail"]["message"]
    # 36 deg of longitude add a tenth of a lunar day of local time
    extra = 36.0 / 360.0 * 708.734
    wide = {"lon_min": 200.0, "lon_max": 236.0}
    h_in = int(lim - extra)
    assert _deep(deep_stub, 3, h_in, hazards_enabled=True, **wide).status_code == 200
    _assert_limit(_deep(deep_stub, 3, h_in + 1, hazards_enabled=True, **wide), "start/end", lim)
    assert _deep(deep_stub, 3, h_in + 1, **wide).status_code == 200  # hazards off


def test_limits_are_none_able_for_the_benchmark() -> None:
    # scripts/bench_limits.py lifts these by name to measure beyond them
    for name in ("SITE_MAX_WINDOW_H", "SITE_MAX_SAMPLES", "LOCAL_SEARCH_MAX_WINDOW_H", "HAZARD_MAX_SPAN_H",
                 "DEEP_MAX_CELLS", "DEEP_MAX_EVALUATIONS", "DEEP_MAX_SKY_SAMPLES"):
        assert hasattr(app_mod, name), name
