"""Windowed DEM sampling. # per D-20261114-pj-f369 D-20261118-pj-d90c"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import map_coordinates, maximum_filter, maximum_filter1d

EDGE_HALF_PX = 5  # out-of-coverage samples: max over +-5 px of edge around the nearest edge pixel # per D-d90c


class Grid:
    def __init__(self, z: NDArray[np.float32], x0: float, y0: float, res: float, n_filled: int = 0):
        self.Z = z
        self.x0 = x0
        self.y0 = y0
        self.res = res
        self.n_filled = int(n_filled)  # pixels filled by load_tif # per D-d90c
        self._edge = None
        self.source = self  # coarsened copies point at the loaded grid, so fills are counted once

    def sample(self, x: NDArray, y: NDArray) -> NDArray:
        return self.sample_with_stats(x, y)[0]

    def sample_with_stats(self, x: NDArray, y: NDArray) -> tuple[NDArray, int]:
        """Bilinear inside the coverage; outside, the max of the nearest edge segment. # per D-d90c"""
        x, y = np.asarray(x), np.asarray(y)
        col = ((x - self.x0) / self.res - 0.5).ravel()
        row = ((self.y0 - y) / self.res - 0.5).ravel()
        h, w = self.Z.shape
        out = (col < -0.5) | (col > w - 0.5) | (row < -0.5) | (row > h - 0.5)
        v = map_coordinates(self.Z, [row, col], order=1, mode="nearest")
        n_out = int(out.sum())
        if n_out:
            r = np.clip(np.rint(row[out]), 0, h - 1).astype(np.intp)
            c = np.clip(np.rint(col[out]), 0, w - 1).astype(np.intp)
            v[out] = self._edge_max(r, c)
        return v.reshape(x.shape), n_out

    def _edge_max(self, r: NDArray, c: NDArray) -> NDArray:
        z = self.Z
        h, w = z.shape
        if h < 2 or w < 2:
            return maximum_filter(z, size=2 * EDGE_HALF_PX + 1, mode="nearest")[r, c]
        if self._edge is None:
            # Perimeter walked clockwise from (0,0); sliding max wraps around corners.
            ring = np.concatenate([z[0, :], z[1:, -1], z[-1, -2::-1], z[-2:0:-1, 0]])
            self._edge = maximum_filter1d(ring, 2 * EDGE_HALF_PX + 1, mode="wrap")
        idx = np.select(
            [r == 0, c == w - 1, r == h - 1],
            [c, (w - 1) + r, (w - 1) + (h - 1) + (w - 1 - c)],
            2 * (w - 1) + (h - 1) + (h - 1 - r),
        )
        return self._edge[idx]

    def coarsen(self, factor: int) -> Grid:
        h = (self.Z.shape[0] // factor) * factor
        w = (self.Z.shape[1] // factor) * factor
        z = self.Z[:h, :w].reshape(h // factor, factor, w // factor, factor).mean(axis=(1, 3)).astype(np.float32)
        g = Grid(z, self.x0, self.y0, self.res * factor, self.n_filled)
        g.source = self.source
        return g


def fill_holes_max(z: NDArray[np.float32]) -> tuple[NDArray[np.float32], int]:
    """Fill non-finite pixels with the max of their finite 8-neighbours, ring by ring. # per D-d90c

    Each ring only sees pixels finite at the start of that ring (order independent).
    Raises ValueError when a hole has no finite pixel to grow from.
    """
    finite = np.isfinite(z)
    n = int(z.size - finite.sum())
    if n == 0:
        return z, 0
    z = z.copy()
    while not finite.all():
        nb = maximum_filter(np.where(finite, z, -np.inf), size=3, mode="constant", cval=-np.inf)
        new = ~finite & np.isfinite(nb)
        if not new.any():
            raise ValueError("DEM hole has no finite neighbour to fill from")
        z[new] = nb[new]
        finite |= new
    return z, n


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
        nodata = src.nodata
    if nodata is not None and np.isfinite(nodata):
        z[z == np.float32(nodata)] = np.nan
    z, n_filled = fill_holes_max(z)
    return Grid(z, float(tr.c), float(tr.f), float(tr.a), n_filled)
