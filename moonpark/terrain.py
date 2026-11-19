"""Ring-mesh terrain around a site, built from our own LOLA DEMs (first-person 3D view).

The mesh is polar around the observer: `naz` azimuths (geographic, clockwise from north) times
rings whose radius grows geometrically, so detail is finest under the eye and coarsens with
distance. Heights are relative to the tangent plane at the site (the Moon's curvature drop is
already removed), so the client can place them straight into a local east-north-up frame.
"""

from __future__ import annotations

import base64
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from moonpark import relief_tiles
from moonpark.horizon import Grid, load_tif, polar_stereo_xy, remote
from moonpark.horizon.mask import R_M

REPO = Path(__file__).resolve().parents[1]
DEM = REPO / "data" / "dem"

R_MIN_M = 4.0
R_MAX_M = 30_000.0
RING_RATIO = 1.025
NAZ = 360
# A DEM window is res * WINDOW_PX across the radius: 5 m -> 7.5 km, 20 m -> 30 km. Keeps memory bounded.
WINDOW_PX = 1500
MIN_WINDOW_M = 100.0

# Finest first. Site tiles are 5 m patches for the four demo sites.
_CANDIDATES = (
    "Site*_final_adj_5mpp_surf.tif",
    "ldem_87s_5mpp.tif",
    "LDEM_83S_10MPP_ADJ.TIF",
    "LDEM_80S_20MPP_ADJ.TIF",
    "LDEM_80S_40MPP_ADJ.TIF",
    "LDEM_80S_80MPP_ADJ.TIF",
    "LDEM_60S_120MPP_ADJ.TIF",
    "LDEM_60S_240MPP_ADJ.TIF",
)


class TerrainUnavailable(RuntimeError):
    """Neither a DEM on disk nor the store's relief tiles cover the site."""


@dataclass
class _Tier:
    name: str
    res: float
    radius: float
    grid: Grid


def _paths() -> list[Path]:
    out: list[Path] = []
    for pat in _CANDIDATES:
        out.extend(sorted(DEM.glob(pat)))
    return out


def _radius(x: float, y: float, b: tuple[float, float, float, float], res: float) -> float | None:
    left, bottom, right, top = b
    room = min(x - left, right - x, y - bottom, top - y)
    return None if room < MIN_WINDOW_M else min(R_MAX_M, res * WINDOW_PX, room)


def _local_tiers(x: float, y: float) -> list[_Tier]:
    import rasterio

    tiers: list[_Tier] = []
    for path in _paths():
        with rasterio.open(path) as src:
            b = tuple(src.bounds)
            res = float(src.res[0])
        radius = _radius(x, y, b, res)
        if radius is None:
            continue
        try:
            grid = load_tif(path, x, y, radius)
        except Exception:  # truncated or unreadable download: use the next DEM instead
            continue
        tiers.append(_Tier(path.name, res, radius, grid))
    return tiers


def _store_tiers(x: float, y: float) -> list[_Tier]:
    """Tiers from the store's relief tiles (D-20261118-pj-6fea); only the tiles each window needs are fetched."""
    tiers: list[_Tier] = []
    for stem in (Path(p).stem for p in _CANDIDATES if "*" not in p):  # 5 m site mosaics are not tiled
        try:
            mpath = relief_tiles.locate(f"relief/{stem}/manifest.json")
            if mpath is None:
                continue
            manifest = json.loads(Path(mpath).read_text())
            radius = _radius(x, y, relief_tiles.bounds(manifest), manifest["res"])
            if radius is None:
                continue

            def fetch(rel: str, stem: str = stem) -> Path:
                p = relief_tiles.locate(f"relief/{stem}/{rel}")
                if p is None:
                    raise FileNotFoundError(f"relief/{stem}/{rel}")
                return p

            grid = relief_tiles.window_from_tiles(manifest, fetch, x, y, radius)
        except Exception:  # offline, bad manifest or failed tile: use the next model instead
            continue
        tiers.append(_Tier(stem, float(manifest["res"]), radius, grid))
    return tiers


def _tiers(x: float, y: float) -> list[_Tier]:
    """Local data/dem files first; the store's relief tiles only when no local DEM covers the site."""
    tiers = _local_tiers(x, y) or _store_tiers(x, y)
    tiers.sort(key=lambda t: t.res)
    return tiers


def ring_radii() -> np.ndarray:
    n = int(math.ceil(math.log(R_MAX_M / R_MIN_M) / math.log(RING_RATIO))) + 1
    return (R_MIN_M * RING_RATIO ** np.arange(n)).clip(max=R_MAX_M)


def build_rings(lat: float, lon: float) -> dict:
    if lat >= 0:
        raise TerrainUnavailable("only the south polar cap has DEMs")
    x, y = polar_stereo_xy(lat, lon)
    tiers = _tiers(x, y)
    if not tiers:
        raise TerrainUnavailable("no local DEM or relief tiles cover this site")

    lon_r = math.radians(lon)
    north = np.array([math.sin(lon_r), math.cos(lon_r)])  # outward from the pole = increasing latitude
    east = np.array([math.cos(lon_r), -math.sin(lon_r)])
    az = np.radians(np.arange(NAZ) * (360.0 / NAZ))
    direction = np.cos(az)[None, :, None] * north + np.sin(az)[None, :, None] * east  # (1, naz, 2)

    radii = ring_radii()
    h0 = float(tiers[0].grid.sample(np.array([x]), np.array([y]))[0])
    heights = np.empty((radii.size, NAZ), dtype=np.float32)
    ring_dem: list[str] = []
    for i, r in enumerate(radii):
        tier = next((t for t in tiers if r <= t.radius), tiers[-1])
        px = x + r * direction[0, :, 0]
        py = y + r * direction[0, :, 1]
        h = tier.grid.sample(px, py)
        heights[i] = h - h0 - r * r / (2.0 * R_M)
        ring_dem.append(tier.name)

    return {
        "lat": lat,
        "lon": lon,
        "ground_m": h0,
        "sphere_radius_m": R_M,
        "naz": NAZ,
        "radii_m": [round(float(r), 3) for r in radii],
        "heights_f32_b64": base64.b64encode(heights.astype("<f4").tobytes()).decode("ascii"),
        "dem": sorted(set(ring_dem), key=ring_dem.index),
        "convention": "az clockwise from geographic north; heights above the tangent plane at ground_m",
    }


@lru_cache(maxsize=8)
def _cached(lat_key: int, lon_key: int) -> dict:
    return build_rings(lat_key / 1e5, lon_key / 1e5)


def rings_for(lat: float, lon: float) -> dict:
    """Memoised on a ~1 m grid so scrubbing time or reloading the view does not re-read the DEMs."""
    return _cached(round(lat * 1e5), round(lon * 1e5))
