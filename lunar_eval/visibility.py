"""Hourly Sun/Earth visibility series (P3). # per D-20261114-pj-9e53"""

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


def _as_hours(samples: int, step_h: float) -> int | float:
    """Samples → hours; stays an int when the result is whole (hourly series, or whole hours at 10 min)."""
    hours = round(samples * step_h, 6)
    return int(hours) if hours == int(hours) else hours


def longest_night_h(fraction: NDArray[np.floating], lit_threshold: float = 0.0, step_h: float = 1.0) -> int | float:
    dark = np.asarray(fraction) <= lit_threshold
    best = cur = 0
    for v in dark:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return _as_hours(int(best), step_h)


def _bridge(lit: NDArray[np.bool_], gap: int) -> NDArray[np.bool_]:
    b = lit.copy()
    n = len(b)
    i = 0
    while i < n:
        if not b[i]:
            j = i
            while j < n and not b[j]:
                j += 1
            if i > 0 and j < n and j - i <= gap:
                b[i:j] = True
            i = j
        else:
            i += 1
    return b


def series(
    sky,
    horizon,
    *,
    sun_threshold: float = 0.0,
    earth_threshold: float = 0.0,
    bridge_h: float = 0,
    step_min: int = 60,
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

    return {
        "sun_fraction": sun_frac,
        "earth_fraction": earth_frac,
        "step_min": int(step_min),
        "longest_night_h": longest_night_h(sun_frac, sun_threshold, step_h),
        "longest_no_earth_h": longest_night_h(earth_frac, earth_threshold, step_h),
        "longest_lit_h": longest_lit_h(sun_frac, sun_threshold, bridge_h, step_h),
        "hours_sun_above_threshold": _as_hours(int(np.sum(sun_frac > sun_threshold)), step_h),
        "hours_earth_above_threshold": _as_hours(int(np.sum(earth_frac > earth_threshold)), step_h),
        "any_both": bool(
            np.any((sun_frac > sun_threshold) & (earth_frac > earth_threshold))
        ),
        "schedule_version": horizon.schedule_version,
    }


def longest_lit_h(
    fraction: NDArray[np.floating],
    lit_threshold: float = 0.0,
    bridge_h: float = 0,
    step_h: float = 1.0,
) -> int | float:
    lit = np.asarray(fraction) > lit_threshold
    gap_samples = int(math.floor(bridge_h / step_h + 1e-9)) if bridge_h > 0 else 0
    if gap_samples > 0:
        lit = _bridge(lit, gap_samples)
    best = cur = 0
    for v in lit:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return _as_hours(int(best), step_h)
