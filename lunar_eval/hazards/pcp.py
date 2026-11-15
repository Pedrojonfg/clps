"""Diviner Polar Cumulative Product climatology (D-41a2, D-affb)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import cKDTree

from lunar_eval.hazards.lst import lst_bin_index, local_solar_time_h_from_utc
from lunar_eval.horizon.mask import R_M

PRODUCT_ID = "urn:nasa:pds:lro_diviner_derived1:data_derived_pcp"
PIXEL_M = 240.0
MAX_FILL_PX = 100  # per D-affb


def default_pcp_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "hazards" / "pcp"


def _south_season(time_utc: np.datetime64) -> str:
    """Williams et al. 2019: south summer when subsolar latitude < 0."""
    try:
        import spiceypy as spice
        from lunar_eval.ephemeris.spice import KERNEL_DIR, _furnsh

        _furnsh(KERNEL_DIR)
        iso = str(np.datetime64(time_utc, "s")).replace("T", " ")
        et = spice.utc2et(iso + " UTC")
        pos, _ = spice.spkpos("SUN", et, "MOON_ME", "LT+S", "MOON")
        r = math.sqrt(float(pos[0]) ** 2 + float(pos[1]) ** 2 + float(pos[2]) ** 2)
        lat = math.degrees(math.asin(float(pos[2]) / r))
        return "summer" if lat < 0.0 else "winter"
    except Exception:
        return "summer"


@dataclass
class _BinCache:
    tree: cKDTree
    tbol: NDArray[np.float32]


@dataclass
class PolarPcpClimatology:
    """Spatial LST-bin lookup against converted PCP npz files."""

    root: Path = field(default_factory=default_pcp_root)
    product: str = PRODUCT_ID
    _cache: dict[tuple[str, int], _BinCache] = field(default_factory=dict, repr=False)

    def available(self) -> bool:
        summer = self.root / "summer"
        winter = self.root / "winter"
        return any(p.is_dir() and any(p.glob("ltim*.npz")) for p in (summer, winter))

    def _load_bin(self, season: str, bin_1based: int) -> _BinCache | None:
        key = (season, bin_1based)
        if key in self._cache:
            return self._cache[key]
        path = self.root / season / f"ltim{bin_1based:02d}.npz"
        if not path.is_file():
            alt = "winter" if season == "summer" else "summer"
            path = self.root / alt / f"ltim{bin_1based:02d}.npz"
            if not path.is_file():
                return None
            season = alt
            key = (season, bin_1based)
        with np.load(path) as z:
            x = np.asarray(z["x"], dtype=np.float64)
            y = np.asarray(z["y"], dtype=np.float64)
            tbol = np.asarray(z["tbol"], dtype=np.float32)
        cache = _BinCache(tree=cKDTree(np.column_stack([x, y])), tbol=tbol)
        self._cache[key] = cache
        return cache

    def at_site_time(
        self, time_utc: np.datetime64, lat_deg: float, lon_deg: float
    ) -> tuple[float | None, dict]:
        from lunar_eval.horizon import polar_stereo_xy

        season = _south_season(time_utc)
        lst = local_solar_time_h_from_utc(time_utc, lon_deg)
        bin0 = lst_bin_index(lst)
        bin_1 = bin0 + 1
        meta: dict = {
            "lst_h": lst,
            "lst_bin": bin0,
            "season": season,
            "product": self.product,
            "quantity": "polar_seasonal_local_time_climatology",
            "pixel_m": PIXEL_M,
        }
        cache = self._load_bin(season, bin_1)
        if cache is None:
            meta["status"] = "missing_pcp_bin"
            return None, meta

        x_m, y_m = polar_stereo_xy(lat_deg, lon_deg)
        xn, yn = x_m / R_M, y_m / R_M
        step = PIXEL_M / R_M
        max_r = MAX_FILL_PX * step

        dist, idx = cache.tree.query([xn, yn], k=1)
        dist = float(dist)
        if dist <= step * 0.75:
            meta["fill"] = "none"
            return float(cache.tbol[int(idx)]), meta

        # Four-quadrant inverse-distance among points inside the search radius.
        idxs = cache.tree.query_ball_point([xn, yn], r=max_r)
        if not idxs:
            meta["fill"] = "none"
            meta["status"] = "no_points_in_radius"
            return None, meta
        pts = cache.tree.data[idxs]
        temps = cache.tbol[idxs]
        dx = pts[:, 0] - xn
        dy = pts[:, 1] - yn
        quarters = (
            (dy <= 0) & (dx <= 0),
            (dy <= 0) & (dx > 0),
            (dy > 0) & (dx > 0),
            (dy > 0) & (dx <= 0),
        )
        picks: list[tuple[float, float]] = []
        for mask in quarters:
            if not np.any(mask):
                continue
            d = np.hypot(dx[mask], dy[mask])
            j = int(np.argmin(d))
            dj = float(d[j])
            if dj <= 0:
                meta["fill"] = "none"
                return float(temps[mask][j]), meta
            picks.append((float(temps[mask][j]), dj))
        if not picks:
            meta["fill"] = "none"
            meta["status"] = "unfilled"
            return None, meta
        wsum = sum(1.0 / d for _, d in picks)
        value = sum(v / d for v, d in picks) / wsum
        meta.update(
            {
                "fill": "four_quadrant_inverse_distance",
                "max_distance_px": MAX_FILL_PX,
                "n_quadrants_used": len(picks),
            }
        )
        return float(value), meta
