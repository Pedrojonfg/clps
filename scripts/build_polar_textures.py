"""Build south-polar hillshade textures for the S9 region map (per D-4126: NASA-derived texture).

Source: LOLA south-pole DEMs (NASA PGDA), polar stereographic, already under data/dem/.
Output: web/assets/southpole_80s.jpg (80 m DEM -> 160 m/px, +-304 km) and southpole_87s.jpg
(centre +-100 km of the 20 m DEM -> 50 m/px). web/map.js places them by those stereographic half-widths.

    python scripts/build_polar_textures.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

REPO = Path(__file__).resolve().parents[1]
JOBS = [
    # (source DEM, output, output px, half-width in metres or None for the full raster)
    ("LDEM_80S_80MPP_ADJ.TIF", "southpole_80s.jpg", 3800, None),
    ("LDEM_80S_20MPP_ADJ.TIF", "southpole_87s.jpg", 4000, 100_000.0),
]


def hillshade(z: np.ndarray, px_m: float, az_deg: float, alt_deg: float, exag: float) -> np.ndarray:
    # Row 0 is +y (north-up image): flip the row gradient so dy is along +y.
    dzdy, dzdx = np.gradient(z * exag, px_m)
    dzdy = -dzdy
    az, alt = np.radians(az_deg), np.radians(alt_deg)
    lx, ly, lz = np.sin(az) * np.cos(alt), np.cos(az) * np.cos(alt), np.sin(alt)
    norm = np.sqrt(dzdx**2 + dzdy**2 + 1.0)
    return np.clip((-dzdx * lx - dzdy * ly + lz) / norm, 0.0, 1.0)


def main() -> None:
    for src_name, out_name, size, half_m in JOBS:
        with rasterio.open(REPO / "data" / "dem" / src_name) as src:
            full_half_m = abs(src.transform.a) * src.width / 2.0
            half_m = half_m or full_half_m
            window = from_bounds(-half_m, -half_m, half_m, half_m, src.transform)
            z = src.read(
                1, window=window, out_shape=(size, size), resampling=Resampling.average
            ).astype(np.float64)
            px_m = 2.0 * half_m / size
        z = np.where(np.isfinite(z), z, np.nanmedian(z))
        # Two light directions so no slope family goes fully black; low sun suits polar relief.
        shade = 0.65 * hillshade(z, px_m, 315, 35, 2.0) + 0.35 * hillshade(z, px_m, 45, 50, 2.0)
        img = np.clip(30 + 215 * shade**0.9, 0, 255).astype(np.uint8)
        out = REPO / "web" / "assets" / out_name
        Image.fromarray(img, mode="L").save(out, quality=82, optimize=True)
        print(out, img.shape, f"{px_m:.0f} m/px", f"{out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
