"""Cache horizon masks under data/masks/. # per D-20261114-pj-aa58 D-20261114-pj-f369"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from moonpark.horizon import mask
from moonpark.horizon.dem_schedule import mask_schedule_for_site
from moonpark.providers import HorizonMask, Site

REPO = Path(__file__).resolve().parents[2]
MASK_DIR = REPO / "data" / "masks"
SITE5 = REPO / "data" / "dem" / "Site01_final_adj_5mpp_surf.tif"


def _cache_key(site: Site) -> str:
    return f"{site.lat_deg:.5f}_{site.lon_deg:.5f}_oh{site.observer_height_m:.1f}"


def _paths(key: str) -> tuple[Path, Path]:
    return MASK_DIR / f"{key}.npy", MASK_DIR / f"{key}.json"


def load_cached_mask(site: Site) -> HorizonMask | None:
    key = _cache_key(site)
    npy, meta = _paths(key)
    if not npy.is_file() or not meta.is_file():
        return None
    elev = np.load(npy)
    info = json.loads(meta.read_text(encoding="utf-8"))
    return HorizonMask(
        elevation_deg=elev.astype(np.float32),
        x_m=float(info["x_m"]),
        y_m=float(info["y_m"]),
        lat=float(info["lat"]),
        lon=float(info["lon"]),
        h0_m=float(info["h0_m"]),
        observer_height_m=float(info["observer_height_m"]),
        schedule_version=str(info["schedule_version"]),
        dem_ids=tuple(info.get("dem_ids", ())),
    )


def save_mask(site: Site, horizon: HorizonMask) -> None:
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(site)
    npy, meta = _paths(key)
    np.save(npy, horizon.elevation_deg)
    meta.write_text(
        json.dumps(
            {
                "x_m": horizon.x_m,
                "y_m": horizon.y_m,
                "lat": horizon.lat,
                "lon": horizon.lon,
                "h0_m": horizon.h0_m,
                "observer_height_m": horizon.observer_height_m,
                "schedule_version": horizon.schedule_version,
                "dem_ids": list(horizon.dem_ids),
            },
            indent=0,
        ),
        encoding="utf-8",
    )


def mask_for_site(site: Site, *, use_site01_5m: bool = False) -> HorizonMask:
    """Load mask from cache or compute and persist."""
    cached = load_cached_mask(site)
    if cached is not None:
        return cached
    site5 = SITE5 if use_site01_5m or (
        abs(site.lat_deg - (-89.46316)) < 0.01 and abs(site.lon_deg - 222.51045) < 0.01
    ) else None
    sched = mask_schedule_for_site(site, site5)
    if sched is None:
        # No DEMs on this machine (the normal client case): snap to the 1 km cap cell. # per D-8c03
        from moonpark.horizon.cap_index import nearest_cap_mask

        snapped = nearest_cap_mask(site)
        if snapped is not None:
            return snapped
        raise FileNotFoundError(
            "No DEM tiles available and the site is outside the precomputed 1 km cap"
        )
    horizon = mask(site, schedule=sched)
    save_mask(site, horizon)
    return horizon