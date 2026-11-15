"""Deep search over user ranges (S7). # per D-54f0 D-e3cf D-cb6b D-8a25 D-1ebf D-c159 D-60a3"""

from __future__ import annotations

import math
import time
from typing import Any, Callable, Sequence

import numpy as np

from lunar_eval.providers import Site
from lunar_eval.score import score

DEFAULT_TMAX_S = 300.0  # per D-8a25
DEFAULT_LEADERBOARD_N = 20  # per D-60a3
_CLIMB_EVALS_PER_START = 10.0  # per D-cb6b calibration stand-in for default N
_CELL_M = 1000.0  # per D-1ebf / D-f369 1 km cell


def _rank_key(row: dict) -> tuple:
    # per D-5577 spirit without local distance: feasible by score; else companion.
    if row["feasible"]:
        return (0, -float(row["score"]))
    return (1, -float(row["companion_score"]))


def _better(a: dict, b: dict) -> bool:
    return _rank_key(a) < _rank_key(b)


def _row_from_eval(
    site: Site,
    start: np.datetime64,
    window_hours: int,
    needs: dict,
    ev: dict,
) -> dict:
    series = ev["series"]
    hazards = ev.get("hazards") or {}
    scored = score(series, hazards, needs)
    if "hazard_gap_star" in ev:
        gap = bool(ev["hazard_gap_star"])
    else:
        gap = bool(scored.get("hazard_gap_star"))
    gap = gap or bool(scored.get("hazard_gap_star"))
    return {
        "site": {"lat_deg": site.lat_deg, "lon_deg": site.lon_deg},
        "window_start": np.datetime64(start, "s"),
        "window_hours": int(window_hours),
        "feasible": bool(scored["feasible"]),
        "score": float(scored["score"]),
        "companion_score": float(scored["companion_score"]),
        "hazard_gap_star": gap,
    }


def _default_start_n(tmax_s: float, cost_per_eval_s: float) -> int:
    # per D-cb6b / D-8a25: densest effort that fits wall-clock budget.
    cost = max(float(cost_per_eval_s), 1e-9)
    return max(1, int(float(tmax_s) / (cost * _CLIMB_EVALS_PER_START)))


def _regular_start_indices(n_sites: int, n_times: int, start_n: int) -> list[tuple[int, int]]:
    # per D-e3cf: regular space-filling lattice in (site, time) index space.
    total = max(n_sites * n_times, 1)
    n = min(max(int(start_n), 1), total)
    nx = max(1, int(round(math.sqrt(n))))
    ny = max(1, math.ceil(n / nx))
    while nx * ny > n and nx > 1:
        nx -= 1
        ny = max(1, math.ceil(n / nx))
    xs = np.unique(np.linspace(0, n_sites - 1, num=min(nx, n_sites), dtype=float).astype(int))
    ys = np.unique(np.linspace(0, n_times - 1, num=min(ny, n_times), dtype=float).astype(int))
    out: list[tuple[int, int]] = []
    for si in xs:
        for ti in ys:
            out.append((int(si), int(ti)))
            if len(out) >= n:
                return out
    return out


def _neighbour_indices(
    si: int,
    ti: int,
    sites: Sequence[Site],
    starts: Sequence[np.datetime64],
    xy: Sequence[tuple[float, float]],
) -> list[tuple[int, int]]:
    # per D-1ebf: ±1 precomputed cell and ±1 h.
    ox, oy = xy[si]
    out: list[tuple[int, int]] = []
    for sj, (x, y) in enumerate(xy):
        dx, dy = abs(x - ox), abs(y - oy)
        space_nb = (dx == _CELL_M and dy == 0.0) or (dy == _CELL_M and dx == 0.0)
        if not space_nb and sj != si:
            continue
        for tj in range(len(starts)):
            if sj == si and tj == ti:
                continue
            if sj == si and abs(tj - ti) == 1:
                out.append((sj, tj))
            elif space_nb and tj == ti:
                out.append((sj, tj))
    return out


def deep_search(
    sites: Sequence[Site],
    window_starts,
    window_hours: int,
    needs: dict,
    *,
    evaluate: Callable[..., dict],
    mode: str = "optimized",
    start_n: int | None = None,
    tmax_s: float = DEFAULT_TMAX_S,
    cost_per_eval_s: float = 0.5,
    leaderboard_n: int = DEFAULT_LEADERBOARD_N,
    site_xy: Sequence[tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Search site×time in a user range. # per D-54f0 D-c159"""
    t_wall0 = time.perf_counter()
    starts = np.asarray(window_starts, dtype="datetime64[s]").reshape(-1)
    site_list = list(sites)
    h = int(window_hours)

    empty = {
        "mode": mode,
        "claim": "grid_optimum" if mode == "total_coverage" else "best_seen",
        "best": None,
        "leaderboard": [],
        "export_rows": [],
        "rows_evaluated": 0,
        "runtime_s": 0.0,
        "eta_s": None,
        "n_starts": 0,
    }
    if mode not in ("optimized", "total_coverage"):
        raise ValueError(f"invalid mode: {mode!r}")
    if not site_list or starts.size == 0:
        empty["mode"] = mode
        empty["claim"] = "grid_optimum" if mode == "total_coverage" else "best_seen"
        empty["runtime_s"] = time.perf_counter() - t_wall0
        return empty

    if site_xy is None:
        # ponytail: synthetic/tests should pass xy; without it treat index adjacency as unavailable.
        xy = [(float(i), 0.0) for i in range(len(site_list))]
    else:
        xy = list(site_xy)
        if len(xy) != len(site_list):
            raise ValueError("site_xy length must match sites")

    cache: dict[tuple[int, int], dict] = {}

    def eval_at(si: int, ti: int) -> dict:
        key = (si, ti)
        if key not in cache:
            cache[key] = _row_from_eval(
                site_list[si], starts[ti], h, needs, evaluate(site_list[si], starts[ti], h)
            )
        return cache[key]

    if mode == "total_coverage":
        for si in range(len(site_list)):
            for ti in range(len(starts)):
                eval_at(si, ti)
        rows = list(cache.values())
        rows.sort(key=_rank_key)
        best = rows[0] if rows else None
        board = rows[: max(int(leaderboard_n), 0)]
        return {
            "mode": "total_coverage",
            "claim": "grid_optimum",  # per D-54f0
            "best": best,
            "leaderboard": board,
            "export_rows": rows,  # per D-60a3 CSV / filter
            "rows_evaluated": len(cache),
            "runtime_s": time.perf_counter() - t_wall0,
            "eta_s": None,
            "n_starts": 0,
        }

    # optimized — multi-start hill climb # per D-54f0 D-1ebf D-e3cf
    n_starts = int(start_n) if start_n is not None else _default_start_n(tmax_s, cost_per_eval_s)
    n_starts = max(1, min(n_starts, len(site_list) * len(starts)))
    seeds = _regular_start_indices(len(site_list), len(starts), n_starts)

    seen_rows: list[dict] = []
    for si0, ti0 in seeds:
        si, ti = si0, ti0
        cur = eval_at(si, ti)
        while True:
            improved = None
            best_nb = None
            for sj, tj in _neighbour_indices(si, ti, site_list, starts, xy):
                nb = eval_at(sj, tj)
                if _better(nb, cur) and (best_nb is None or _better(nb, best_nb)):
                    best_nb = nb
                    improved = (sj, tj)
            if improved is None:
                break
            si, ti = improved
            cur = best_nb  # type: ignore[assignment]

    seen_rows = list(cache.values())
    seen_rows.sort(key=_rank_key)
    best = seen_rows[0] if seen_rows else None
    board = seen_rows[: max(int(leaderboard_n), 0)]
    return {
        "mode": "optimized",
        "claim": "best_seen",  # per D-54f0
        "best": best,
        "leaderboard": board,
        "export_rows": seen_rows,  # per D-60a3 CSV
        "rows_evaluated": len(cache),
        "runtime_s": time.perf_counter() - t_wall0,
        "eta_s": None,
        "n_starts": len(seeds),
    }
