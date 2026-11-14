"""Sample PGDA GeoTIFFs at a site."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from lunar_eval.horizon import polar_stereo_xy


def sample_geotiff(path: Path, lat_deg: float, lon_deg: float) -> float | None:
    import rasterio

    x, y = polar_stereo_xy(lat_deg, lon_deg)
    with rasterio.open(path) as src:
        try:
            row, col = src.index(x, y)
        except Exception:
            return None
        if row < 0 or col < 0 or row >= src.height or col >= src.width:
            return None
        band = src.read(1, window=((row, row + 1), (col, col + 1)))
        val = float(band[0, 0])
        nodata = src.nodata
        if nodata is not None and val == float(nodata):
            return None
        if not np.isfinite(val):
            return None
        return val


def sample_window(path: Path, lat_deg: float, lon_deg: float, *, win_px: int = 5) -> np.ndarray | None:
    import rasterio

    x, y = polar_stereo_xy(lat_deg, lon_deg)
    half = win_px // 2
    with rasterio.open(path) as src:
        try:
            row, col = src.index(x, y)
        except Exception:
            return None
        row0 = max(0, row - half)
        col0 = max(0, col - half)
        row1 = min(src.height, row0 + win_px)
        col1 = min(src.width, col0 + win_px)
        band = src.read(1, window=((row0, row1), (col0, col1))).astype(np.float64)
        nodata = src.nodata
        if nodata is not None:
            band = np.where(band == float(nodata), np.nan, band)
        return band