"""Battery state of charge from the Sun series. # per D-20261117-pj-7b2d

Lunar surface, no atmosphere: P_gen = P_peak * sun_fraction * cos(incidence). Static platform, flat site frame,
constant loads, SOC starts at 100 % (all v1 limits recorded in the ADR).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

PANELS = ("horizontal", "fixed_vertical", "tracking_vertical")
RESERVE_DEFAULT = 0.10  # per D-20261117-pj-7b2d (provisional, confirmed by pj)
SIGMA_SOC_DEFAULT = 0.10  # fraction of capacity; per D-20261117-pj-7b2d (provisional, confirmed by pj)


@dataclass(frozen=True)
class EnergyParams:
    capacity_wh: float
    array_w: float  # array power with the Sun at normal incidence
    dark_w: float  # load with no light (survival, incl. heaters)
    lit_w: float | None = None  # load when lit; defaults to dark_w
    panel: str = "tracking_vertical"
    panel_az_deg: float = 0.0  # geographic azimuth (from north), same frame as the sky; not the mask azimuth
    reserve_frac: float = RESERVE_DEFAULT
    charge_eff: float = 1.0

    def __post_init__(self) -> None:
        if self.capacity_wh <= 0 or self.array_w < 0 or self.dark_w < 0:
            raise ValueError("capacity_wh must be > 0; array_w and dark_w >= 0")
        if self.panel not in PANELS:
            raise ValueError(f"panel must be one of {PANELS}")
        if not 0.0 <= self.reserve_frac < 1.0:
            raise ValueError("reserve_frac must be in [0, 1)")
        if not 0.0 < self.charge_eff <= 1.0:
            raise ValueError("charge_eff must be in (0, 1]")


def params_from_needs(needs: dict[str, Any]) -> EnergyParams | None:
    """Energy mode only when tier 1 is complete: capacity, array power and a darkness consumption (W or hours)."""
    cap = needs.get("battery_wh")
    arr = needs.get("array_w")
    if not cap or arr is None:
        return None
    dark = needs.get("dark_w")
    if dark is None and needs.get("endurance_h"):
        dark = float(cap) / float(needs["endurance_h"])  # P_dark = C / endurance
    if dark is None:
        return None
    reserve = needs.get("reserve_pct")
    return EnergyParams(
        capacity_wh=float(cap),
        array_w=float(arr),
        dark_w=float(dark),
        lit_w=None if needs.get("lit_w") is None else float(needs["lit_w"]),
        panel=str(needs.get("panel") or "tracking_vertical"),
        panel_az_deg=float(needs.get("panel_az_deg") or 0.0),
        reserve_frac=RESERVE_DEFAULT if reserve is None else float(reserve) / 100.0,
        charge_eff=1.0 if needs.get("charge_eff") is None else float(needs["charge_eff"]),
    )


def incidence_cos(
    sun_az_deg: NDArray[np.floating], sun_el_deg: NDArray[np.floating], panel: str, panel_az_deg: float
) -> NDArray[np.float64]:
    """cos of the angle between the Sun and the panel normal, floored at 0 (local horizon frame, az from north)."""
    az = np.radians(np.asarray(sun_az_deg, dtype=np.float64))
    el = np.radians(np.asarray(sun_el_deg, dtype=np.float64))
    if panel == "horizontal":
        c = np.sin(el)
    elif panel == "tracking_vertical":
        c = np.cos(el)
    elif panel == "fixed_vertical":
        c = np.cos(el) * np.cos(az - math.radians(panel_az_deg))
    else:
        raise ValueError(f"unknown panel {panel!r}")
    return np.clip(c, 0.0, 1.0)


def soc_series(
    sun_fraction: NDArray[np.floating],
    sun_az_deg: NDArray[np.floating],
    sun_el_deg: NDArray[np.floating],
    params: EnergyParams,
    *,
    step_h: float,
    lit_threshold: float = 0.0,
) -> NDArray[np.float64]:
    """SOC as a fraction of capacity, one value per sample, starting full (sample 0 is the initial 100 %)."""
    frac = np.asarray(sun_fraction, dtype=np.float64)
    gen = params.array_w * frac * incidence_cos(sun_az_deg, sun_el_deg, params.panel, params.panel_az_deg)
    lit_w = params.dark_w if params.lit_w is None else params.lit_w
    load = np.where(frac > lit_threshold, lit_w, params.dark_w)
    soc = np.empty(len(frac), dtype=np.float64)
    wh = params.capacity_wh
    for i in range(len(frac)):
        soc[i] = wh / params.capacity_wh
        wh = min(params.capacity_wh, max(0.0, wh + (gen[i] * params.charge_eff - load[i]) * step_h))
    return soc
