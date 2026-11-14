"""Windowed DEM sampling. # per D-20261114-pj-f369"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import map_coordinates


class Grid:
    def __init__(self, z: NDArray[np.float32], x0: float, y0: float, res: float):
        self.Z = z
        self.x0 = x0
        self.y0 = y0
        self.res = res

    def sample(self, x: NDArray, y: NDArray) -> NDArray:
        col = (x - self.x0) / self.res - 0.5
        row = (self.y0 - y) / self.res - 0.5
        return map_coordinates(self.Z, [row.ravel(), col.ravel()], order=1, mode="nearest").reshape(x.shape)

    def coarsen(self, factor: int) -> Grid:
        h = (self.Z.shape[0] // factor) * factor
        w = (self.Z.shape[1] // factor) * factor
        z = self.Z[:h, :w].reshape(h // factor, factor, w // factor, factor).mean(axis=(1, 3)).astype(np.float32)
        return Grid(z, self.x0, self.y0, self.res * factor)


def load_tif(path: str | Path, x: float | None = None, y: float | None = None, radius_m: float | None = None) -> Grid:
    import rasterio
    from rasterio.windows import from_bounds

    with rasterio.open(path) as src:
        if x is None or y is None or radius_m is None:
            z = src.read(1).astype(np.float32)
            tr = src.transform
        else:
            window = from_bounds(x - radius_m, y - radius_m, x + radius_m, y + radius_m, src.transform)
            window = window.round_offsets().round_lengths()
            z = src.read(1, window=window).astype(np.float32)
            tr = src.window_transform(window)
    finite = np.isfinite(z)
    if not finite.all():
        z = np.where(finite, z, np.nanmean(z)).astype(np.float32)
    return Grid(z, float(tr.c), float(tr.f), float(tr.a))
