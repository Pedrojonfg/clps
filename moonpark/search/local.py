"""Local site×time search (S6). # per D-9cc5 D-72bc D-f57e D-5577 D-75f1 D-b3dc"""

from __future__ import annotations

import numpy as np

from moonpark.horizon import polar_stereo_xy
from moonpark.providers import Site
from moonpark.score import score

DEFAULT_RADIUS_KM = 5.0  # per D-72bc


def window_slide_starts(a: np.datetime64, h_hours: int) -> np.ndarray:
    """Hourly starts from a−h through a+h inclusive. # per D-9cc5"""
    h = int(h_hours)
    offsets = np.arange(-h, h + 1, dtype="timedelta64[h]")
    anchor = np.datetime64(a, "s")
    return anchor + offsets


def _distance_hours(anchor: np.datetime64, start: np.datetime64) -> float:
    delta = np.datetime64(start, "s") - np.datetime64(anchor, "s")
    return abs(float(delta / np.timedelta64(1, "h")))


def _site_km(origin: Site, site: Site) -> float:
    ox, oy = polar_stereo_xy(origin.lat_deg, origin.lon_deg)
    sx, sy = polar_stereo_xy(site.lat_deg, site.lon_deg)
    return float(np.hypot(sx - ox, sy - oy) / 1000.0)


def _sort_key(row: dict) -> tuple:
    # per D-9cc5 / D-72bc / D-5577: feasible by Δt then score; infeasible by companion then Δt.
    if row["feasible"]:
        return (0, row["distance_hours"], -row["score"], row["distance_km"], row["window_start"])
    return (1, -row["companion_score"], row["distance_hours"], row["distance_km"], row["window_start"])


def local_search(
    origin: Site,
    window_start,
    window_hours: int,
    needs: dict,
    *,
    evaluate,
    neighbour_sites=None,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> dict:
    anchor = np.datetime64(window_start, "s")
    neighbours = list(neighbour_sites or [])
    sites: list[Site] = [origin]
    for nb in neighbours:
        if _site_km(origin, nb) <= float(radius_km):
            sites.append(nb)

    starts = window_slide_starts(anchor, window_hours)
    rows: list[dict] = []
    dropped = 0
    h = int(window_hours)
    for site in sites:
        dist_km = _site_km(origin, site)
        for start in starts:
            ev = evaluate(site, start, h)
            if ev is None:  # the window lacks hazard data for a limit the user set (D-75f1 / D-b3dc)
                dropped += 1
                continue
            series = ev["series"]
            hazards = ev.get("hazards") or {}
            scored = score(series, hazards, needs)
            gap = bool(ev.get("hazard_gap_star")) or bool(scored.get("hazard_gap_star"))
            if gap:  # a set limit is not evaluated: dropped and counted, never a starred row (D-75f1 / D-b3dc)
                dropped += 1
                continue
            rows.append(
                {
                    "site": {"lat_deg": site.lat_deg, "lon_deg": site.lon_deg},
                    "window_start": np.datetime64(start, "s"),
                    "window_hours": h,
                    "feasible": scored["feasible"],
                    "score": scored["score"],
                    "companion_score": scored["companion_score"],
                    "hazard_gap_star": False,  # kept for the row schema; starred windows are dropped above
                    "distance_hours": _distance_hours(anchor, start),
                    "distance_km": dist_km,
                }
            )

    leaderboard = sorted(rows, key=_sort_key)
    pick = leaderboard[0] if leaderboard else None
    return {"pick": pick, "leaderboard": leaderboard, "dropped_windows": dropped}


def nearest_feasible_time(times, series_per_window, needs, t0):
    best_index: int | None = None
    best_time = None
    best_score = None
    best_dt = None
    for index, (time, series) in enumerate(zip(times, series_per_window, strict=True)):
        sc = score(series, {}, needs)
        if not sc["feasible"]:
            continue
        dt = abs(time - t0)
        if best_index is None:
            best_index, best_time, best_score, best_dt = index, time, sc, dt
            continue
        if dt < best_dt or (dt == best_dt and time > best_time):
            best_index, best_time, best_score, best_dt = index, time, sc, dt
    if best_index is None:
        return None
    return {"time": best_time, "score": best_score, "index": best_index}


def better_neighbours(origin: Site, candidates: list, needs: dict, radius_km: float):
    from math import hypot

    ox, oy = polar_stereo_xy(origin.lat_deg, origin.lon_deg)
    best: dict | None = None
    best_value: float | None = None
    for site, series in candidates:
        sx, sy = polar_stereo_xy(site.lat_deg, site.lon_deg)
        if hypot(sx - ox, sy - oy) / 1000.0 > radius_km:
            continue
        sc = score(series, {}, needs)
        if not sc["feasible"]:
            continue
        value = sc["score"]
        if best is None or value > best_value:
            best = {"site": site, "score": sc, "series": series}
            best_value = value
    return best