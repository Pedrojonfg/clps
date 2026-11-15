#!/usr/bin/env python3
"""Medium deep-search megatest vs total_coverage (~1–2 h). # per D-0ee7 D-1ebf D-8a25

Compares optimized (default T_max) against total_coverage on a ~50×50 km × ~7 d
box near Site01, and optionally varies neighbour step sizes.

Does not change production defaults. Run tonight when ready:
  python3 scripts/megatest_deep_search.py
  python3 scripts/megatest_deep_search.py --quick   # smaller box smoke
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lunar_eval.ephemeris import SpiceEphemeris  # noqa: E402
from lunar_eval.horizon import polar_stereo_xy  # noqa: E402
from lunar_eval.horizon.cap_index import (  # noqa: E402
    cap_index_available,
    mask_from_cap_tile,
    sites_in_xy_rect,
)
from lunar_eval.planner_payload import kernels_available  # noqa: E402
from lunar_eval.planner_templates import TEMPLATES  # noqa: E402
from lunar_eval.search.deep import DEFAULT_TMAX_S, deep_search  # noqa: E402
from lunar_eval.site01 import SITE01  # noqa: E402
from lunar_eval.visibility import series as vis_series  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="~10×10 km × 2 d smoke")
    ap.add_argument("--template", default="clps_average")
    args = ap.parse_args()

    if not kernels_available() or not cap_index_available():
        print("kernels or cap_1km missing", file=sys.stderr)
        return 1

    # Stereo metres near the pole (lat/lon pads collapse E–W). Quick ≈10×10 km; medium ≈50×50 km.
    if args.quick:
        half_m, days = 5_000.0, 2
    else:
        half_m, days = 25_000.0, 7

    sx, sy = polar_stereo_xy(SITE01.lat_deg, SITE01.lon_deg)
    cells = sites_in_xy_rect(sx - half_m, sx + half_m, sy - half_m, sy + half_m)
    print(
        f"cells_in_rect={len(cells)} quick={args.quick} half_m={half_m} center_xy=({sx:.1f},{sy:.1f})",
        flush=True,
    )
    if len(cells) < 5:
        print("rect too empty", file=sys.stderr)
        return 1

    tmpl = TEMPLATES[args.template]
    needs = {
        "max_night_h": int(tmpl["max_night_h"]),
        "max_no_earth_h": int(tmpl["max_no_earth_h"]),
        "require_both": bool(tmpl["require_both"]),
        "min_continuous_lit_h": int(tmpl.get("min_continuous_lit_h", 0)),
    }
    sun_thr = float(tmpl["sun_lit_percent"]) / 100.0
    earth_thr = float(tmpl["earth_lit_percent"]) / 100.0
    bridge = int(tmpl["bridge_h"])
    wh = 24

    t0 = np.datetime64("2027-01-01T00:00:00")
    span = t0 + np.arange(days * 24 + wh, dtype="timedelta64[h]")
    starts = span[: days * 24]
    sites = [c[0] for c in cells]
    site_xy = [(c[1], c[2]) for c in cells]
    eph = SpiceEphemeris()
    sky_by: dict[int, list] = {}

    def evaluate(candidate, start, hours: int) -> dict:
        idx = next(
            i
            for i, s in enumerate(sites)
            if s.lat_deg == candidate.lat_deg and s.lon_deg == candidate.lon_deg
        )
        _s, _x, _y, tx, ty, row = cells[idx]
        horizon = mask_from_cap_tile(tx, ty, row)
        if idx not in sky_by:
            sky_by[idx] = eph.sky(candidate, span)
        i0 = int((np.datetime64(start, "s") - span[0]) / np.timedelta64(1, "h"))
        sky_win = sky_by[idx][i0 : i0 + int(hours) + 1]
        vis = vis_series(
            sky_win, horizon, sun_threshold=sun_thr, earth_threshold=earth_thr, bridge_h=bridge
        )
        return {"series": vis, "hazards": {}, "hazard_gap_star": False}

    summary: dict = {"template": args.template, "n_sites": len(sites), "n_starts_time": len(starts)}

    t_cov0 = time.perf_counter()
    print("running total_coverage…", flush=True)
    cov = deep_search(
        sites,
        starts,
        wh,
        needs,
        evaluate=evaluate,
        mode="total_coverage",
        site_xy=site_xy,
    )
    summary["coverage"] = {
        "runtime_s": time.perf_counter() - t_cov0,
        "rows_evaluated": cov["rows_evaluated"],
        "best_score": None if cov["best"] is None else cov["best"]["score"],
        "best_feasible": None if cov["best"] is None else cov["best"]["feasible"],
    }
    print(json.dumps(summary["coverage"], indent=2), flush=True)

    print("running optimized default…", flush=True)
    opt = deep_search(
        sites,
        starts,
        wh,
        needs,
        evaluate=evaluate,
        mode="optimized",
        start_n=None,
        tmax_s=DEFAULT_TMAX_S,
        site_xy=site_xy,
    )
    match_site = False
    match_score = False
    if cov["best"] and opt["best"]:
        match_site = (
            abs(cov["best"]["site"]["lat_deg"] - opt["best"]["site"]["lat_deg"]) < 1e-9
            and abs(cov["best"]["site"]["lon_deg"] - opt["best"]["site"]["lon_deg"]) < 1e-9
            and str(cov["best"]["window_start"]) == str(opt["best"]["window_start"])
        )
        match_score = abs(float(cov["best"]["score"]) - float(opt["best"]["score"])) < 1e-9
        summary["coverage_best"] = {
            "lat_deg": cov["best"]["site"]["lat_deg"],
            "lon_deg": cov["best"]["site"]["lon_deg"],
            "window_start": str(cov["best"]["window_start"]),
            "score": cov["best"]["score"],
        }
        summary["optimized_best"] = {
            "lat_deg": opt["best"]["site"]["lat_deg"],
            "lon_deg": opt["best"]["site"]["lon_deg"],
            "window_start": str(opt["best"]["window_start"]),
            "score": opt["best"]["score"],
        }
    summary["optimized"] = {
        "runtime_s": opt["runtime_s"],
        "rows_evaluated": opt["rows_evaluated"],
        "n_starts": opt["n_starts"],
        "best_score": None if opt["best"] is None else opt["best"]["score"],
        "matches_coverage_best": match_site,
        "matches_coverage_score": match_score,
    }
    print(json.dumps(summary["optimized"], indent=2), flush=True)
    if match_score and not match_site:
        print(
            "note: same best score, different site/window (ties expected on flat plateaus)",
            flush=True,
        )

    out = REPO / "data" / "megatest_deep_search_last.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
