"""Hourly Sun/Earth visibility series (P3). # per D-20261114-pj-9e53, D-20261118-pj-9413 (durations)"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray


def sun_fraction(
    elevation_deg: NDArray[np.floating],
    mask_el_deg: NDArray[np.floating],
    sun_radius_deg: float | NDArray[np.floating] = 0.2665,
) -> NDArray[np.float64]:
    x = np.clip(
        (np.asarray(elevation_deg) - np.asarray(mask_el_deg)) / np.asarray(sun_radius_deg),
        -1.0,
        1.0,
    )
    return 1.0 - (np.arccos(x) - x * np.sqrt(1.0 - x * x)) / np.pi


def _mask_el_at_geo_az(geo_az_deg: NDArray[np.floating], elevation_deg: NDArray[np.floating]) -> NDArray[np.float64]:
    mask_az = (180.0 - np.asarray(geo_az_deg, dtype=np.float64)) % 360.0
    elev = np.asarray(elevation_deg, dtype=np.float64)
    az_bins = np.arange(len(elev), dtype=np.float64) * (360.0 / len(elev))
    elev_wrap = np.concatenate([elev, elev[:1]])
    az_wrap = np.concatenate([az_bins, [360.0]])
    return np.interp(mask_az, az_wrap, elev_wrap)


def _as_hours(hours: float) -> int | float:
    """Rounded hours; stays an int when the result is whole (hourly series, or whole hours at 10 min)."""
    hours = round(float(hours), 6)
    return int(hours) if hours == int(hours) else hours


def _runs(mask: NDArray[np.bool_]) -> tuple[NDArray[np.intp], NDArray[np.intp]]:
    """Start and end (inclusive) sample indices of each run of True."""
    d = np.diff(np.concatenate([[0], np.asarray(mask, dtype=np.int8), [0]]))
    return np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1


def _run_bounds(mask: NDArray[np.bool_], step_h: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Per-run duration bounds on a closed sample grid (D-20261118-pj-9413).

    Lower: last minus first sample of the run. Upper: hole to hole, from the last opposite-state sample before
    to the first after, clipped to the window [t_0, t_(n-1)].
    """
    s, e = _runs(mask)
    n = len(mask)
    lower = (e - s) * step_h
    upper = (np.minimum(e + 1, n - 1) - np.maximum(s - 1, 0)) * step_h
    return lower.astype(np.float64), upper.astype(np.float64)


def _longest(b: NDArray[np.float64]) -> int | float:
    return _as_hours(b.max()) if len(b) else 0


def longest_night_bounds(
    fraction: NDArray[np.floating], lit_threshold: float = 0.0, step_h: float = 1.0
) -> tuple[int | float, int | float]:
    """(lower, upper) bounds of the longest dark run; a sample is dark when fraction <= threshold."""
    lo, up = _run_bounds(np.asarray(fraction) <= lit_threshold, step_h)
    return _longest(lo), _longest(up)


def longest_night_h(fraction: NDArray[np.floating], lit_threshold: float = 0.0, step_h: float = 1.0) -> int | float:
    """Longest dark run, upper (hole-to-hole) bound: a maximum-type limit (D-20261118-pj-9413)."""
    return longest_night_bounds(fraction, lit_threshold, step_h)[1]


def total_lit_h(fraction: NDArray[np.floating], lit_threshold: float = 0.0, step_h: float = 1.0) -> int | float:
    """Total lit time: sum of per-run lower bounds (single lit sample = 0 h) (D-20261118-pj-9413)."""
    return _as_hours(_run_bounds(np.asarray(fraction) > lit_threshold, step_h)[0].sum())


def _bridge(lit: NDArray[np.bool_], gap: int) -> NDArray[np.bool_]:
    """Fill interior dark runs of at most `gap` samples (runs touching a window edge are never bridged).
    Callers pass gap = floor(bridge_h / step) - 1: see longest_lit_bounds."""
    b = np.asarray(lit, dtype=bool)
    s, e = _runs(~b)
    keep = (s > 0) & (e < len(b) - 1) & (e - s + 1 <= gap)
    edges = np.zeros(len(b) + 1, dtype=np.int64)
    np.add.at(edges, s[keep], 1)
    np.add.at(edges, e[keep] + 1, -1)
    return b | (np.cumsum(edges[:-1]) > 0)


def series(
    sky,
    horizon,
    *,
    sun_threshold: float = 0.0,
    earth_threshold: float = 0.0,
    bridge_h: float = 0,
    step_min: int = 60,
    energy=None,
) -> dict:
    step_h = step_min / 60.0
    sun_az = np.array([s.sun_az_deg for s in sky], dtype=np.float64)
    sun_el = np.array([s.sun_el_deg for s in sky], dtype=np.float64)
    sun_r = np.array([s.sun_radius_deg for s in sky], dtype=np.float64)
    earth_az = np.array([s.earth_az_deg for s in sky], dtype=np.float64)
    earth_el = np.array([s.earth_el_deg for s in sky], dtype=np.float64)
    earth_r = np.array([s.earth_radius_deg for s in sky], dtype=np.float64)

    mask_sun = _mask_el_at_geo_az(sun_az, horizon.elevation_deg)
    mask_earth = _mask_el_at_geo_az(earth_az, horizon.elevation_deg)

    sun_frac = sun_fraction(sun_el, mask_sun, sun_r)
    earth_frac = sun_fraction(earth_el, mask_earth, earth_r)

    night_lo, night_up = longest_night_bounds(sun_frac, sun_threshold, step_h)
    no_earth_lo, no_earth_up = longest_night_bounds(earth_frac, earth_threshold, step_h)
    lit_lo, lit_up = longest_lit_bounds(sun_frac, sun_threshold, bridge_h, step_h)
    # D-20261118-pj-9413: maximum-type limits use the upper bound, minimum-type the lower; the other bound is
    # exposed (`*_lower` / `*_upper`) for the risk model.
    out = {
        "sun_fraction": sun_frac,
        "earth_fraction": earth_frac,
        "step_min": int(step_min),
        "longest_night_h": night_up,
        "longest_night_h_lower": night_lo,
        "longest_no_earth_h": no_earth_up,
        "longest_no_earth_h_lower": no_earth_lo,
        "longest_lit_h": lit_lo,
        "longest_lit_h_upper": lit_up,
        "hours_sun_above_threshold": total_lit_h(sun_frac, sun_threshold, step_h),
        "hours_earth_above_threshold": total_lit_h(earth_frac, earth_threshold, step_h),
        "any_both": bool(
            np.any((sun_frac > sun_threshold) & (earth_frac > earth_threshold))
        ),
        "schedule_version": horizon.schedule_version,
    }
    if energy is not None:
        from moonpark.energy import soc_series

        soc = soc_series(
            sun_frac, sun_az, sun_el, energy, step_h=step_h, lit_threshold=sun_threshold
        )
        out["soc"] = soc
        out["soc_min"] = float(soc.min()) if len(soc) else 1.0
    return out


def longest_lit_bounds(
    fraction: NDArray[np.floating],
    lit_threshold: float = 0.0,
    bridge_h: float = 0,
    step_h: float = 1.0,
) -> tuple[int | float, int | float]:
    """(lower, upper) bounds of the longest lit run after bridging dark gaps of at most bridge_h.

    Pessimistic (D-20261118-pj-9413): an interior run of k dark samples may last up to (k + 1) steps (hole to
    hole), so it is bridged only when (k + 1) * step <= bridge_h. A coarse grid therefore never bridges a gap
    that a finer grid of the same sky sees as longer than bridge_h.
    """
    lit = np.asarray(fraction) > lit_threshold
    gap_samples = int(math.floor(bridge_h / step_h + 1e-9)) - 1 if bridge_h > 0 else 0
    if gap_samples > 0:
        lit = _bridge(lit, gap_samples)
    lo, up = _run_bounds(lit, step_h)
    return _longest(lo), _longest(up)


def longest_lit_h(
    fraction: NDArray[np.floating],
    lit_threshold: float = 0.0,
    bridge_h: float = 0,
    step_h: float = 1.0,
) -> int | float:
    """Longest lit run, lower bound (last minus first lit sample): a minimum-type limit (D-20261118-pj-9413)."""
    return longest_lit_bounds(fraction, lit_threshold, bridge_h, step_h)[0]
