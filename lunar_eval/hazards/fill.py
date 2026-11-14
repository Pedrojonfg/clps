"""Nodata fill (D-affb). Four-quadrant inverse distance, GDAL-style defaults."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

G_M = 1.62
FILL_MAX_DISTANCE_PX = 100
FILL_SMOOTHING_ITERATIONS = 0


def _quadrant_masks(rows: int, cols: int, cy: int, cx: int) -> tuple[NDArray[np.bool_], ...]:
    yy, xx = np.ogrid[:rows, :cols]
    q0 = (yy <= cy) & (xx <= cx)
    q1 = (yy <= cy) & (xx > cx)
    q2 = (yy > cy) & (xx > cx)
    q3 = (yy > cy) & (xx <= cx)
    return q0, q1, q2, q3


def fill_nodata_quadrant_idw(
    grid: NDArray[np.float64],
    *,
    max_distance: int = FILL_MAX_DISTANCE_PX,
) -> tuple[float | None, dict]:
    """Value at the centre cell; None if no valid pixel within max_distance."""
    rows, cols = grid.shape
    cy, cx = rows // 2, cols // 2
    valid = np.isfinite(grid)
    if valid[cy, cx]:
        return float(grid[cy, cx]), {"fill": "none"}

    quarters = _quadrant_masks(rows, cols, cy, cx)
    picks: list[tuple[float, float]] = []
    for qmask in quarters:
        dists: list[tuple[float, int, int]] = []
        ys, xs = np.where(valid & qmask)
        for y, x in zip(ys, xs, strict=False):
            d = float(np.hypot(y - cy, x - cx))
            if d <= max_distance and d > 0:
                dists.append((d, y, x))
        if not dists:
            continue
        d, y, x = min(dists, key=lambda t: t[0])
        picks.append((float(grid[y, x]), d))

    if not picks:
        return None, {"fill": "none", "max_distance_px": max_distance}

    weights = [1.0 / d for _, d in picks]
    wsum = sum(weights)
    value = sum(v * w for (v, _), w in zip(picks, weights, strict=True)) / wsum
    return value, {
        "fill": "four_quadrant_inverse_distance",
        "max_distance_px": max_distance,
        "smoothing_iterations": FILL_SMOOTHING_ITERATIONS,
        "n_quadrants_used": len(picks),
    }