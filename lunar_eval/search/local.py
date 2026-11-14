"""Nearest feasible time and neighbouring sites (S6). # per D-20261114-pj-de42 D-20261114-pj-9e53"""

from __future__ import annotations

from math import hypot

from lunar_eval.horizon import polar_stereo_xy
from lunar_eval.providers import Site
from lunar_eval.score import score


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