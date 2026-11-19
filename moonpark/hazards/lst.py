"""Local solar time for climatology bins (D-41a2), from SPICE et2lst (D-20261118-pj-633d)."""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

MOON_BODY_ID = 301


class HazardDataUnavailable(RuntimeError):
    """Program data a hazard needs (ephemeris for season / local time, climatology) is not available.

    Callers must not substitute a value: the hazard is "not evaluated" (D-20261118-pj-b3dc)."""


def _utc_seconds(time_utc: np.datetime64) -> int:
    return int(np.datetime64(time_utc, "s").astype(np.int64))


@lru_cache(maxsize=65536)
def _et_from_utc_seconds(t_s: int) -> float:
    """Ephemeris time for a UTC instant (whole seconds). Failures raise and are not cached."""
    try:
        import spiceypy

        from moonpark.ephemeris.spice import KERNEL_DIR, _furnsh

        _furnsh(KERNEL_DIR)
        iso = str(np.datetime64(t_s, "s")).replace("T", " ")
        return float(spiceypy.utc2et(iso + " UTC"))
    except Exception as exc:  # SPICE error, missing kernel, missing spiceypy
        raise HazardDataUnavailable(f"ephemeris time unavailable: {exc}") from exc


def et_from_utc(time_utc: np.datetime64) -> float:
    """Ephemeris time (TDB s past J2000) for a UTC datetime64; raises HazardDataUnavailable."""
    return _et_from_utc_seconds(_utc_seconds(time_utc))


@lru_cache(maxsize=262144)
def _lst_h(t_s: int, lon_deg: float) -> float:
    et = _et_from_utc_seconds(t_s)
    try:
        import spiceypy

        hr, mn, sc = spiceypy.et2lst(et, MOON_BODY_ID, math.radians(lon_deg), "PLANETOCENTRIC")[:3]
    except Exception as exc:
        raise HazardDataUnavailable(f"local solar time unavailable: {exc}") from exc
    return (int(hr) + int(mn) / 60.0 + int(sc) / 3600.0) % 24.0


def local_solar_time_h_from_utc(time_utc: np.datetime64, lon_deg: float) -> float:
    """Local solar time (h, [0, 24)) at a planetocentric east longitude on the Moon.

    NAIF et2lst, body 301, planetocentric longitude; noon = 12 h, the Diviner PCP convention
    (LTIM=(NUM-1)*0.25). No light-time correction beyond what et2lst applies. Resolution is one
    second of local time (et2lst returns whole seconds). # per D-20261118-pj-633d
    Raises HazardDataUnavailable if SPICE or its kernels fail (D-20261118-pj-b3dc)."""
    return _lst_h(_utc_seconds(time_utc), float(lon_deg) % 360.0)


def lst_bin_index(lst_h: float, *, bin_h: float = 0.25) -> int:
    return int(math.floor(lst_h / bin_h)) % int(24 / bin_h)
