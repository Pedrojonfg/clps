"""Regression tests for the reviewer findings on feat/audit-decisions-impl.

1 zero minimum limit = not requested; 2 pessimistic bridge_h (D-9413); 3 deep-search resume fingerprint and
checkpoint validation; 4 store version format, short store-status timeout, keep previous version dir;
5 local search drops windows with unevaluated limits (D-75f1 / D-b3dc); 7 provenance cap_version.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import urllib.error

import numpy as np
import pytest
from fastapi.testclient import TestClient

from moonpark.api.app import app
from moonpark.providers import HorizonMask, Site, SkySample

client = TestClient(app, raise_server_exceptions=False)


def _data_available() -> bool:
    try:
        from moonpark.horizon.cap_index import cap_index_available
        from moonpark.planner_payload import kernels_available

        return bool(kernels_available() and cap_index_available())
    except Exception:
        return False


needs_data = pytest.mark.skipif(not _data_available(), reason="SPICE kernels / cap index not on disk")


class FakeHazards:
    """MoonHazards-shaped result with the given fields reported unavailable."""

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
    import moonpark.hazards.moon as hm

    monkeypatch.setattr(hz, "default_moon_hazards", lambda *a, **k: FakeHazards(unavailable))
    monkeypatch.setattr(hm, "default_moon_hazards", lambda *a, **k: FakeHazards(unavailable), raising=False)


@pytest.fixture()
def client_masks(monkeypatch):
    """No own-DEM masks: /site snaps to the 1 km cap cell (fast and machine independent)."""
    import moonpark.horizon.mask_store as ms

    monkeypatch.setattr(ms, "load_cached_mask", lambda site: None)
    monkeypatch.setattr(ms, "mask_schedule_for_site", lambda *a, **k: None)


WINDOW = {"start": "2027-01-01T00:00:00Z", "end": "2027-01-01T06:00:00Z"}
SOIL_GONE = {"soil_resistance": "slope raster missing"}


# =============================================================== 1. a minimum limit <= 0 is not requested


def test_hazard_status_zero_minimum_is_not_requested() -> None:
    from moonpark.planner_payload import hazard_status

    raw = {"unavailable": dict(SOIL_GONE)}
    status, not_eval, warnings = hazard_status(True, raw, {"min_soil_resistance": 0.0})
    assert not_eval == [] and warnings == []
    assert status["status"] == "partial"  # the data gap itself is still reported
    _, not_eval, warnings = hazard_status(True, raw, {"min_soil_resistance": -1.0})
    assert not_eval == [] and warnings == []
    _, not_eval, warnings = hazard_status(True, raw, {"min_soil_resistance": 10.0})
    assert not_eval == ["min_soil_resistance"] and warnings


def test_gap_star_zero_minimum_is_not_requested() -> None:
    from moonpark.score import _hazard_gap_star, score

    series = {"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True}
    base = {"max_night_h": 50, "max_no_earth_h": 20}
    assert _hazard_gap_star({}, {**base, "min_soil_resistance": 0.0}) is False
    assert _hazard_gap_star({}, {**base, "min_temperature_k": 0.0}) is False
    assert "hazard_gap_star" not in score(series, {}, {**base, "min_soil_resistance": 0.0})
    assert score(series, {}, {**base, "min_soil_resistance": 10.0}).get("hazard_gap_star") is True


def test_app_requested_shares_the_rule() -> None:
    from moonpark.api.app import _requested

    assert not _requested("min_soil_resistance", 0.0)
    assert not _requested("min_soil_resistance", -2.0)
    assert _requested("min_soil_resistance", 10.0)
    assert _requested("max_temperature_k", 0.0)  # a maximum of 0 does constrain


@needs_data
def test_site_zero_soil_limit_with_soil_missing_does_not_warn(monkeypatch, client_masks) -> None:
    _patch_hazards(monkeypatch, SOIL_GONE)
    r = client.get("/site", params={**WINDOW, "min_soil_resistance": "0"})
    assert r.status_code == 200, r.text[:300]
    p = r.json()
    assert p["needs"]["not_evaluated"] == []
    assert p["warnings"] == []
    assert not p["score"].get("hazard_gap_star")


@needs_data
def test_site_positive_soil_limit_with_soil_missing_is_not_evaluated(monkeypatch, client_masks) -> None:
    _patch_hazards(monkeypatch, SOIL_GONE)
    r = client.get("/site", params={**WINDOW, "min_soil_resistance": "10"})
    assert r.status_code == 200, r.text[:300]
    p = r.json()
    assert p["needs"]["not_evaluated"] == ["min_soil_resistance"]
    assert p["score"].get("hazard_gap_star") is True


RECT = {"lat_min": -89.52, "lat_max": -89.40, "lon_min": 222.0, "lon_max": 223.0}
DEEP = {**RECT, "start": "2027-01-01T00:00:00Z", "end": "2027-01-02T00:00:00Z", "window_hours": 24,
        "mode": "total_coverage"}


@needs_data
def test_deep_search_zero_soil_limit_drops_nothing(monkeypatch, client_masks) -> None:
    _patch_hazards(monkeypatch, SOIL_GONE)
    r = client.post("/deep-search", json={**DEEP, "hazards_enabled": True, "min_soil_resistance": 0})
    assert r.status_code == 200, r.text[:300]
    p = r.json()
    assert p["dropped_cells"] == 0
    assert len(p["export_rows"]) == 3


@needs_data
def test_deep_search_positive_soil_limit_still_drops(monkeypatch, client_masks) -> None:
    _patch_hazards(monkeypatch, SOIL_GONE)
    r = client.post("/deep-search", json={**DEEP, "hazards_enabled": True, "min_soil_resistance": 10})
    assert r.status_code == 200, r.text[:300]
    assert r.json()["dropped_cells"] == 3


# =============================================================== 2. pessimistic bridge_h (D-9413)


def test_bridge_uses_upper_bound_of_gap() -> None:
    from moonpark.visibility import longest_lit_h

    f = np.array([1.0, 1.0, 0.0, 1.0, 1.0])  # one dark hourly sample: the gap may last up to 2 h
    assert longest_lit_h(f, 0.0, bridge_h=1) == 1
    assert longest_lit_h(f, 0.0, bridge_h=2) == 4
    f2 = np.array([1.0, 1.0, 0.0, 0.0, 1.0, 1.0])  # up to 3 h
    assert longest_lit_h(f2, 0.0, bridge_h=2) == 1
    assert longest_lit_h(f2, 0.0, bridge_h=3) == 5


def test_bridge_never_at_window_edge() -> None:
    from moonpark.visibility import longest_lit_h

    assert longest_lit_h(np.array([0.0, 1.0, 1.0, 1.0]), 0.0, bridge_h=10) == 2
    assert longest_lit_h(np.array([1.0, 1.0, 1.0, 0.0]), 0.0, bridge_h=10) == 2


def _flat() -> HorizonMask:
    return HorizonMask(
        elevation_deg=np.zeros(720, dtype=np.float32), x_m=0.0, y_m=0.0, lat=-89.46316, lon=222.51045,
        h0_m=0.0, observer_height_m=2.0, schedule_version="t", dem_ids=(),
    )


def _gap_sky(step_min: int, centre_h: float, half_gap_h: float = 0.75) -> list[SkySample]:
    t0 = np.datetime64("2027-06-01T00:00:00")
    n = 24 * 60 // step_min + 1
    h = np.arange(n) * step_min / 60.0
    el = 5.0 * ((h - centre_h) ** 2 - half_gap_h**2)  # smooth; dark for 2*half_gap_h hours around centre_h
    return [SkySample(t0 + np.timedelta64(int(i * step_min), "m"), 0.0, float(e), 0.2665, 0.0, 10.0, 0.5)
            for i, e in enumerate(el)]


@pytest.mark.parametrize("centre", [11.0, 11.2, 11.5, 11.75, 12.0, 12.1, 12.4])
def test_coarse_bridge_never_longer_than_fine(centre: float) -> None:
    from moonpark.visibility import series

    coarse = series(_gap_sky(60, centre), _flat(), bridge_h=1, step_min=60)
    fine = series(_gap_sky(10, centre), _flat(), bridge_h=1, step_min=10)
    assert coarse["longest_lit_h"] <= fine["longest_lit_h"] + 1e-9, (coarse["longest_lit_h"], fine["longest_lit_h"])


# =============================================================== 3. deep-search resume fingerprint / checkpoint


def _grid():
    sites = [Site(lat_deg=-89.0 - 0.01 * i, lon_deg=10.0, observer_height_m=2.0) for i in range(3)]
    xy = [(1000.0 * i, 0.0) for i in range(3)]
    starts = np.datetime64("2027-01-01T00:00:00", "s") + np.arange(3) * np.timedelta64(1, "h")
    return sites, xy, starts


def _ev(site, start, hours):
    return {"series": {"longest_night_h": 10 + abs(site.lat_deg), "longest_no_earth_h": 1, "any_both": True},
            "hazards": {}}


NEEDS = {"max_night_h": 200, "max_no_earth_h": 20}


def _stopped_checkpoint(extra: dict) -> dict:
    from moonpark.search.deep import deep_search

    sites, xy, starts = _grid()
    calls = []

    def stop():
        calls.append(1)
        return len(calls) > 2

    res = deep_search(sites, starts, 24, NEEDS, evaluate=_ev, mode="total_coverage", site_xy=xy,
                      should_stop=stop, fingerprint_extra=extra)
    assert res["state"] == "stopped"
    return res["checkpoint"]


def _resume(cp, extra):
    from moonpark.search.deep import deep_search

    sites, xy, starts = _grid()
    return deep_search(sites, starts, 24, NEEDS, evaluate=_ev, mode="total_coverage", site_xy=xy,
                       resume=cp, fingerprint_extra=extra)


def test_fingerprint_extra_round_trips_and_mismatch_is_rejected() -> None:
    extra = {"requirements": {"sun_lit_percent": 10.0, "bridge_h": 5}, "rect": [1, 2, 3, 4]}
    cp = json.loads(json.dumps(_stopped_checkpoint(extra)))  # what the client sends back
    assert _resume(cp, extra)["state"] == "complete"
    with pytest.raises(ValueError):
        _resume(cp, {**extra, "requirements": {"sun_lit_percent": 20.0, "bridge_h": 5}})


@pytest.mark.parametrize(
    "mutate",
    [
        lambda cp: cp.update(rows=[5]),
        lambda cp: cp.update(rows=[[0, 0, [True]]]),
        lambda cp: cp.update(rows=[[99, 0, None]]),
        lambda cp: cp.update(rows=[[0, 99, [True, 1.0, 1.0, False]]]),
        lambda cp: cp.update(rows=[[0, 0, [True, "x", 1.0, False]]]),
        lambda cp: cp.update(rows={"a": 1}),
        lambda cp: cp.update(n_starts=[1]),
        lambda cp: cp.update(n_starts=-3),
        lambda cp: cp.pop("fingerprint"),
    ],
)
def test_malformed_checkpoint_is_value_error(mutate) -> None:
    cp = json.loads(json.dumps(_stopped_checkpoint({"k": 1})))
    mutate(cp)
    with pytest.raises(ValueError):
        _resume(cp, {"k": 1})


@pytest.fixture()
def first_call_stops(monkeypatch):
    """The first /deep-search call stops at once (returns a checkpoint); later calls run normally."""
    from moonpark.search import deep as deep_mod

    real = deep_mod.deep_search
    state = {"n": 0}

    def wrapper(*a, **kw):
        state["n"] += 1
        if state["n"] == 1:
            kw["should_stop"] = lambda: True
        return real(*a, **kw)

    monkeypatch.setattr(deep_mod, "deep_search", wrapper)


def _checkpoint_from_api(body: dict) -> dict:
    r = client.post("/deep-search", json=body)
    assert r.status_code == 200, r.text[:300]
    p = r.json()
    assert p["state"] == "stopped" and isinstance(p["checkpoint"], dict)
    return p["checkpoint"]


BASE_BODY = {**DEEP, "hazards_enabled": False}


@needs_data
@pytest.mark.parametrize(
    "change",
    [
        {"sun_lit_percent": 37.0},
        {"lon_max": 222.9},  # same cells, different rectangle
        {"step_min": 10},
        {"bridge_h": 2},
        {"hazards_enabled": True},
    ],
)
def test_api_resume_with_changed_request_is_400(first_call_stops, client_masks, monkeypatch, change) -> None:
    _patch_hazards(monkeypatch, None)
    cp = _checkpoint_from_api(BASE_BODY)
    r = client.post("/deep-search", json={**BASE_BODY, **change, "resume": cp})
    assert r.status_code == 400, r.text[:300]


@needs_data
def test_api_resume_same_request_completes(first_call_stops, client_masks) -> None:
    cp = _checkpoint_from_api(BASE_BODY)
    r = client.post("/deep-search", json={**BASE_BODY, "resume": cp})
    assert r.status_code == 200, r.text[:300]
    assert r.json()["state"] == "complete"


@needs_data
@pytest.mark.parametrize("rows", [[5], [[0, 0, [True]]], [[99, 0, [True, 1.0, 1.0, False]]], "x"])
def test_api_malformed_checkpoint_rows_is_400(first_call_stops, client_masks, rows) -> None:
    cp = _checkpoint_from_api(BASE_BODY)
    cp["rows"] = rows
    r = client.post("/deep-search", json={**BASE_BODY, "resume": cp})
    assert r.status_code == 400, r.text[:300]


# =============================================================== 4. remote store


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


STORE = "http://store.test/data"


class FakeStore:
    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.requests: list[tuple[str, float]] = []
        self.offline = False

    def put(self, url, data):
        self.files[url] = data if isinstance(data, bytes) else json.dumps(data).encode()

    def publish(self, version, blobs):
        for rel, b in blobs.items():
            self.put(f"{STORE}/{version}/{rel}", b)
        files = {r: {"size": len(b), "sha256": hashlib.sha256(b).hexdigest()} for r, b in blobs.items()}
        self.put(f"{STORE}/{version}/manifest.json", {"schema": 1, "version": version, "files": files})
        self.put(f"{STORE}/latest.json", {"version": version, "min_app_version": ""})

    def get(self, url, timeout=0):
        self.requests.append((url, timeout))
        if self.offline:
            raise urllib.error.URLError("offline")
        if url not in self.files:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return _Resp(self.files[url])


@pytest.fixture()
def fake(monkeypatch):
    from moonpark.horizon import remote

    s = FakeStore()
    monkeypatch.setattr(remote, "_get", s.get)
    return s


@pytest.mark.parametrize("bad", ["x\\..\\..\\evil", "D:evil", "\\\\srv\\share", "../x", "v1", "ABCDEF123456",
                                 "abc123def4567", ""])
def test_bad_store_version_is_rejected(fake, tmp_path, bad) -> None:
    from moonpark.horizon.remote import RemoteCap

    fake.put(f"{STORE}/latest.json", {"version": bad, "min_app_version": ""})
    fake.put(f"{STORE}/{bad}/manifest.json", {"schema": 1, "version": bad, "files": {}})
    cache = tmp_path / "cache"
    c = RemoteCap(STORE, cache)
    with pytest.raises(OSError):
        c.manifest  # nothing cached: unreachable
    assert c.version is None
    assert not any(u.endswith("/manifest.json") for u, _ in fake.requests), "pointer must be rejected first"
    assert not cache.exists() or [p.name for p in cache.iterdir()] == []
    assert sorted(p.name for p in tmp_path.iterdir()) in ([], ["cache"])


def test_good_store_version_is_accepted(fake, tmp_path) -> None:
    from moonpark.horizon.remote import RemoteCap

    fake.publish("0123456789ab", {"d/f.bin": b"Z" * 10})
    c = RemoteCap(STORE, tmp_path / "cache")
    assert c.get("d/f.bin").read_bytes() == b"Z" * 10
    assert c.version == "0123456789ab"


def test_store_status_uses_short_timeout(fake, tmp_path, monkeypatch) -> None:
    from moonpark.horizon import remote

    monkeypatch.setenv("LUNAR_STORE_URL", "http://store.test")
    monkeypatch.setenv("LUNAR_CACHE", str(tmp_path / "cache"))
    monkeypatch.setattr(remote, "_GROUPS", {})
    fake.publish("0123456789ab", {"d/f.bin": b"Z" * 10})
    st = remote.store_status()
    assert st["version"] == "0123456789ab" and st["reachable"] is True
    assert fake.requests and all(t <= 2.5 for _, t in fake.requests), fake.requests


def test_failed_short_status_probe_does_not_pin_the_group_offline(fake, tmp_path, monkeypatch) -> None:
    from moonpark.horizon import remote

    monkeypatch.setenv("LUNAR_STORE_URL", "http://store.test")
    monkeypatch.setenv("LUNAR_CACHE", str(tmp_path / "cache"))
    monkeypatch.setattr(remote, "_GROUPS", {})
    fake.publish("0123456789ab", {"d/f.bin": b"Z" * 10})
    fake.offline = True
    assert remote.store_status()["reachable"] is False
    fake.offline = False
    g = remote.group("data")
    assert g.get("d/f.bin").read_bytes() == b"Z" * 10  # the normal path retries with its own timeout
    assert g.reachable is True


def test_other_paths_keep_manifest_timeout(fake, tmp_path) -> None:
    from moonpark.horizon import remote

    fake.publish("0123456789ab", {"d/f.bin": b"Z" * 10})
    remote.RemoteCap(STORE, tmp_path / "cache").manifest
    assert all(t == remote.MANIFEST_TIMEOUT_S for _, t in fake.requests), fake.requests


def test_prune_keeps_current_and_previous_version(fake, tmp_path) -> None:
    from moonpark.horizon.remote import RemoteCap

    cache = tmp_path / "cache"
    for i, v in enumerate(("aaaaaaaaaaa1", "aaaaaaaaaaa2", "aaaaaaaaaaa3")):
        fake.publish(v, {"d/f.bin": bytes([65 + i]) * 10})
        RemoteCap(STORE, cache).get("d/f.bin")
        m = cache / v / "manifest.json"
        os.utime(m, (1_000_000 + i * 100, 1_000_000 + i * 100))  # deterministic order
    assert not (cache / "aaaaaaaaaaa1").exists()
    assert (cache / "aaaaaaaaaaa2" / "d" / "f.bin").is_file()  # previous: still usable offline
    assert (cache / "aaaaaaaaaaa3" / "d" / "f.bin").is_file()
    fake.offline = True
    c = RemoteCap(STORE, cache)
    assert c.get("d/f.bin").read_bytes() == b"C" * 10 and c.version == "aaaaaaaaaaa3"


# =============================================================== 5. local search drops unevaluated windows


ORIGIN = Site(lat_deg=-89.46316, lon_deg=222.51045, observer_height_m=2.0)
A = np.datetime64("2027-01-01T06:00:00", "s")


def _ser():
    return {"longest_night_h": 1, "longest_no_earth_h": 1, "any_both": True}


def test_local_search_drops_none_and_gap_windows_and_counts() -> None:
    from moonpark.search.local import local_search

    def evaluate(site, start, hours):
        off = int((np.datetime64(start, "s") - A) / np.timedelta64(1, "h"))
        if off == 1:
            return None
        if off == 2:
            return {"series": _ser(), "hazards": {}, "hazard_gap_star": True}
        return {"series": _ser(), "hazards": {}, "hazard_gap_star": False}

    res = local_search(ORIGIN, A, 3, {"max_night_h": 50, "max_no_earth_h": 20}, evaluate=evaluate)
    assert res["dropped_windows"] == 2
    assert len(res["leaderboard"]) == 7 - 2
    assert not any(r["hazard_gap_star"] for r in res["leaderboard"])


def test_local_search_gap_from_score_is_dropped() -> None:
    from moonpark.search.local import local_search

    res = local_search(ORIGIN, A, 1, {"max_night_h": 50, "max_no_earth_h": 20, "max_temperature_k": 300.0},
                       evaluate=lambda s, t, h: {"series": _ser(), "hazards": {}})
    assert res["dropped_windows"] == 3 and res["leaderboard"] == [] and res["pick"] is None


@needs_data
def test_site_local_search_drops_windows_and_warns(monkeypatch, client_masks) -> None:
    _patch_hazards(monkeypatch, {"temperature": "no PCP data"})
    r = client.get("/site", params={"start": "2027-01-01T00:00:00Z", "end": "2027-01-01T02:00:00Z",
                                    "local_search": 1})
    assert r.status_code == 200, r.text[:300]
    p = r.json()
    # origin analysis unchanged: its own not-evaluated handling
    assert "max_temperature_k" in p["needs"]["not_evaluated"]
    ls = p["local_search"]
    assert ls["dropped_windows"] == 5  # 2 h window: starts a-2 .. a+2
    assert ls["leaderboard"] == [] and ls["pick"] is None
    codes = {w["code"]: w for w in p["warnings"]}
    assert "windows_dropped_hazard_data" in codes and "5" in codes["windows_dropped_hazard_data"]["message"]
    assert "hazard_data_unavailable" in codes


@needs_data
def test_site_local_search_no_drop_no_warning(monkeypatch, client_masks) -> None:
    _patch_hazards(monkeypatch, None)
    r = client.get("/site", params={"start": "2027-01-01T00:00:00Z", "end": "2027-01-01T02:00:00Z",
                                    "local_search": 1})
    assert r.status_code == 200, r.text[:300]
    p = r.json()
    assert p["local_search"]["dropped_windows"] == 0
    assert len(p["local_search"]["leaderboard"]) == 5
    assert "windows_dropped_hazard_data" not in {w["code"] for w in p["warnings"]}


# =============================================================== 7. provenance cap_version


def test_provenance_has_cap_version(monkeypatch) -> None:
    from moonpark import planner_payload as pp
    from moonpark.horizon import remote

    class G:
        def __init__(self, v):
            self.version = v

    groups = {"data": G("0123456789ab"), "cap_1km": G("ba9876543210")}
    monkeypatch.setattr(remote, "group", lambda name: groups.get(name))
    prov = pp.provenance(needs={}, step_min=60, observer_height_m=2.0, mask={}, fill=None, hazards_enabled=False)
    assert prov["data_version"] == "0123456789ab"
    assert prov["cap_version"] == "ba9876543210"
    monkeypatch.setattr(remote, "group", lambda name: None)
    prov = pp.provenance(needs={}, step_min=60, observer_height_m=2.0, mask={}, fill=None, hazards_enabled=False)
    assert prov["data_version"] is None and prov["cap_version"] is None
