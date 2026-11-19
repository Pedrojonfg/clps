"""Deep search over user ranges (S7). # per D-54f0 D-e3cf D-cb6b D-8a25 D-1ebf D-c159 D-60a3"""

from __future__ import annotations

import json
import math
import time
from typing import Any, Callable, Sequence

import numpy as np

from moonpark.providers import Site
from moonpark.score import score

DEFAULT_TMAX_S = 300.0  # per D-8a25
DEFAULT_LEADERBOARD_N = 20  # per D-60a3
_CLIMB_EVALS_PER_START = 10.0  # per D-cb6b calibration stand-in for default N
_CELL_M = 1000.0  # per D-1ebf / D-f369 1 km cell
# Requirement names no search can evaluate yet: requested ones are warned and skipped (D-20261118-pj-75f1).
# Empty today; read at call time.
UNEVALUABLE_REQUIREMENTS: set[str] = set()


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


class _Stopped(Exception):
    pass


def _cp_entry(key: tuple[int, int], row: dict | None) -> list:
    if row is None:  # evaluated, cell lacked data the search needs (dropped)
        return [key[0], key[1], None]
    return [key[0], key[1], [row["feasible"], row["score"], row["companion_score"], row["hazard_gap_star"]]]


def _index(v: Any, n: int, what: str) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < n:
        raise ValueError(f"resume checkpoint: bad {what} index {v!r}")
    return v


def _number(v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
        raise ValueError(f"resume checkpoint: bad row value {v!r}")
    return float(v)


def _validated_resume(resume: Any, fingerprint: dict, n_starts: int, n_sites: int, n_times: int,
                      cache: dict, dropped: set, make_row: Callable) -> int:
    """Check a client-supplied checkpoint and load its rows into ``cache``/``dropped``; returns the start count.
    Anything malformed is a ValueError (the API answers 400), never an internal error."""
    if not isinstance(resume, dict):
        raise ValueError("resume checkpoint must be an object")
    if resume.get("fingerprint") != fingerprint:
        raise ValueError("resume checkpoint does not match this search (range, window, mode, step or requirements)")
    ns = resume.get("n_starts", n_starts)  # start count fixed at the first run
    if isinstance(ns, bool) or not isinstance(ns, int) or ns < 0:
        raise ValueError(f"resume checkpoint: bad n_starts {ns!r}")
    rows = resume.get("rows")
    if rows is None:
        rows = []
    if not isinstance(rows, list):
        raise ValueError("resume checkpoint: rows must be a list")
    for entry in rows:
        if not isinstance(entry, list) or len(entry) != 3:
            raise ValueError(f"resume checkpoint: bad row {entry!r}")
        si, ti = _index(entry[0], n_sites, "site"), _index(entry[1], n_times, "window")
        vals = entry[2]
        if vals is None:
            cache[(si, ti)] = None
            dropped.add(si)
            continue
        if (not isinstance(vals, list) or len(vals) != 4 or not isinstance(vals[0], bool)
                or not isinstance(vals[3], bool)):
            raise ValueError(f"resume checkpoint: bad row values {vals!r}")
        cache[(si, ti)] = make_row(si, ti, [vals[0], _number(vals[1]), _number(vals[2]), vals[3]])
    return ns


def deep_search(
    sites: Sequence[Site],
    window_starts,
    window_hours: int,
    needs: dict,
    *,
    evaluate: Callable[..., dict | None],
    mode: str = "optimized",
    start_n: int | None = None,
    tmax_s: float = DEFAULT_TMAX_S,
    cost_per_eval_s: float = 0.5,
    leaderboard_n: int = DEFAULT_LEADERBOARD_N,
    site_xy: Sequence[tuple[float, float]] | None = None,
    should_stop: Callable[[], bool] | None = None,
    resume: dict | None = None,
    fingerprint_extra: dict | None = None,
) -> dict[str, Any]:
    """Search site×time in a user range. # per D-54f0 D-c159 D-20261118-pj-1454 D-75f1

    ``evaluate`` returning None means the cell lacks data the search needs: the whole cell is dropped
    and counted (D-75f1). ``tmax_s`` only sizes the optimized start count; it never stops the search
    (D-1454). ``should_stop()`` is checked before each evaluation; when True the result has state
    "stopped" and a JSON ``checkpoint``; passing it back as ``resume`` continues without redoing
    evaluations and ends equal to an uninterrupted run. ``fingerprint_extra`` (JSON-able: the full request
    requirements, rectangle, step, hazards switch...) joins the resume fingerprint so a checkpoint only resumes
    the same search. A malformed ``resume`` raises ValueError.
    """
    t_wall0 = time.perf_counter()
    starts = np.asarray(window_starts, dtype="datetime64[s]").reshape(-1)
    site_list = list(sites)
    h = int(window_hours)
    claim = "grid_optimum" if mode == "total_coverage" else "best_seen"  # per D-54f0

    if mode not in ("optimized", "total_coverage"):
        raise ValueError(f"invalid mode: {mode!r}")
    if not site_list or starts.size == 0:
        return {"mode": mode, "claim": claim, "best": None, "leaderboard": [], "export_rows": [],
                "rows_evaluated": 0, "runtime_s": time.perf_counter() - t_wall0, "eta_s": None,
                "n_starts": 0, "state": "complete", "checkpoint": None, "dropped_cells": 0}

    if site_xy is None:
        # ponytail: synthetic/tests should pass xy; without it treat index adjacency as unavailable.
        xy = [(float(i), 0.0) for i in range(len(site_list))]
    else:
        xy = list(site_xy)
        if len(xy) != len(site_list):
            raise ValueError("site_xy length must match sites")

    if mode == "optimized":
        n_starts = int(start_n) if start_n is not None else _default_start_n(tmax_s, cost_per_eval_s)
        n_starts = max(1, min(n_starts, len(site_list) * len(starts)))
    else:
        n_starts = 0
    fingerprint = {
        "mode": mode, "n_sites": len(site_list), "n_window_starts": int(starts.size),
        "first_start": str(starts[0]), "window_hours": h, "needs": json.loads(json.dumps(needs, default=str)),
        "extra": json.loads(json.dumps(fingerprint_extra or {}, default=str, sort_keys=True)),
    }

    cache: dict[tuple[int, int], dict | None] = {}
    dropped: set[int] = set()

    def make_row(si: int, ti: int, vals: list) -> dict:
        s = site_list[si]
        return {
            "site": {"lat_deg": s.lat_deg, "lon_deg": s.lon_deg},
            "window_start": np.datetime64(starts[ti], "s"),
            "window_hours": h,
            "feasible": bool(vals[0]),
            "score": float(vals[1]),
            "companion_score": float(vals[2]),
            "hazard_gap_star": bool(vals[3]),
        }

    if resume:
        n_starts = _validated_resume(resume, fingerprint, n_starts, len(site_list), int(starts.size), cache,
                                     dropped, make_row)

    def eval_at(si: int, ti: int) -> dict | None:
        key = (si, ti)
        if si in dropped:
            return None
        if key not in cache:
            if should_stop is not None and should_stop():
                raise _Stopped
            ev = evaluate(site_list[si], starts[ti], h)
            if ev is None:
                cache[key] = None
                dropped.add(si)
            else:
                cache[key] = _row_from_eval(site_list[si], starts[ti], h, needs, ev)
        return cache[key]

    seeds = _regular_start_indices(len(site_list), len(starts), n_starts) if mode == "optimized" else []
    state = "complete"
    try:
        if mode == "total_coverage":
            for si in range(len(site_list)):
                for ti in range(len(starts)):
                    eval_at(si, ti)
        else:
            # optimized — multi-start hill climb # per D-54f0 D-1ebf D-e3cf; cached cells replay for free on resume
            for si0, ti0 in seeds:
                si, ti = si0, ti0
                cur = eval_at(si, ti)
                while cur is not None:
                    improved = None
                    best_nb = None
                    for sj, tj in _neighbour_indices(si, ti, site_list, starts, xy):
                        nb = eval_at(sj, tj)
                        if nb is not None and _better(nb, cur) and (best_nb is None or _better(nb, best_nb)):
                            best_nb = nb
                            improved = (sj, tj)
                    if improved is None or si in dropped:
                        break
                    si, ti = improved
                    cur = best_nb
    except _Stopped:
        state = "stopped"

    rows = [r for (si, _ti), r in cache.items() if r is not None and si not in dropped]
    rows.sort(key=_rank_key)
    checkpoint = None
    if state == "stopped":
        total = len(site_list) * len(starts)
        checkpoint = {
            "version": 1,
            "fingerprint": fingerprint,
            "n_starts": n_starts,
            "rows": [_cp_entry(k, v) for k, v in cache.items()],
            "dropped_sites": sorted(dropped),
            # total_coverage: cells x windows not yet evaluated; optimized: hill climbs replay from the seeds
            "remaining": (total - len(cache)) if mode == "total_coverage" else None,
        }
    return {
        "mode": mode,
        "claim": claim,
        "best": rows[0] if rows else None,
        "leaderboard": rows[: max(int(leaderboard_n), 0)],
        "export_rows": rows,  # per D-60a3 CSV / filter
        "rows_evaluated": len(cache),
        "runtime_s": time.perf_counter() - t_wall0,
        "eta_s": None,
        "n_starts": len(seeds),
        "state": state,
        "checkpoint": checkpoint,
        "dropped_cells": len(dropped),
    }
