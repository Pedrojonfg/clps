#!/usr/bin/env python3
"""Layer-1 risk×bonus tune sweep (pre-S6 green). # per D-6ce5 D-7c70 D-d37a D-7520

Scores Site01 sliding windows × mission templates over one week or a full year
of week chunks. Reports separate risk-order inversion rates for feasible and
infeasible pairs (same template pool), vs the 2–40% accept band. Optional
--betas reapplies companion with fixed R,B. Does not write production defaults.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from moonpark.ephemeris import SpiceEphemeris  # noqa: E402
from moonpark.horizon.mask_store import mask_for_site  # noqa: E402
from moonpark.planner_payload import parse_time_window  # noqa: E402
from moonpark.planner_templates import TEMPLATES  # noqa: E402
from moonpark.score import score  # noqa: E402
from moonpark.site01 import SITE01, real_data_available  # noqa: E402
from moonpark.visibility import series  # noqa: E402

# per D-7c70
_LOW_PCT = 2.0
_HIGH_PCT = 40.0
# per D-6ce5 provisional
_DEFAULT_BETA = 0.25  # per D-20261115-pj-48ee
_DEFAULT_MAX_UPLIFT = 0.40  # per D-20261115-pj-48ee
_MIN_PAIRS = 50
_WINDOW_H = 24


def _series_json(raw: dict) -> dict:
    out = dict(raw)
    for key in ("sun_fraction", "earth_fraction"):
        out[key] = np.asarray(raw[key], dtype=float).tolist()
    return out


def _companion(r: float, b: float, beta: float, max_uplift: float) -> float:
    """R*(1+βB) with uplift cap. # per D-7520 D-6ce5"""
    raw = r * (1.0 + beta * b)
    if r > 0 and (raw - r) / r > max_uplift:
        return r * (1.0 + max_uplift)
    return float(raw)


def _uplift(r: float, companion: float) -> float | None:
    if r <= 0:
        return None
    return (companion - r) / r


def _inversion_stats(points: list[dict]) -> tuple[int, int, float | None]:
    """Return n_pairs, n_inversions, rate_pct. # per D-7c70 D-d37a"""
    n = len(points)
    if n < 2:
        return 0, 0, None
    r = np.asarray([p["R"] for p in points], dtype=np.float64)
    c = np.asarray([p["companion"] for p in points], dtype=np.float64)
    inv = 0
    pairs = n * (n - 1) // 2
    for i in range(n - 1):
        rj = r[i + 1 :]
        cj = c[i + 1 :]
        ri = r[i]
        ci = c[i]
        inv += int(np.count_nonzero(((ri > rj) & (ci < cj)) | ((ri < rj) & (ci > cj))))
    rate = 100.0 * inv / pairs if pairs else None
    return pairs, inv, rate


def _band_label(rate: float | None) -> str:
    if rate is None:
        return "n/a"
    if rate < _LOW_PCT or rate > _HIGH_PCT:
        return "REOPEN"  # per D-7c70
    return "ACCEPT_BAND"


def _week_chunks(year: int) -> list[tuple[date, date]]:
    d0 = date(year, 1, 1)
    d1 = date(year, 12, 31)
    out: list[tuple[date, date]] = []
    d = d0
    while d <= d1:
        end = min(d + timedelta(days=6), d1)
        out.append((d, end))
        d = end + timedelta(days=1)
    return out


def _iso(d: date, hour: int = 0) -> str:
    return f"{d.isoformat()}T{hour:02d}:00:00Z"


def _pooled_rates(
    pools: dict[str, dict[str, list]], beta: float, max_uplift: float
) -> dict[str, dict]:
    tot = {"feasible": {"pairs": 0, "inv": 0}, "infeasible": {"pairs": 0, "inv": 0}}
    uplifts: list[float] = []
    cap_hits = 0
    for tid in TEMPLATES:
        for split in ("feasible", "infeasible"):
            pts = []
            for p in pools[tid][split]:
                c = _companion(p["R"], p["B"], beta, max_uplift)
                pts.append({"R": p["R"], "companion": c})
                u = _uplift(p["R"], c)
                if u is not None:
                    uplifts.append(u)
                    if u >= max_uplift - 1e-12:
                        cap_hits += 1
            pairs, inv, _ = _inversion_stats(pts)
            tot[split]["pairs"] += pairs
            tot[split]["inv"] += inv
    out: dict[str, dict] = {}
    for split in ("feasible", "infeasible"):
        pairs = tot[split]["pairs"]
        inv = tot[split]["inv"]
        rate = 100.0 * inv / pairs if pairs else None
        out[split] = {"pairs": pairs, "inv": inv, "rate": rate, "band": _band_label(rate)}
    out["uplift"] = {
        "n": len(uplifts),
        "cap_hits": cap_hits,
        "max": max(uplifts) if uplifts else None,
        "med": float(np.median(uplifts)) if uplifts else None,
    }
    return out


def _accumulate_week(
    pools: dict[str, dict[str, list]],
    sky,
    horizon,
    starts: list[int],
    win: int,
) -> int:
    scored = 0
    series_cache: dict[tuple, dict] = {}
    for tid, tmpl in TEMPLATES.items():
        sun_thr = max(0.0, min(100.0, float(tmpl["sun_lit_percent"]))) / 100.0
        earth_thr = max(0.0, min(100.0, float(tmpl["earth_lit_percent"]))) / 100.0
        bridge_h = int(tmpl["bridge_h"])
        needs = {
            "max_night_h": int(tmpl["max_night_h"]),
            "max_no_earth_h": int(tmpl["max_no_earth_h"]),
            "require_both": bool(tmpl["require_both"]),
            "min_continuous_lit_h": int(tmpl.get("min_continuous_lit_h", 0)),
        }
        for i0 in starts:
            key = (sun_thr, earth_thr, bridge_h, i0)
            if key not in series_cache:
                series_cache[key] = series(
                    sky[i0 : i0 + win],
                    horizon,
                    sun_threshold=sun_thr,
                    earth_threshold=earth_thr,
                    bridge_h=bridge_h,
                )
            vis = _series_json(series_cache[key])
            out = score(vis, {}, needs)  # hazards off
            r = float(out["breakdown"]["layer1_R"])
            b = float(out["breakdown"]["layer1_B"])
            feasible = bool(out["feasible"])
            pools[tid]["feasible" if feasible else "infeasible"].append({"R": r, "B": b})
            scored += 1
    return scored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-h", type=int, default=_WINDOW_H)
    parser.add_argument("--step-h", type=int, default=1)
    parser.add_argument("--min-pairs", type=int, default=_MIN_PAIRS)
    parser.add_argument(
        "--year",
        type=int,
        default=0,
        help="If set (e.g. 2027), score every week chunk in that calendar year at Site01.",
    )
    parser.add_argument("--week-start", type=str, default="2027-01-01T00:00:00Z")
    parser.add_argument("--week-end", type=str, default="2027-01-07T23:00:00Z")
    parser.add_argument("--betas", type=str, default="")
    parser.add_argument("--beta", type=float, default=_DEFAULT_BETA)
    parser.add_argument("--max-uplift", type=float, default=_DEFAULT_MAX_UPLIFT)
    args = parser.parse_args()

    if not real_data_available():
        print("INSUFFICIENT: kernels or Site01 DEM missing.")
        print("per D-d37a: stop and decide whether to compute/fetch more.")
        return 2

    if args.betas.strip():
        betas = [float(x) for x in args.betas.split(",") if x.strip()]
    else:
        betas = [float(args.beta)]
    max_uplift = float(args.max_uplift)
    win = max(int(args.window_h), 2)
    step = max(int(args.step_h), 1)

    if args.year:
        chunks = _week_chunks(int(args.year))
    else:
        # single window from flags
        s = args.week_start[:10]
        e = args.week_end[:10]
        chunks = [(date.fromisoformat(s), date.fromisoformat(e))]

    horizon = mask_for_site(SITE01)
    ephem = SpiceEphemeris()
    pools: dict[str, dict[str, list]] = defaultdict(lambda: {"feasible": [], "infeasible": []})
    scored = 0
    t_all = time.perf_counter()
    print(
        f"Site01 chunks={len(chunks)} window={win}h step={step}h "
        f"templates={len(TEMPLATES)} max_uplift={max_uplift}",
        flush=True,
    )

    for i, (d0, d1) in enumerate(chunks, 1):
        # hourly from 00:00 d0 through 23:00 d1
        times = parse_time_window(_iso(d0, 0), _iso(d1, 23), step_h=1)
        if len(times) < win:
            print(f"[{i}/{len(chunks)}] {d0}..{d1} skip (n={len(times)} < window)", flush=True)
            continue
        t0 = time.perf_counter()
        sky = ephem.sky(SITE01, times)
        starts = list(range(0, len(times) - win + 1, step))
        n = _accumulate_week(pools, sky, horizon, starts, win)
        scored += n
        print(
            f"[{i}/{len(chunks)}] {d0}..{d1} hours={len(times)} windows={len(starts)} "
            f"scored+={n} wall={time.perf_counter()-t0:.2f}s",
            flush=True,
        )

    print(f"scored_points={scored} wall_total={time.perf_counter()-t_all:.1f}s")
    print(f"bands: accept if rate in [{_LOW_PCT}, {_HIGH_PCT}] %; else REOPEN (D-7c70)")

    # Feasibility mix
    print("\n=== pool sizes ===")
    for tid in TEMPLATES:
        nf = len(pools[tid]["feasible"])
        ni = len(pools[tid]["infeasible"])
        print(f"{tid:24} feas={nf:5} infeas={ni:5}")

    print(
        f"\n{'beta':>6} {'feas%':>8} {'feas_band':>11} {'infeas%':>8} {'infeas_band':>11} "
        f"{'upl_med':>8} {'upl_max':>8} {'cap_hits':>10}"
    )
    thin = False
    for beta in betas:
        res = _pooled_rates(pools, beta, max_uplift)
        for split in ("feasible", "infeasible"):
            if res[split]["pairs"] < int(args.min_pairs):
                thin = True
        f_rate = res["feasible"]["rate"]
        i_rate = res["infeasible"]["rate"]
        f_s = f"{f_rate:.2f}" if f_rate is not None else "n/a"
        i_s = f"{i_rate:.2f}" if i_rate is not None else "n/a"
        u = res["uplift"]
        med_s = f"{u['med']:.4f}" if u["med"] is not None else "n/a"
        max_s = f"{u['max']:.4f}" if u["max"] is not None else "n/a"
        print(
            f"{beta:6.2f} {f_s:>8} {res['feasible']['band']:>11} {i_s:>8} "
            f"{res['infeasible']['band']:>11} {med_s:>8} {max_s:>8} "
            f"{u['cap_hits']:>4}/{u['n']:<5}"
        )
        print(
            f"SUMMARY beta={beta} feasible={f_s}% {_band_label(f_rate)} "
            f"infeasible={i_s}% {_band_label(i_rate)}"
        )

    if thin:
        print("\nINSUFFICIENT_PAIR_COUNT per D-d37a.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
