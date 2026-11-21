"""Query precomputed 1 km cap sites and load tile masks. # per D-c159 D-f369"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from moonpark.horizon import polar_stereo_xy
from moonpark.providers import HorizonMask, Site

REPO = Path(__file__).resolve().parents[2]
CAP_DIR = REPO / "data" / "masks" / "cap_1km"
_INDEX = CAP_DIR / "index.parquet"
_TILES = CAP_DIR / "tiles"
SCHEDULE_VERSION = "D-f369-v1"


def _local_available() -> bool:
    return _INDEX.is_file() and _TILES.is_dir()


@lru_cache(maxsize=1)
def _remote():
    """Remote cap store when there is no local cap and a URL is configured. # per D-8c03"""
    from moonpark.horizon.remote import group

    return group("cap_1km")


def cap_source() -> str:
    """Where masks come from: ``local``, ``remote`` or ``none``."""
    if _local_available():
        return "local"
    r = _remote()
    return "remote" if r is not None and r.available() else "none"


def cap_index_available() -> bool:
    return cap_source() != "none"


def _file(rel: str) -> Path:
    """Local path of a cap file (``index.parquet`` or ``tiles/...``), fetching if remote."""
    if _local_available():
        return CAP_DIR / rel
    return _remote().get(rel)


@lru_cache(maxsize=1)
def _load_index():
    import pyarrow.parquet as pq

    # Keep as pyarrow Table (no pandas) so cap queries work with project deps only.
    return pq.read_table(_file("index.parquet"))


def sites_in_xy_rect(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> list[tuple[Site, float, float, int, int, int]]:
    """Return (site, x_m, y_m, tile_x, tile_y, row) snapped cells in stereo AABB. # per D-c159"""
    if not cap_index_available():
        return []
    table = _load_index()
    x0, x1 = sorted((float(x_min), float(x_max)))
    y0, y1 = sorted((float(y_min), float(y_max)))
    x_m = table.column("x_m").to_numpy()
    y_m = table.column("y_m").to_numpy()
    lat = table.column("lat").to_numpy()
    lon = table.column("lon").to_numpy()
    tile_x = table.column("tile_x").to_numpy()
    tile_y = table.column("tile_y").to_numpy()
    row = table.column("row").to_numpy()
    mask = (x_m >= x0) & (x_m <= x1) & (y_m >= y0) & (y_m <= y1)
    out: list[tuple[Site, float, float, int, int, int]] = []
    for i in np.flatnonzero(mask):
        site = Site(lat_deg=float(lat[i]), lon_deg=float(lon[i]), observer_height_m=2.0)
        out.append(
            (
                site,
                float(x_m[i]),
                float(y_m[i]),
                int(tile_x[i]),
                int(tile_y[i]),
                int(row[i]),
            )
        )
    return out


def sites_in_latlon_rect(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
) -> list[tuple[Site, float, float, int, int, int]]:
    """Return cells in lat/lon box via stereo AABB of corners (polar lon wrap soft). # per D-c159"""
    lo_lat, hi_lat = sorted((float(lat_min), float(lat_max)))
    lo_lon, hi_lon = sorted((float(lon_min), float(lon_max)))
    # Stereo AABB from corners (and mid-edges) so polar lon wrap is less wrong.
    corners = [
        (lo_lat, lo_lon),
        (lo_lat, hi_lon),
        (hi_lat, lo_lon),
        (hi_lat, hi_lon),
        ((lo_lat + hi_lat) / 2, lo_lon),
        ((lo_lat + hi_lat) / 2, hi_lon),
        (lo_lat, (lo_lon + hi_lon) / 2),
        (hi_lat, (lo_lon + hi_lon) / 2),
    ]
    xs, ys = zip(*(polar_stereo_xy(la, lo) for la, lo in corners))
    hit = sites_in_xy_rect(min(xs), max(xs), min(ys), max(ys))
    width = hi_lon - lo_lon
    if width >= 360.0:
        in_lon = lambda lon: True  # noqa: E731
    else:
        in_lon = lambda lon: (lon - lo_lon) % 360.0 <= width  # noqa: E731  (handles 0/360 wrap)
    return [c for c in hit if lo_lat <= c[0].lat_deg <= hi_lat and in_lon(c[0].lon_deg)]


@lru_cache(maxsize=64)
def _tile_elev(tx: int, ty: int) -> np.ndarray:
    return np.load(_file(f"tiles/t{tx}_{ty}.npy"))


@lru_cache(maxsize=64)
def _tile_meta(tx: int, ty: int) -> dict:
    import json

    return json.loads(_file(f"tiles/t{tx}_{ty}.json").read_text(encoding="utf-8"))


def nearest_cap_mask(site: Site, max_dist_m: float = 1000.0) -> HorizonMask | None:
    """Mask of the closest 1 km cap cell within ``max_dist_m`` of ``site`` (None if none).

    Used when no DEMs are on the machine: the site snaps to its cell (<= ~0.7 km off).
    """
    if not cap_index_available():
        return None
    x, y = polar_stereo_xy(site.lat_deg, site.lon_deg)
    cells = sites_in_xy_rect(x - max_dist_m, x + max_dist_m, y - max_dist_m, y + max_dist_m)
    if not cells:
        return None
    _, cx, cy, tx, ty, row = min(cells, key=lambda c: (c[1] - x) ** 2 + (c[2] - y) ** 2)
    if ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5 > max_dist_m:
        return None
    return mask_from_cap_tile(tx, ty, row)


def mask_from_cap_tile(tile_x: int, tile_y: int, row: int) -> HorizonMask:
    elev = _tile_elev(tile_x, tile_y)[int(row)]
    meta = _tile_meta(tile_x, tile_y)
    s = meta["sites"][int(row)]
    return HorizonMask(
        elevation_deg=np.asarray(elev, dtype=np.float32),
        x_m=float(s["x_m"]),
        y_m=float(s["y_m"]),
        lat=float(s["lat"]),
        lon=float(s["lon"]),
        h0_m=float(s["h0_m"]),
        observer_height_m=float(meta.get("observer_height_m", 2.0)),
        schedule_version=str(meta.get("schedule_version", SCHEDULE_VERSION)),
        dem_ids=tuple(),
        fill_stats=s.get("fill"),  # absent in tiles written before D-d90c
    )
