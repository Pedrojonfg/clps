"""Query precomputed 1 km cap sites and load tile masks. # per D-c159 D-f369"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from lunar_eval.horizon import polar_stereo_xy
from lunar_eval.providers import HorizonMask, Site

REPO = Path(__file__).resolve().parents[2]
CAP_DIR = REPO / "data" / "masks" / "cap_1km"
_INDEX = CAP_DIR / "index.parquet"
_TILES = CAP_DIR / "tiles"
SCHEDULE_VERSION = "D-f369-v1"


def cap_index_available() -> bool:
    return _INDEX.is_file() and _TILES.is_dir()


@lru_cache(maxsize=1)
def _load_index():
    import pyarrow.parquet as pq

    return pq.read_table(_INDEX).to_pandas()


def sites_in_latlon_rect(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
) -> list[tuple[Site, float, float, int, int, int]]:
    """Return (site, x_m, y_m, tile_x, tile_y, row) snapped cells in bbox. # per D-c159"""
    if not cap_index_available():
        return []
    df = _load_index()
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
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    hit = df[(df["x_m"] >= x0) & (df["x_m"] <= x1) & (df["y_m"] >= y0) & (df["y_m"] <= y1)]
    hit = hit[(hit["lat"] >= lo_lat) & (hit["lat"] <= hi_lat)]
    out: list[tuple[Site, float, float, int, int, int]] = []
    for r in hit.itertuples(index=False):
        site = Site(lat_deg=float(r.lat), lon_deg=float(r.lon), observer_height_m=2.0)
        out.append(
            (
                site,
                float(r.x_m),
                float(r.y_m),
                int(r.tile_x),
                int(r.tile_y),
                int(r.row),
            )
        )
    return out


@lru_cache(maxsize=64)
def _tile_elev(tx: int, ty: int) -> np.ndarray:
    path = _TILES / f"t{tx}_{ty}.npy"
    return np.load(path)


@lru_cache(maxsize=64)
def _tile_meta(tx: int, ty: int) -> dict:
    import json

    return json.loads((_TILES / f"t{tx}_{ty}.json").read_text(encoding="utf-8"))


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
    )
