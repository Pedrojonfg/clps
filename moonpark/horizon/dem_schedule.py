"""DEM distance schedule for mask(site). # per D-20261114-pj-f369"""

from __future__ import annotations

from pathlib import Path

from moonpark.horizon import load_tif, polar_stereo_xy
from moonpark.providers import Site

REPO = Path(__file__).resolve().parents[2]
DEM = REPO / "data" / "dem"


def mask_schedule_for_site(site: Site, site5_tif: Path | None = None):
    """Return a schedule list or None if no DEMs are available."""
    g80 = DEM / "LDEM_80S_80MPP_ADJ.TIF"
    g240 = DEM / "LDEM_60S_240MPP_ADJ.TIF"
    x, y = polar_stereo_xy(site.lat_deg, site.lon_deg)

    if site5_tif and site5_tif.is_file():
        g5 = load_tif(site5_tif)
        if g80.is_file() and g240.is_file():
            g80w = load_tif(g80, x, y, 30_000.0)
            g240w = load_tif(g240, x, y, 260_000.0)
            return [
                (0.0, 250.0, g5),
                (250.0, 1000.0, g5.coarsen(4)),
                (1000.0, 2000.0, g5.coarsen(8)),
                (2000.0, 5000.0, g80w),
                (5000.0, 25000.0, g80w),
                (25000.0, 250000.0, g240w),
            ]
        return [(5.0, 4000.0, g5)]

    if g80.is_file() and g240.is_file():
        g80w = load_tif(g80, x, y, 30_000.0)
        g240w = load_tif(g240, x, y, 260_000.0)
        return [
            (2000.0, 5000.0, g80w),
            (5000.0, 25000.0, g80w),
            (25000.0, 250000.0, g240w),
        ]
    return None