"""Lane W2a: site integration decisions (D-b3dc, D-70ec, D-1bc9, D-cd33, D-62d3, D-75f1).

Failures must be assertion failures (guards via .get), never KeyError/AttributeError.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient

from moonpark.api.app import app
from moonpark.site01 import real_data_available

pytestmark = pytest.mark.skipif(not real_data_available(), reason="kernels or Site01 data not present")

client = TestClient(app, raise_server_exceptions=False)
WINDOW = {"start": "2027-01-01T00:00:00Z", "end": "2027-01-01T06:00:00Z"}


def _site(**params) -> Any:
    return client.get("/site", params={**WINDOW, **params})


def _ok(r) -> dict:
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"
    return r.json()


def _text(r) -> str:
    return r.text.lower()


class FakeHazards:
    """Provider shaped like MoonHazards.hazards(): aggregate + top-level 'unavailable'."""

    def __init__(self, unavailable: dict[str, str] | None = None) -> None:
        self.unavailable = dict(unavailable or {})

    def hazards(self, site, times) -> dict:
        temp_ok = "temperature" not in self.unavailable
        soil_ok = "soil_resistance" not in self.unavailable
        agg = {
            "temperature_k": 200.0 if temp_ok else None,
            "temperature_min_k": 100.0 if temp_ok else None,
            "soil_resistance": 5.0 if soil_ok else None,
            "slope_deg": 3.0,
            "psr": {"in_psr": False, "message": None},
            "unavailable": dict(self.unavailable),
        }
        return {"hours": [], "aggregate": agg, "psr_precheck": agg["psr"], "unavailable": dict(self.unavailable)}


def _patch_hazards(monkeypatch, unavailable: dict[str, str] | None) -> None:
    import moonpark.hazards as hz

    monkeypatch.setattr(hz, "default_moon_hazards", lambda: FakeHazards(unavailable))


# ---------------------------------------------------------------- 1. hazard data missing (D-b3dc)

def test_hazards_all_available_status_ok(monkeypatch) -> None:
    _patch_hazards(monkeypatch, None)
    p = _ok(_site(min_temperature_k="150"))
    hs = p.get("hazards_status")
    assert isinstance(hs, dict), f"hazards_status missing: {hs!r}"
    assert hs.get("status") == "ok", hs
    assert hs.get("unavailable") == {}, hs
    assert p.get("warnings") == [], p.get("warnings")
    assert (p.get("needs") or {}).get("not_evaluated") == [], (p.get("needs") or {}).get("not_evaluated")
    assert not p["score"].get("hazard_gap_star")


def test_hazards_temperature_unavailable(monkeypatch) -> None:
    _patch_hazards(monkeypatch, {"temperature": "no PCP data"})
    p = _ok(_site(min_temperature_k="150"))  # max (320 default) and min both set
    hs = p.get("hazards_status") or {}
    assert hs.get("status") == "partial", hs
    assert "temperature" in (hs.get("unavailable") or {}), hs
    needs = p["needs"]
    assert sorted(needs.get("not_evaluated") or []) == ["max_temperature_k", "min_temperature_k"], needs.get("not_evaluated")
    # the requirement does not silently disappear
    assert needs.get("max_temperature_k") == 320.0 and needs.get("min_temperature_k") == 150.0
    warns = p.get("warnings")
    assert isinstance(warns, list) and len(warns) == 1, warns
    w = warns[0]
    assert w.get("code") == "hazard_data_unavailable", w
    assert sorted(w.get("fields") or []) == ["max_temperature_k", "min_temperature_k"] or "temperature" in (w.get("fields") or []), w
    assert isinstance(w.get("message"), str) and w["message"], w
    assert p["score"].get("hazard_gap_star") is True


def test_hazards_soil_unavailable(monkeypatch) -> None:
    _patch_hazards(monkeypatch, {"soil_resistance": "no slope data"})
    # A minimum limit of 0 constrains nothing (D-b3dc: nothing to evaluate), so the soil limit must be set.
    p = _ok(_site(min_soil_resistance="10"))
    hs = p.get("hazards_status") or {}
    assert hs.get("status") == "partial", hs
    assert "soil_resistance" in (hs.get("unavailable") or {}), hs
    assert (p["needs"].get("not_evaluated") or []) == ["min_soil_resistance"], p["needs"].get("not_evaluated")
    assert p["needs"].get("min_soil_resistance") == 10.0
    warns = p.get("warnings") or []
    assert [w.get("code") for w in warns] == ["hazard_data_unavailable"], warns
    assert p["score"].get("hazard_gap_star") is True


def test_hazards_unavailable_no_limit_set_means_no_gap_star(monkeypatch) -> None:
    _patch_hazards(monkeypatch, {"temperature": "no PCP data"})
    p = _ok(_site(max_temperature_k="", min_temperature_k=""))  # both temperature limits switched off
    assert (p["needs"].get("not_evaluated") or []) == [], p["needs"].get("not_evaluated")
    assert not p["score"].get("hazard_gap_star")


def test_hazards_unavailable_lists_not_evaluated_and_stars_gap(monkeypatch) -> None:
    # Renamed: it never asserted viability; it checks the not-evaluated list, the gap star and no substitutes.
    # Default soil limit is 0 (constrains nothing), so only the temperature limit can be unevaluated.
    _patch_hazards(monkeypatch, {"temperature": "x", "soil_resistance": "y"})
    p = _ok(_site())
    assert p["sky"] and p["series"]["sun_fraction"]
    assert sorted(p["needs"].get("not_evaluated") or []) == ["max_temperature_k"]
    assert p["score"].get("hazard_gap_star") is True
    # no substitute values: score hazard margins carry nothing for the missing quantities
    margins = p["score"]["provenance"].get("hazard_margins") or {}
    assert not any(v is not None for k, v in margins.items() if "temp" in k or "soil" in k or "dust" in k), margins


def test_hazards_disabled_status_and_no_warnings(monkeypatch) -> None:
    p = _ok(_site(hazards_enabled="false"))
    hs = p.get("hazards_status") or {}
    assert hs.get("status") == "disabled", hs
    assert p.get("warnings") == [], p.get("warnings")
    assert (p["needs"].get("not_evaluated") or []) == [], p["needs"].get("not_evaluated")


def test_missing_psr_is_silent(monkeypatch) -> None:
    class NoPsr(FakeHazards):
        def hazards(self, site, times):
            out = super().hazards(site, times)
            out["psr_precheck"] = {"in_psr": False, "message": None, "status": "psr_map_missing"}
            return out

    import moonpark.hazards as hz

    monkeypatch.setattr(hz, "default_moon_hazards", lambda: NoPsr())
    p = _ok(_site())
    assert (p.get("hazards_status") or {}).get("status") == "ok", p.get("hazards_status")
    assert p.get("warnings") == []


# ---------------------------------------------------------------- 2. templates (D-70ec)

def test_template_alone_fills_all_and_keeps_id(monkeypatch) -> None:
    _patch_hazards(monkeypatch, None)
    p = _ok(_site(template_id="artemis_iii_stay"))
    n = p["needs"]
    assert (n["max_night_h"], n["max_no_earth_h"], n["require_both"]) == (24, 12, True)
    assert (n["sun_lit_percent"], n["earth_lit_percent"], n["bridge_h"]) == (50, 50, 5)
    assert n.get("template_id") == "artemis_iii_stay"


@pytest.mark.parametrize(
    "param,value,key,expected",
    [
        ("max_night_h", "10", "max_night_h", 10),
        ("max_no_earth_h", "7", "max_no_earth_h", 7),
        ("min_continuous_lit_h", "3", "min_continuous_lit_h", 3),
        ("require_both", "false", "require_both", False),
        ("sun_lit_percent", "10", "sun_lit_percent", 10.0),
        ("earth_lit_percent", "20", "earth_lit_percent", 20.0),
        ("bridge_h", "2", "bridge_h", 2),
    ],
)
def test_explicit_value_wins_over_template_and_makes_it_custom(monkeypatch, param, value, key, expected) -> None:
    _patch_hazards(monkeypatch, None)
    p = _ok(_site(template_id="artemis_iii_stay", **{param: value}))
    n = p["needs"]
    assert n.get(key) == expected, f"{key}: {n.get(key)!r}"
    assert n.get("template_id") is None, n.get("template_id")
    # unrelated template fields still fill in
    if key != "max_night_h":
        assert n["max_night_h"] == 24
    if key != "sun_lit_percent":
        assert n["sun_lit_percent"] == 50


def test_explicit_values_equal_to_template_keep_id(monkeypatch) -> None:
    _patch_hazards(monkeypatch, None)
    p = _ok(_site(template_id="artemis_iii_stay", max_night_h="24", require_both="true", sun_lit_percent="50"))
    assert p["needs"].get("template_id") == "artemis_iii_stay"
    assert p["needs"]["max_night_h"] == 24


# ---------------------------------------------------------------- 3. provenance (D-1bc9)

def test_provenance_shape_and_values(monkeypatch) -> None:
    _patch_hazards(monkeypatch, None)
    p = _ok(_site(max_night_h="30", step_min="30"))
    prov = p.get("provenance")
    assert isinstance(prov, dict), f"provenance missing: {prov!r}"
    assert isinstance(prov.get("engine_version"), str) and prov["engine_version"]
    assert prov.get("formula_version") == p["score"]["provenance"]["score_formula"]
    assert prov.get("observer_height_m") == 2.0
    assert prov.get("step_min") == 30
    assert "data_version" in prov and (prov["data_version"] is None or isinstance(prov["data_version"], str))
    appr = prov.get("approximations")
    assert isinstance(appr, list) and all(isinstance(a, str) for a in appr)
    assert "climatology_not_forecast" in appr and "mask_interval_bounds_pessimistic" in appr
    eff = prov.get("effective_needs")
    assert isinstance(eff, dict) and eff.get("max_night_h") == 30
    for k, v in eff.items():  # effective needs equal the requirements actually used
        assert p["needs"].get(k) == v, (k, v, p["needs"].get(k))
    assert "fill" in prov
    assert prov["fill"] is None or isinstance(prov["fill"], dict)


def test_provenance_mask_block(monkeypatch) -> None:
    _patch_hazards(monkeypatch, None)
    p = _ok(_site(lat="-89.46316", lon="222.51045"))
    m = (p.get("provenance") or {}).get("mask")
    assert isinstance(m, dict), f"provenance.mask missing: {m!r}"
    assert {"requested_lat", "requested_lon", "lat", "lon", "distance_m", "source"} <= m.keys(), m
    assert m["requested_lat"] == pytest.approx(-89.46316) and m["requested_lon"] == pytest.approx(222.51045)
    assert m["source"] in ("own_dem", "cap_cell"), m["source"]
    assert isinstance(m["distance_m"], (int, float)) and m["distance_m"] >= 0


# ---------------------------------------------------------------- 4. coverage / validation (D-cd33)

@pytest.mark.parametrize("lat", ["90", "89.5", "0", "-59.9", "-30"])
def test_site_rejects_lat_outside_south_polar_coverage(lat: str) -> None:
    r = _site(lat=lat, lon="0")
    assert r.status_code == 422, f"{r.status_code}: {r.text[:200]}"
    t = _text(r)
    assert "lat" in t and "coverage" in t, t


@pytest.mark.parametrize("lat", ["90", "0", "-59.9"])
def test_deep_search_rejects_lat_outside_coverage(lat: str) -> None:
    body = {
        "lat_min": -89.6, "lat_max": float(lat), "lon_min": 222.0, "lon_max": 223.0,
        "start": "2027-01-01T00:00:00Z", "end": "2027-01-03T00:00:00Z", "window_hours": 24,
    }
    if float(lat) < -89.6:
        body["lat_min"] = float(lat) - 1
    r = client.post("/deep-search", json=body)
    assert r.status_code == 422, f"{r.status_code}: {r.text[:200]}"
    t = _text(r)
    assert "lat" in t and "coverage" in t, t


def test_local_search_requires_step_h_1() -> None:
    r = _site(local_search="1", step_h="2")
    assert r.status_code == 422, f"{r.status_code}: {r.text[:200]}"
    assert "step_h" in _text(r)


# ---------------------------------------------------------------- 5. store status (D-62d3)

def test_store_status_endpoint(monkeypatch) -> None:
    import moonpark.horizon.remote as remote

    monkeypatch.setattr(
        remote, "store_status", lambda: {"version": "2027.1", "min_app_version": "0.3.0", "reachable": True}
    )
    r = client.get("/store-status")
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    j = r.json()
    assert j.get("version") == "2027.1" and j.get("min_app_version") == "0.3.0" and j.get("reachable") is True, j
    assert isinstance(j.get("engine_version"), str) and j["engine_version"], j


def test_store_status_unreachable(monkeypatch) -> None:
    import moonpark.horizon.remote as remote

    monkeypatch.setattr(remote, "store_status", lambda: {"version": None, "min_app_version": None, "reachable": False})
    r = client.get("/store-status")
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    j = r.json()
    assert j.get("reachable") is False and j.get("version") is None and "engine_version" in j, j


# ---------------------------------------------------------------- 6. mock payload

def test_mock_series_matches_visibility_bounds() -> None:
    from moonpark.visibility import total_lit_h

    p = _ok(client.get("/site?mock=1"))
    s = p["series"]
    for k in ("longest_night_h_lower", "longest_no_earth_h_lower", "longest_lit_h_upper"):
        assert k in s, f"mock series lacks {k}"
    if "longest_night_h_lower" in s:
        assert s["longest_night_h_lower"] <= s["longest_night_h"]
        assert s["longest_no_earth_h_lower"] <= s["longest_no_earth_h"]
        assert s["longest_lit_h_upper"] >= s["longest_lit_h"]
    n = p["needs"]
    sun = np.asarray(s["sun_fraction"])
    earth = np.asarray(s["earth_fraction"])
    assert s["hours_sun_above_threshold"] == total_lit_h(sun, n["sun_lit_threshold"], 1.0)
    assert s["hours_earth_above_threshold"] == total_lit_h(earth, n["earth_lit_threshold"], 1.0)
    assert s.get("step_min") == 60


def test_mock_has_same_top_level_extras_as_real(monkeypatch) -> None:
    _patch_hazards(monkeypatch, None)
    mock = _ok(client.get("/site?mock=1"))
    real = _ok(_site())
    for k in ("hazards_status", "warnings", "provenance"):
        assert k in real, f"real payload lacks {k}"
        assert k in mock, f"mock payload lacks {k}"
    assert mock.get("warnings") == []
    assert (mock.get("hazards_status") or {}).get("status") == "disabled"
    assert isinstance(mock.get("provenance"), dict)


# ---------------------------------------------------------------- 7. local search uses user requirements (D-75f1)

def test_local_search_candidates_use_same_effective_needs(monkeypatch) -> None:
    import moonpark.planner_payload as pp
    import moonpark.search.local as local_mod
    from moonpark.providers import Site

    _patch_hazards(monkeypatch, None)
    captured: dict[str, Any] = {}
    sub_calls: list[dict] = []
    real_build = pp.build_planner_payload

    def fake_local_search(origin, start, hours, needs, *, evaluate, **kw):
        captured["needs"] = dict(needs)
        captured["hours"] = hours
        evaluate(origin, np.datetime64(start, "s"), 2)
        return {"pick": None, "leaderboard": []}

    def spy_build(*args, **kwargs):
        if not kwargs.get("local_search"):
            sub_calls.append(kwargs)
        return real_build(*args, **kwargs)

    monkeypatch.setattr(local_mod, "local_search", fake_local_search)
    monkeypatch.setattr(pp, "build_planner_payload", spy_build)

    site = Site(lat_deg=-89.46316, lon_deg=222.51045, observer_height_m=2.0)
    times = pp.parse_time_window("2027-01-01T00:00:00Z", "2027-01-01T06:00:00Z", step_min=60)
    needs = {
        "max_night_h": 30, "max_no_earth_h": 20, "require_both": True, "min_continuous_lit_h": 2,
        "min_total_lit_h": 3.0, "max_temperature_k": 300.0, "min_temperature_k": 100.0,
        "min_soil_resistance": 1.0, "battery_wh": 100.0, "array_w": 10.0, "dark_w": 1.0,
    }
    payload = real_build(
        site, times, needs=needs, sun_lit_percent=10, earth_lit_percent=20, bridge_h=3,
        hazards_enabled=True, local_search=True, step_min=60,
    )
    assert "needs" in captured, "local_search was not called"
    sub = [c for c in sub_calls if c is not None]
    assert sub, "evaluate() did not build a payload"
    c = sub[-1]
    assert c.get("needs") == needs, c.get("needs")
    assert c.get("hazards_enabled") is True
    assert (c.get("sun_lit_percent"), c.get("earth_lit_percent"), c.get("bridge_h")) == (10, 20, 3)
    assert c.get("step_min") == 60
    # the needs handed to local_search are the effective needs of the main analysis
    eff = (payload.get("provenance") or {}).get("effective_needs")
    assert isinstance(eff, dict), "provenance.effective_needs missing"
    for k, v in captured["needs"].items():
        assert eff.get(k) == v, (k, v, eff.get(k))
    for k in ("min_total_lit_h", "max_temperature_k", "min_temperature_k", "min_soil_resistance", "battery_wh"):
        assert k in captured["needs"] or k in eff, f"{k} lost for local search"


def test_default_zero_soil_limit_with_soil_unavailable_is_not_a_gap(monkeypatch) -> None:
    # Review finding: min_soil_resistance=0 constrains nothing, so missing slope data must not warn,
    # list it as not evaluated, or star the result.
    _patch_hazards(monkeypatch, {"soil_resistance": "no slope data"})
    p = _ok(_site())
    assert (p["needs"].get("not_evaluated") or []) == [], p["needs"].get("not_evaluated")
    assert not (p.get("warnings") or []), p.get("warnings")
    assert not p["score"].get("hazard_gap_star")
