"""Diviner Polar Cumulative Product climatology (D-41a2, D-affb)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from lunar_eval.hazards.lst import lst_bin_index, local_solar_time_h_from_utc
from lunar_eval.horizon.mask import R_M

PRODUCT_ID = "urn:nasa:pds:lro_diviner_derived1:data_derived_pcp"
PIXEL_M = 240.0
MAX_FILL_PX = 100  # per D-affb


def default_pcp_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "hazards" / "pcp"


_SEASON_BY_DAY: dict[str, str] = {}


def _south_season(time_utc: np.datetime64) -> str:
    """Williams et al. 2019: south summer when subsolar latitude < 0."""
    day = str(np.datetime64(time_utc, "D"))
    cached = _SEASON_BY_DAY.get(day)
    if cached is not None:
        return cached
    try:
        import spiceypy as spice
        from lunar_eval.ephemeris.spice import KERNEL_DIR, _furnsh

        _furnsh(KERNEL_DIR)
        iso = str(np.datetime64(time_utc, "s")).replace("T", " ")
        et = spice.utc2et(iso + " UTC")
        pos, _ = spice.spkpos("SUN", et, "MOON_ME", "LT+S", "MOON")
        r = math.sqrt(float(pos[0]) ** 2 + float(pos[1]) ** 2 + float(pos[2]) ** 2)
        lat = math.degrees(math.asin(float(pos[2]) / r))
        season = "summer" if lat < 0.0 else "winter"
    except Exception:
        season = "summer"
    _SEASON_BY_DAY[day] = season
    return season


@dataclass
class _BinCache:
    """Raw stereo points (normalized by R_M). No KDTree — build was ~4s/bin on ~3M pts."""

    x: NDArray[np.float64]
    y: NDArray[np.float64]
    tbol: NDArray[np.float32]


SPREAD_RADIUS_M = 300.0  # ~ the 3x3 pixel neighbourhood of a 240 m pixel (1 km mixed lit and shaded terrain, ~100 K); spatial spread of the climatology around the site (D-20261117-pj-e3a7)


def spread_k(
    cache: _BinCache,
    neighbours: list[_BinCache],
    xn: float,
    yn: float,
    *,
    radius_m: float = SPREAD_RADIUS_M,
) -> float | None:
    """Spread of the climatology around a site, in K: spatial std of the pixels within `radius_m` and the mean
    change to the adjacent local-time bins at the nearest pixel, in quadrature. It is variability of the
    climatology (terrain and timing), not instrument error. # per D-20261117-pj-e3a7 (temperature, v1 only)"""
    dx, dy = cache.x - xn, cache.y - yn
    d2 = dx * dx + dy * dy
    r = radius_m / R_M
    near = d2 <= r * r
    sigma_space = float(np.std(cache.tbol[near])) if int(near.sum()) >= 4 else 0.0
    i0 = int(np.argmin(d2))
    t0 = float(cache.tbol[i0])
    diffs: list[float] = []
    for nb in neighbours:
        j = int(np.argmin((nb.x - xn) ** 2 + (nb.y - yn) ** 2))
        diffs.append(abs(float(nb.tbol[j]) - t0))
    sigma_time = float(np.mean(diffs)) if diffs else 0.0
    if int(near.sum()) < 4 and not diffs:
        return None
    return math.hypot(sigma_space, sigma_time)


@dataclass
class PolarPcpClimatology:
    """Spatial LST-bin lookup against converted PCP npz files."""

    root: Path = field(default_factory=default_pcp_root)
    product: str = PRODUCT_ID
    _cache: dict[tuple[str, int], _BinCache] = field(default_factory=dict, repr=False)
    _value_cache: dict[tuple[str, int, float, float], tuple[float | None, dict]] = field(
        default_factory=dict, repr=False
    )

    def _is_default_root(self) -> bool:
        return self.root == default_pcp_root()

    def _bin_path(self, season: str, bin_1based: int) -> Path | None:
        name = f"ltim{bin_1based:02d}.npz"
        local = self.root / season / name
        if local.is_file():
            return local
        if self._is_default_root():
            from lunar_eval.horizon.remote import locate

            return locate(f"hazards/pcp/{season}/{name}")  # per D-8c03: bins come from the store
        return None

    def available(self) -> bool:
        summer = self.root / "summer"
        winter = self.root / "winter"
        if any(p.is_dir() and any(p.glob("ltim*.npz")) for p in (summer, winter)):
            return True
        if self._is_default_root():
            from lunar_eval.horizon.remote import remote_has_prefix

            return remote_has_prefix("hazards/pcp/")
        return False

    def preload(self, times: NDArray[np.datetime64], lon_deg: float) -> None:
        """Load unique season/LST bins for a window (threaded) before hourly lookups."""
        from concurrent.futures import ThreadPoolExecutor

        keys: set[tuple[str, int]] = set()
        for time_utc in np.asarray(times):
            season = _south_season(time_utc)
            bin_1 = lst_bin_index(local_solar_time_h_from_utc(time_utc, lon_deg)) + 1
            keys.add((season, bin_1))
        missing = [k for k in keys if k not in self._cache]
        if not missing:
            return
        workers = min(8, len(missing))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(lambda k: self._load_bin(k[0], k[1]), missing))

    def _load_bin(self, season: str, bin_1based: int) -> _BinCache | None:
        key = (season, bin_1based)
        if key in self._cache:
            return self._cache[key]
        path = self._bin_path(season, bin_1based)
        if path is None:
            alt = "winter" if season == "summer" else "summer"
            path = self._bin_path(alt, bin_1based)
            if path is None:
                return None
            season = alt
            key = (season, bin_1based)
        with np.load(path) as z:
            x = np.asarray(z["x"], dtype=np.float64)
            y = np.asarray(z["y"], dtype=np.float64)
            tbol = np.asarray(z["tbol"], dtype=np.float32)
        cache = _BinCache(x=x, y=y, tbol=tbol)
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
        value_key = (season, bin_1, float(lat_deg), float(lon_deg))
        hit = self._value_cache.get(value_key)
        if hit is not None:
            temp, base_meta = hit
            meta = {
                **base_meta,
                "lst_h": lst,
                "lst_bin": bin0,
                "season": season,
            }
            return temp, meta

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
            self._value_cache[value_key] = (None, dict(meta))
            return None, meta

        x_m, y_m = polar_stereo_xy(lat_deg, lon_deg)
        xn, yn = x_m / R_M, y_m / R_M
        step = PIXEL_M / R_M
        max_r = MAX_FILL_PX * step

        dx = cache.x - xn
        dy = cache.y - yn
        d2 = dx * dx + dy * dy
        idx = int(np.argmin(d2))
        dist = float(math.sqrt(float(d2[idx])))
        if dist <= step * 0.75:
            meta["fill"] = "none"
            temp = float(cache.tbol[idx])
            self._value_cache[value_key] = (temp, dict(meta))
            return temp, meta

        # Four-quadrant inverse-distance among points inside the search radius.
        near = d2 <= max_r * max_r
        if not np.any(near):
            meta["fill"] = "none"
            meta["status"] = "no_points_in_radius"
            self._value_cache[value_key] = (None, dict(meta))
            return None, meta
        dx_n = dx[near]
        dy_n = dy[near]
        temps = cache.tbol[near]
        quarters = (
            (dy_n <= 0) & (dx_n <= 0),
            (dy_n <= 0) & (dx_n > 0),
            (dy_n > 0) & (dx_n > 0),
            (dy_n > 0) & (dx_n <= 0),
        )
        picks: list[tuple[float, float]] = []
        for mask in quarters:
            if not np.any(mask):
                continue
            d = np.hypot(dx_n[mask], dy_n[mask])
            j = int(np.argmin(d))
            dj = float(d[j])
            if dj <= 0:
                meta["fill"] = "none"
                temp = float(temps[mask][j])
                self._value_cache[value_key] = (temp, dict(meta))
                return temp, meta
            picks.append((float(temps[mask][j]), dj))
        if not picks:
            meta["fill"] = "none"
            meta["status"] = "unfilled"
            self._value_cache[value_key] = (None, dict(meta))
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
        temp = float(value)
        self._value_cache[value_key] = (temp, dict(meta))
        return temp, meta

    def sigma_at_site_time(self, time_utc: np.datetime64, lat_deg: float, lon_deg: float) -> float | None:
        """Spread (K) of the climatology at a site and time; None when the bin is not available."""
        from lunar_eval.horizon import polar_stereo_xy

        season = _south_season(time_utc)
        bin0 = lst_bin_index(local_solar_time_h_from_utc(time_utc, lon_deg))
        cache = self._load_bin(season, bin0 + 1)
        if cache is None:
            return None
        x_m, y_m = polar_stereo_xy(lat_deg, lon_deg)
        nbs = [
            c
            for c in (
                self._load_bin(season, (bin0 - 1) % 96 + 1),
                self._load_bin(season, (bin0 + 1) % 96 + 1),
            )
            if c is not None
        ]
        return spread_k(cache, nbs, x_m / R_M, y_m / R_M)
