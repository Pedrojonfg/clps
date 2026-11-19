"""Measure where GET /site and POST /deep-search start to fail or become unreasonable (D-20261118-pj-cd33).

Each measurement runs in its own subprocess (fresh interpreter, cold caches, like a first request on a
client machine) through FastAPI's TestClient, with the usage limits lifted so sizes beyond them can be
measured. Client conditions: no own-DEM masks (mask_store.load_cached_mask and mask_schedule_for_site
return None), so /site snaps to the 1 km cap mask, as the deep search does.

The parent polls the child's RSS and kills it above --rss-cap-mb or after --timeout-s; it never runs
two measurements at once. Results are appended as JSON lines to --out (one object per run).

Usage:
    python scripts/bench_limits.py site  --out RESULTS.jsonl [--days 1,7,31] [--steps 60,10] [--repeat 3]
    python scripts/bench_limits.py deep  --out RESULTS.jsonl [--cells 3,100,1000] ...
    python scripts/bench_limits.py child '<json spec>'      # internal: one measurement
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
START = datetime(2027, 1, 1, tzinfo=timezone.utc)
ENERGY = {"battery_wh": 1000.0, "array_w": 100.0, "dark_w": 20.0}
# Rectangle centre for deep-search sizes: away from the pole so a lat/lon box is a plain stereo box.
CENTRE_LAT, CENTRE_LON = -87.5, 222.0


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- child


def _lift_limits() -> None:
    import moonpark.horizon.mask_store as ms
    import moonpark.planner_payload as pp

    ms.load_cached_mask = lambda site: None
    ms.mask_schedule_for_site = lambda *a, **k: None
    pp.MAX_WINDOW_H = None
    import moonpark.api.app as app_mod

    for name in ("SITE_MAX_WINDOW_H", "SITE_MAX_SAMPLES", "LOCAL_SEARCH_MAX_WINDOW_H", "HAZARD_MAX_SPAN_H",
                 "DEEP_MAX_CELLS", "DEEP_MAX_EVALUATIONS", "DEEP_MAX_SKY_SAMPLES"):
        if hasattr(app_mod, name):
            setattr(app_mod, name, None)


def child(spec: dict) -> dict:
    import resource

    t0 = time.perf_counter()
    _lift_limits()
    from fastapi.testclient import TestClient

    from moonpark.api.app import app

    client = TestClient(app)
    rss_import_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    t_import = time.perf_counter() - t0
    t1 = time.perf_counter()
    if spec["kind"] == "site":
        resp = client.get("/site", params=spec["params"])
    else:
        resp = client.post("/deep-search", json=spec["body"])
    wall = time.perf_counter() - t1
    out: dict = {
        "status": resp.status_code,
        "wall_s": round(wall, 3),
        "import_s": round(t_import, 3),
        "bytes": len(resp.content),
        "rss_import_mb": round(rss_import_mb, 1),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
    }
    if resp.status_code != 200:
        out["error"] = resp.text[:500]
    else:
        js = resp.json()
        if spec["kind"] == "deep":
            out.update({k: js.get(k) for k in ("n_sites", "n_window_starts", "rows_evaluated", "state",
                                                  "dropped_cells", "n_starts", "runtime_s")})
            out["export_rows"] = len(js.get("export_rows") or [])
        else:
            out["n_samples"] = len(js.get("sky") or js.get("times_utc") or [])
    return out


# ---------------------------------------------------------------- parent


def _rss_mb(pid: int) -> float:
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        pass
    return 0.0


def run_one(spec: dict, timeout_s: float, rss_cap_mb: float) -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "child", json.dumps(spec)]
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    peak_seen = 0.0
    killed = None
    while p.poll() is None:
        peak_seen = max(peak_seen, _rss_mb(p.pid))
        el = time.perf_counter() - t0
        if el > timeout_s:
            killed = "timeout"
        elif peak_seen > rss_cap_mb:
            killed = "rss_cap"
        if killed:
            p.kill()
            break
        time.sleep(0.2)
    stdout, stderr = p.communicate()
    res: dict = {"spec": spec, "elapsed_total_s": round(time.perf_counter() - t0, 2),
                 "peak_rss_polled_mb": round(peak_seen, 1)}
    if killed:
        res.update({"status": None, "killed": killed})
        return res
    try:
        res.update(json.loads(stdout.strip().splitlines()[-1]))
    except (ValueError, IndexError):
        res.update({"status": None, "error": "child crashed rc=%s: %s" % (p.returncode, stderr[-800:])})
    return res


def site_spec(days: float, step_min: int, hazards: bool, energy: bool, local: bool = False) -> dict:
    end = START + timedelta(hours=days * 24) - timedelta(hours=1)
    params = {"start": _iso(START), "end": _iso(end), "step_min": step_min,
              "hazards_enabled": str(hazards).lower()}
    if energy:
        params.update(ENERGY)
    if local:
        params["local_search"] = 1
    return {"kind": "site", "params": params,
            "label": {"days": days, "hours": int(days * 24), "step_min": step_min,
                      "hazards": hazards, "energy": energy, "local_search": local}}


def rect_for_cells(target: int) -> tuple[dict, int]:
    """Lat/lon box around (CENTRE_LAT, CENTRE_LON) whose cap-cell count is close to ``target``."""
    import math

    from moonpark.horizon.cap_index import sites_in_latlon_rect

    def box(d: float) -> dict:
        dl = d / math.cos(math.radians(abs(CENTRE_LAT)))
        return {"lat_min": CENTRE_LAT - d, "lat_max": CENTRE_LAT + d,
                "lon_min": CENTRE_LON - dl, "lon_max": CENTRE_LON + dl}

    lo, hi = 0.0, 2.4
    if target > 20000:
        # Large regions: a sector lat -89.9..-80, lon 0..W (a box containing the pole is not usable: the
        # corner-based stereo AABB in sites_in_latlon_rect collapses there). W = 180 holds about half the cap.
        def box(w: float) -> dict:  # noqa: F811
            return {"lat_min": -89.9, "lat_max": -80.0, "lon_min": 0.0, "lon_max": w}

        lo, hi = 0.0, 180.0
    best = (box(hi), len(sites_in_latlon_rect(**box(hi))))
    for _ in range(40):
        mid = (lo + hi) / 2
        n = len(sites_in_latlon_rect(**box(mid)))
        if abs(n - target) < abs(best[1] - target) or (n == target):
            best = (box(mid), n)
        if n == target:
            break
        if n < target:
            lo = mid
        else:
            hi = mid
    return {k: round(v, 6) for k, v in best[0].items()}, best[1]


def deep_spec(rect: dict, n_cells: int, window_h: int, span_days: float, mode: str, step_min: int,
              hazards: bool) -> dict:
    # span_days = number of window starts / 24 (one start per hour): end = start + span + window
    n_starts = int(round(span_days * 24))
    end = START + timedelta(hours=n_starts + window_h - 1)
    body = {**rect, "start": _iso(START), "end": _iso(end), "window_hours": window_h, "mode": mode,
            "step_min": step_min, "hazards_enabled": hazards}
    return {"kind": "deep", "body": body,
            "label": {"cells": n_cells, "window_h": window_h, "span_days": span_days, "n_starts": n_starts,
                      "mode": mode, "step_min": step_min, "hazards": hazards}}


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "child":
        print(json.dumps(child(json.loads(sys.argv[2]))))
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["site", "deep", "rects"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", default="1,7,31,62,124")
    ap.add_argument("--steps", default="60,10")
    ap.add_argument("--hazards", default="0,1")
    ap.add_argument("--energy", default="0,1")
    ap.add_argument("--local", default="0", help="site: local_search values to run (0,1)")
    ap.add_argument("--cells", default="3,100,1000,10000")
    ap.add_argument("--windows", default="24,168")
    ap.add_argument("--spans", default="1,14")
    ap.add_argument("--modes", default="total_coverage,optimized")
    ap.add_argument("--plan", default="", help="deep: explicit runs, see main()")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--timeout-s", type=float, default=1200)
    ap.add_argument("--rss-cap-mb", type=float, default=3584)
    a = ap.parse_args()
    ints = lambda s: [int(x) for x in s.split(",") if x]  # noqa: E731
    floats = lambda s: [float(x) for x in s.split(",") if x]  # noqa: E731
    out = Path(a.out)

    def record(res: dict) -> None:
        with out.open("a") as f:
            f.write(json.dumps(res) + "\n")
        lab = res["spec"]["label"]
        print(json.dumps({**lab, **{k: res.get(k) for k in (
            "status", "killed", "wall_s", "peak_rss_mb", "peak_rss_polled_mb", "bytes", "error",
            "rows_evaluated", "n_sites")}})[:600], flush=True)

    if a.what == "rects":
        for n in ints(a.cells):
            print(n, rect_for_cells(n))
        return
    if a.what == "site":
        # grow days within each (step, hazards, energy) combination; stop growing on failure
        for step in ints(a.steps):
            for hz in ints(a.hazards):
                for en in ints(a.energy):
                    for loc in ints(a.local):
                        for d in floats(a.days):
                            failed = False
                            for _ in range(a.repeat):
                                res = run_one(site_spec(d, step, bool(hz), bool(en), bool(loc)),
                                              a.timeout_s, a.rss_cap_mb)
                                record(res)
                                if res.get("status") != 200:
                                    failed = True
                                    break
                            if failed:
                                break
        return
    if a.plan:  # explicit list "cells:window_h:span_days:mode:step_min:hazards[:start_n]" separated by spaces
        rects: dict = {}
        for item in a.plan.split():
            parts = item.split(":")
            n, wh, span, mode, step, hz = int(parts[0]), int(parts[1]), float(parts[2]), parts[3], int(parts[4]), \
                bool(int(parts[5]))
            if n not in rects:
                rects[n] = rect_for_cells(n)
            rect, got = rects[n]
            spec = deep_spec(rect, got, wh, span, mode, step, hz)
            if len(parts) > 6:
                spec["body"]["start_n"] = int(parts[6])
                spec["label"]["start_n"] = int(parts[6])
            for _ in range(a.repeat):
                res = run_one(spec, a.timeout_s, a.rss_cap_mb)
                record(res)
                if res.get("status") != 200:
                    break
        return
    rects = {n: rect_for_cells(n) for n in ints(a.cells)}
    for mode in a.modes.split(","):
        for step in ints(a.steps):
            for hz in ints(a.hazards):
                for wh in ints(a.windows):
                    for span in floats(a.spans):
                        for n in ints(a.cells):
                            rect, got = rects[n]
                            failed = False
                            for _ in range(a.repeat):
                                res = run_one(deep_spec(rect, got, wh, span, mode, step, bool(hz)),
                                              a.timeout_s, a.rss_cap_mb)
                                record(res)
                                if res.get("status") != 200:
                                    failed = True
                                    break
                            if failed:
                                break  # stop growing cells for this combination


if __name__ == "__main__":
    main()
