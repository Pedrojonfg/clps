"""POST /deep-search and deep_search() contract from the audit decisions.

per D-20261118-pj-75f1 (every search uses the user's requirements; unevaluable -> warn;
cell without hazard data -> dropped and counted; missing PSR never blocks),
D-20261118-pj-1454 (no hard time stop; Stop; resumable), D-20261118-pj-cd33 (coverage limit),
D-20261118-pj-70ec (explicit field > template > default), D-20261118-pj-b3dc (hazards 'unavailable').

Real Site01 data on a 3-cell rectangle (see RECT) with 24 h windows at step 60; small and fast.
Naming assumptions the implementation must follow are listed in the report next to this file's tests:
  - response keys: requirements, warnings, dropped_cells, state, (checkpoint when stopped)
  - moonpark.search.deep.UNEVALUABLE_REQUIREMENTS (module-level set, read at call time)
  - deep_search(..., should_stop=None, resume=None) returning state and checkpoint
  - body fields job_id, resume; POST /deep-search/stop {job_id} -> {"stopped": bool}
  - default_moon_hazards is looked up at call time (patched on moonpark.hazards / moonpark.hazards.moon)
"""

from __future__ import annotations

import inspect
import json
import threading
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient

from moonpark.api.app import DeepSearchBody, app, site as site_endpoint
from moonpark.providers import Site
from moonpark.search import deep as deep_mod
from moonpark.search.deep import deep_search

client = TestClient(app)

REQUIREMENT_FIELDS = (
    "max_night_h", "max_no_earth_h", "require_both", "min_continuous_lit_h", "min_total_lit_h",
    "sun_lit_percent", "earth_lit_percent", "bridge_h", "battery_wh", "array_w", "dark_w",
    "endurance_h", "lit_w", "panel", "panel_az_deg", "reserve_pct", "charge_eff",
    "max_temperature_k", "min_temperature_k", "min_soil_resistance", "hazards_enabled",
)

# 3 cells (Site01 and its two neighbours along the cap), all inside the 1 km cap index.
RECT = {"lat_min": -89.52, "lat_max": -89.40, "lon_min": 222.0, "lon_max": 223.0}
SITE01_LAT = -89.463162834037
START = "2027-01-01T00:00:00Z"
END_1WIN = "2027-01-02T00:00:00Z"  # exactly one 24 h window start
END_2WIN = "2027-01-02T01:00:00Z"  # two window starts


def _data_available() -> bool:
    try:
        from moonpark.horizon.cap_index import cap_index_available
        from moonpark.planner_payload import kernels_available

        return bool(kernels_available() and cap_index_available())
    except Exception:
        return False


needs_data = pytest.mark.skipif(not _data_available(), reason="SPICE kernels / cap index not on disk")


@pytest.fixture(autouse=True)
def _client_masks(monkeypatch):
    """Environment only: reproduce a client machine (no DEMs, no cached own-DEM masks), where /site snaps to
    the nearest 1 km cap cell mask, the same mask the search uses. A dev machine with DEMs computes own-DEM
    masks for /site that differ from the precomputed cap masks, which these equivalence checks do not test."""
    import moonpark.horizon.mask_store as ms

    monkeypatch.setattr(ms, "load_cached_mask", lambda site: None)
    monkeypatch.setattr(ms, "mask_schedule_for_site", lambda *a, **k: None)


def _deep(extra: dict | None = None, end: str = END_1WIN, **kw):
    body = {**RECT, "start": START, "end": end, "window_hours": 24, "mode": "total_coverage",
            "hazards_enabled": False, **(extra or {})}
    return client.post("/deep-search", json=body, **kw)


def _rows(payload: dict) -> list[dict]:
    return payload.get("export_rows") or payload.get("leaderboard") or []


def _end_of(window_start: str, hours: int = 24) -> str:
    t = datetime.fromisoformat(window_start.rstrip("Z")).replace(tzinfo=timezone.utc) + timedelta(hours=hours)
    return f"{t:%Y-%m-%dT%H:%M:%S}Z"


def _site_for(row: dict, extra: dict) -> dict:
    params = {
        "lat": row["site"]["lat_deg"], "lon": row["site"]["lon_deg"], "start": row["window_start"],
        "end": _end_of(row["window_start"], row["window_hours"]), "step_min": 60,
        "hazards_enabled": False, **extra,  # same default as _deep(): both paths get the same request
    }
    params = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in params.items()}
    r = client.get("/site", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _assert_equivalent(extra: dict, end: str = END_1WIN, max_rows: int = 3) -> list[dict]:
    """Every checked deep row has the same feasible/score as GET /site; requirements equal /site needs."""
    r = _deep(extra, end=end)
    assert r.status_code == 200, r.text
    p = r.json()
    rows = _rows(p)
    assert rows, "deep search returned no rows"
    # first, middle, last of the ranking: covers different cells
    picks = [rows[i] for i in sorted({0, len(rows) // 2, len(rows) - 1})][:max_rows]
    first_site = None
    for row in picks:
        s = _site_for(row, extra)
        assert row["feasible"] == s["score"]["feasible"], (row["site"], row["window_start"])
        assert row["score"] == pytest.approx(s["score"]["score"], abs=1e-9), (row["site"], row["window_start"])
        first_site = first_site or s
    req = p.get("requirements")
    assert isinstance(req, dict), "response has no 'requirements' dict"
    assert req == first_site["needs"], "requirements must equal the /site payload['needs']"
    return rows


# --------------------------------------------------------------------------- 1. requirement fields


def test_body_has_requirement_fields_with_site_defaults() -> None:
    fields = DeepSearchBody.model_fields
    sig = inspect.signature(site_endpoint).parameters
    missing = [n for n in REQUIREMENT_FIELDS if n not in fields]
    assert not missing, f"DeepSearchBody lacks requirement fields: {missing}"
    for name in REQUIREMENT_FIELDS:
        assert fields[name].default == sig[name].default.default, f"default of {name} differs from /site"


@needs_data
def test_default_requirements_are_the_site_defaults() -> None:
    p = _deep().json()
    s = _site_for(_rows(p)[0], {"hazards_enabled": False})
    assert p.get("requirements") == s["needs"]


@needs_data
def test_explicit_fields_win_over_template_and_template_over_default() -> None:
    with_tpl = _deep({"template_id": "viper_nominal"}).json()
    req = with_tpl.get("requirements") or {}
    assert req.get("max_night_h") == 50 and req.get("max_no_earth_h") == 24  # template, not 72/48
    explicit = _deep({"template_id": "viper_nominal", "max_night_h": 7, "sun_lit_percent": 10}).json()
    req = explicit.get("requirements") or {}
    assert req.get("max_night_h") == 7  # explicit wins
    assert req.get("max_no_earth_h") == 24  # untouched field still from template
    assert req.get("sun_lit_percent") == 10.0


@needs_data
def test_verdict_equivalence_with_site_defaults() -> None:
    _assert_equivalent({}, end=END_2WIN)


@needs_data
def test_total_lit_requirement_changes_verdict_and_matches_site() -> None:
    base = _rows(_deep().json())
    assert any(r["feasible"] for r in base)
    constrained = _assert_equivalent({"min_total_lit_h": 1000})
    assert all(not r["feasible"] for r in constrained), "1000 lit hours in a 24 h window cannot be met"


@needs_data
def test_battery_energy_mode_changes_verdict_and_matches_site() -> None:
    base = _rows(_deep().json())
    assert any(r["feasible"] for r in base)
    energy = {"battery_wh": 1, "array_w": 1, "dark_w": 100}  # 1 Wh cannot carry 100 W through any darkness
    rows = _assert_equivalent(energy)
    assert all(not r["feasible"] for r in rows)
    ok = _rows(_deep({"battery_wh": 1000, "array_w": 500, "dark_w": 1}).json())
    assert any(r["feasible"] for r in ok)


@needs_data
def test_hazard_limits_are_evaluated_and_match_site() -> None:
    off = _rows(_deep({"hazards_enabled": False, "max_temperature_k": "100"}).json())
    assert any(r["feasible"] for r in off)  # hazards off: the limit is not applied
    rows = _assert_equivalent({"hazards_enabled": True, "max_temperature_k": "100", "min_temperature_k": "",
                               "min_soil_resistance": "none"})
    assert all(not r["feasible"] for r in rows), "polar cells exceed 100 K at some hour"


# --------------------------------------------------------------------------- 2. response metadata


@needs_data
def test_response_carries_requirements_warnings_dropped_and_state() -> None:
    p = _deep().json()
    assert isinstance(p.get("requirements"), dict) and p["requirements"].get("max_night_h") == 72
    assert p.get("warnings") == []
    assert p.get("dropped_cells") == 0
    assert p.get("state") == "complete"


# --------------------------------------------------------------------------- 3. hazard-data drop


class _FakeHazards:
    """Layer-B shaped result; the Site01 cell is 'unavailable' (D-b3dc contract) when drop_site01."""

    def __init__(self, drop_site01: bool, psr_missing: bool = False) -> None:
        self.drop_site01, self.psr_missing = drop_site01, psr_missing

    def hazards(self, site, times) -> dict:
        psr = {"in_psr": False, "message": None}
        agg = {"temperature_k": 200.0, "temperature_min_k": 150.0, "soil_resistance": 1.0, "slope_deg": 1.0,
               "psr": psr, "unavailable": {}}
        unavailable: dict = {}
        if self.drop_site01 and abs(site.lat_deg - SITE01_LAT) < 1e-6:
            reason = "temperature data missing"
            agg.update(temperature_k=None, temperature_min_k=None, unavailable={"temperature": reason})
            unavailable = {"temperature": reason}
        out = {"hours": [], "aggregate": agg, "psr_precheck": psr, "unavailable": unavailable}
        if self.psr_missing:
            out["psr_precheck"] = {"status": "missing"}
        return out


def _patch_hazards(monkeypatch, provider) -> None:
    import moonpark.hazards as hz
    import moonpark.hazards.moon as hm

    monkeypatch.setattr(hz, "default_moon_hazards", lambda *a, **k: provider)
    monkeypatch.setattr(hm, "default_moon_hazards", lambda *a, **k: provider)


@needs_data
def test_cell_without_hazard_data_is_dropped_and_counted(monkeypatch) -> None:
    _patch_hazards(monkeypatch, _FakeHazards(drop_site01=True))
    p = _deep({"hazards_enabled": True}, end=END_2WIN).json()
    rows = _rows(p)
    assert rows, "other cells must remain"
    assert all(abs(r["site"]["lat_deg"] - SITE01_LAT) > 1e-6 for r in rows), "dropped cell still in results"
    assert len({round(r["site"]["lat_deg"], 6) for r in rows}) == 2
    assert p.get("dropped_cells") == 1
    codes = {w.get("code"): w for w in p.get("warnings") or []}
    assert "cells_dropped_hazard_data" in codes
    assert "1" in codes["cells_dropped_hazard_data"].get("message", "")


@needs_data
def test_nothing_dropped_when_hazards_disabled(monkeypatch) -> None:
    _patch_hazards(monkeypatch, _FakeHazards(drop_site01=True))
    p = _deep({"hazards_enabled": False}).json()
    assert any(abs(r["site"]["lat_deg"] - SITE01_LAT) < 1e-6 for r in _rows(p))
    assert p.get("dropped_cells") == 0
    assert "cells_dropped_hazard_data" not in {w.get("code") for w in p.get("warnings") or []}


@needs_data
def test_missing_psr_map_never_drops(monkeypatch) -> None:
    _patch_hazards(monkeypatch, _FakeHazards(drop_site01=False, psr_missing=True))
    p = _deep({"hazards_enabled": True}).json()
    assert len({round(r["site"]["lat_deg"], 6) for r in _rows(p)}) == 3
    assert p.get("dropped_cells") == 0
    assert "cells_dropped_hazard_data" not in {w.get("code") for w in p.get("warnings") or []}


# --------------------------------------------------------------------------- 4. unevaluable requirement


@needs_data
def test_unevaluable_requirement_is_warned_and_search_continues(monkeypatch) -> None:
    monkeypatch.setattr(deep_mod, "UNEVALUABLE_REQUIREMENTS", {"min_total_lit_h"}, raising=False)
    p = _deep({"min_total_lit_h": 1000}).json()
    warns = [w for w in p.get("warnings") or [] if w.get("code") == "requirement_not_evaluated"]
    assert warns, f"no requirement_not_evaluated warning; warnings={p.get('warnings')}"
    assert any("min_total_lit_h" in json.dumps(w) for w in warns)
    assert any(r["feasible"] for r in _rows(p)), "skipped requirement must not be applied"
    assert p.get("state") == "complete"


@needs_data
def test_no_unevaluated_warning_when_requirement_not_requested(monkeypatch) -> None:
    monkeypatch.setattr(deep_mod, "UNEVALUABLE_REQUIREMENTS", {"min_total_lit_h"}, raising=False)
    p = _deep({"min_total_lit_h": 0}).json()
    assert "requirement_not_evaluated" not in {w.get("code") for w in p.get("warnings") or []}
    assert isinstance(p.get("warnings"), list)


# --------------------------------------------------------------------------- synthetic engine helpers

NEEDS = {"max_night_h": 50, "max_no_earth_h": 20, "require_both": False}
T0 = np.datetime64("2026-06-01T12:00", "s")
HOURS = 4


def _grid() -> tuple[list[Site], list[tuple[float, float]]]:
    sites = [Site(lat_deg=-89.5 + iy * 0.001, lon_deg=ix * 0.001) for iy in range(3) for ix in range(3)]
    xy = [(float(ix * 1000), float(iy * 1000)) for iy in range(3) for ix in range(3)]
    return sites, xy


def _starts(n: int = 4) -> np.ndarray:
    return T0 + np.arange(n, dtype="int64").astype("timedelta64[h]")


def _make_eval(sites, starts, counter: list | None = None, sleep: float = 0.0):
    def evaluate(site, start, hours):
        if counter is not None:
            counter.append(1)
        if sleep:
            time.sleep(sleep)
        si = next(i for i, s in enumerate(sites) if s.lat_deg == site.lat_deg and s.lon_deg == site.lon_deg)
        ti = int((np.datetime64(start, "s") - starts[0]) / np.timedelta64(1, "h"))
        night = 10 + ((si * 7 + ti * 3) % 11) * 4  # some rows infeasible (night > 50)
        return {"series": {"longest_night_h": night, "longest_no_earth_h": 5 + (si + ti) % 4, "any_both": True}}

    return evaluate


def _norm_row(row):
    if row is None:
        return None
    out = dict(row)
    out["window_start"] = str(np.datetime64(str(row["window_start"]).rstrip("Z"), "s"))
    return out


def _signature(res: dict) -> str:
    keep = {
        "best": _norm_row(res["best"]),
        "leaderboard": [_norm_row(r) for r in res["leaderboard"]],
        "export_rows": sorted((_norm_row(r) for r in res["export_rows"]), key=lambda r: (r["site"]["lat_deg"], r["site"]["lon_deg"], r["window_start"])),
        "rows_evaluated": res["rows_evaluated"],
    }
    return json.dumps(keep, sort_keys=True, default=str)


def _run(mode: str, *, start_n=None, **kw):
    sites, xy = _grid()
    starts = _starts()
    counter: list = []
    res = deep_search(sites, starts, HOURS, NEEDS, evaluate=_make_eval(sites, starts, counter),
                      mode=mode, start_n=start_n, site_xy=xy, **kw)
    return res, len(counter)


# --------------------------------------------------------------------------- 5. no hard time stop


def test_tiny_time_budget_does_not_stop_total_coverage() -> None:
    big, _ = _run("total_coverage", tmax_s=1e6)
    sites, xy = _grid()
    starts = _starts()
    slow = deep_search(sites, starts, HOURS, NEEDS, evaluate=_make_eval(sites, starts, sleep=0.005),
                       mode="total_coverage", site_xy=xy, tmax_s=0.0001)
    assert slow["rows_evaluated"] == len(sites) * len(starts)
    assert _signature(slow) == _signature(big)
    assert slow.get("state") == "complete"
    assert big.get("state") == "complete"


def test_tiny_time_budget_does_not_stop_optimized_with_explicit_starts() -> None:
    big, n_big = _run("optimized", start_n=3, tmax_s=1e6)
    small, n_small = _run("optimized", start_n=3, tmax_s=0.0001)
    assert n_small == n_big
    assert _signature(small) == _signature(big)
    assert small.get("state") == "complete"


# --------------------------------------------------------------------------- 6. stop and resume


@pytest.mark.parametrize("mode", ["total_coverage", "optimized"])
@pytest.mark.parametrize("stop_after", [1, 4])
def test_stop_then_resume_equals_uninterrupted_run(mode: str, stop_after: int) -> None:
    start_n = 3 if mode == "optimized" else None
    full, n_full = _run(mode, start_n=start_n)
    assert n_full > stop_after + 1

    calls: list = []
    sites, xy = _grid()
    starts = _starts()
    ev = _make_eval(sites, starts, calls)
    stopped = deep_search(sites, starts, HOURS, NEEDS, evaluate=ev, mode=mode, start_n=start_n, site_xy=xy,
                          should_stop=lambda: len(calls) >= stop_after)
    assert stopped.get("state") == "stopped", "should_stop() True must yield state 'stopped'"
    assert len(calls) <= stop_after + 1, "stop must be honoured promptly (between evaluations)"
    cp = stopped.get("checkpoint")
    assert isinstance(cp, dict) and cp, "stopped result needs a checkpoint dict"
    cp = json.loads(json.dumps(cp))  # JSON-serialisable and survives a save/reload
    assert 1 <= stopped["rows_evaluated"] <= stop_after + 1
    for row in stopped["export_rows"]:
        assert {"site", "window_start", "window_hours", "feasible", "score", "companion_score"} <= row.keys()

    calls2: list = []
    resumed = deep_search(sites, starts, HOURS, NEEDS, evaluate=_make_eval(sites, starts, calls2), mode=mode,
                          start_n=start_n, site_xy=xy, resume=cp)
    assert resumed.get("state") == "complete"
    assert _signature(resumed) == _signature(full)
    assert len(calls2) < n_full, "resume must not redo the evaluations already in the checkpoint"


def test_complete_run_has_state_complete() -> None:
    res, _ = _run("total_coverage")
    assert res.get("state") == "complete"


# --- API stop


@needs_data
def test_api_stop_halts_running_job_and_returns_checkpoint(monkeypatch) -> None:
    started, seen = threading.Event(), {}

    def fake_deep_search(sites, starts, wh, needs, *, should_stop=None, resume=None, **kw):
        seen["should_stop"], seen["resume"] = should_stop, resume
        started.set()
        deadline = time.time() + 10
        while should_stop is not None and not should_stop() and time.time() < deadline:
            time.sleep(0.005)
        stopped = should_stop is not None and should_stop()
        return {"mode": kw.get("mode", "optimized"), "claim": "best_seen", "best": None, "leaderboard": [],
                "export_rows": [], "rows_evaluated": 0, "runtime_s": 0.0, "eta_s": None, "n_starts": 0,
                "state": "stopped" if stopped else "complete", "checkpoint": {"rows": []} if stopped else None,
                "warnings": [], "dropped_cells": 0}

    monkeypatch.setattr(deep_mod, "deep_search", fake_deep_search)
    result: dict = {}

    def run() -> None:
        with TestClient(app) as c:
            result["r"] = c.post("/deep-search", json={**RECT, "start": START, "end": END_1WIN, "window_hours": 24,
                                                       "job_id": "job-stop-1", "resume": {"rows": [1]}})

    t = threading.Thread(target=run)
    t.start()
    assert started.wait(15), "deep_search was not reached"
    assert callable(seen.get("should_stop")), "endpoint must pass should_stop to deep_search"
    assert seen["resume"] == {"rows": [1]}, "endpoint must pass the request's resume checkpoint through"
    r = client.post("/deep-search/stop", json={"job_id": "job-stop-1"})
    t.join(15)
    assert r.status_code == 200 and r.json() == {"stopped": True}
    resp = result["r"]
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("state") == "stopped" and isinstance(body.get("checkpoint"), dict)


def test_api_stop_unknown_job_is_not_stopped() -> None:
    r = client.post("/deep-search/stop", json={"job_id": "no-such-job"})
    assert r.status_code == 200 and r.json() == {"stopped": False}


# --------------------------------------------------------------------------- 7. coverage


@pytest.mark.parametrize("lat_min,lat_max", [(-89.5, -59.0), (-89.5, 0.0), (-30.0, -20.0)])
def test_latitude_beyond_coverage_is_422_naming_coverage(lat_min: float, lat_max: float) -> None:
    r = client.post("/deep-search", json={"lat_min": lat_min, "lat_max": lat_max, "lon_min": 0.0, "lon_max": 10.0,
                                          "start": START, "end": END_1WIN, "window_hours": 24})
    assert r.status_code == 422, r.text
    assert "coverage" in json.dumps(r.json()).lower()
