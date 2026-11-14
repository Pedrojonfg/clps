"""Polar climatology temperature (D-41a2, D-affb)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from lunar_eval.hazards.fill import fill_nodata_quadrant_idw
from lunar_eval.hazards.lst import lst_bin_index, local_solar_time_h_from_utc


@dataclass
class ClimatologyTable:
    """lst_bin -> kelvin; labels as provenance only."""

    bins_k: dict[int, float]
    season: str = "unspecified"
    product: str = "deferred_pds_pcp"

    def at_lst(self, lst_h: float) -> tuple[float | None, dict]:
        idx = lst_bin_index(lst_h)
        if idx not in self.bins_k:
            return None, {"lst_bin": idx, "season": self.season, "product": self.product, "status": "missing_bin"}
        return self.bins_k[idx], {
            "lst_bin": idx,
            "bin_h": 0.25,
            "season": self.season,
            "product": self.product,
            "quantity": "polar_seasonal_local_time_climatology",
        }


@dataclass
class RasterClimatology:
    """2-D grid indexed by lst column (centre row) with optional nodata fill."""

    values: NDArray[np.float64]
    season: str
    product: str = "deferred_pds_pcp"

    def at_site_time(self, time_utc: np.datetime64, lon_deg: float) -> tuple[float | None, dict]:
        lst = local_solar_time_h_from_utc(time_utc, lon_deg)
        col = lst_bin_index(lst)
        if col >= self.values.shape[1]:
            col = col % self.values.shape[1]
        win = self.values[:, max(0, col - 2) : col + 3]
        if win.size == 0:
            return None, {"status": "empty_window"}
        centre = win[:, min(2, win.shape[1] - 1)]
        val, fill_meta = fill_nodata_quadrant_idw(centre.reshape(-1, 1))
        meta = {
            "lst_h": lst,
            "lst_bin": col,
            "season": self.season,
            "product": self.product,
            "quantity": "polar_seasonal_local_time_climatology",
            **fill_meta,
        }
        return val, meta