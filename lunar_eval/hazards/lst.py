"""Local solar time for climatology bins (D-41a2)."""

from __future__ import annotations

import math

import numpy as np


def local_solar_time_h_from_utc(time_utc: np.datetime64, lon_deg: float) -> float:
    """Ponytail LST for bin lookup until ephemeris-backed subsolar lon is wired."""
    hour = int(np.datetime64(time_utc, "h").astype(np.int64) % 24)
    return (hour + lon_deg / 15.0) % 24.0


def lst_bin_index(lst_h: float, *, bin_h: float = 0.25) -> int:
    return int(math.floor(lst_h / bin_h)) % int(24 / bin_h)