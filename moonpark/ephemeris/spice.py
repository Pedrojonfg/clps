"""Local kernel sky. # per D-20261114-pj-4ffe D-20261114-pj-9e53"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from moonpark.providers import MOON, Site, SkySample

KERNEL_DIR = Path(__file__).resolve().parents[2] / "data" / "kernels"
KERNEL_NAMES = (
    "naif0012.tls",
    "pck00011.tpc",
    "moon_pa_de440_200625.bpc",
    "moon_de440_250416.tf",
    "moon_assoc_me.tf",
    "de440s.bsp",
)
# moon_080317.tf aliases MOON_ME to MOON_PA_DE421; do not load it with the DE440 PCK.
# Horizons fixtures: spherical 1737.4 km, IAU 2015 solar radius.
R_MOON_KM = MOON.radius_m / 1000.0
SUN_R_KM = 695_700.0
EARTH_R_KM = 6378.137
_FURNISHED: Path | None = None


def _furnsh(kernel_dir: Path) -> None:
    global _FURNISHED
    import spiceypy as spice

    if _FURNISHED == kernel_dir:
        return
    spice.kclear()
    for name in KERNEL_NAMES:
        path = kernel_dir / name
        if not path.is_file() and kernel_dir == KERNEL_DIR:
            from moonpark.horizon.remote import locate

            path = locate(f"kernels/{name}") or path  # per D-8c03: kernels come from the store
        spice.furnsh(str(path))
    _FURNISHED = kernel_dir


def _azel(vec: NDArray[np.float64], east: NDArray, north: NDArray, up: NDArray) -> tuple[float, float]:
    el = math.degrees(math.asin(float(np.clip(np.dot(vec, up) / np.linalg.norm(vec), -1.0, 1.0))))
    az = math.degrees(math.atan2(float(np.dot(vec, east)), float(np.dot(vec, north)))) % 360.0
    return az, el


class SpiceEphemeris:
    def __init__(self, kernel_dir: Path | None = None):
        self._kernel_dir = Path(kernel_dir) if kernel_dir is not None else KERNEL_DIR

    def sky(self, site: Site, times: NDArray[np.datetime64]) -> list[SkySample]:
        import spiceypy as spice

        _furnsh(self._kernel_dir)
        lat = math.radians(site.lat_deg)
        lon = math.radians(site.lon_deg)
        obspos = spice.georec(lon, lat, site.height_m / 1000.0, R_MOON_KM, 0.0)
        sin_lat, cos_lat = math.sin(lat), math.cos(lat)
        sin_lon, cos_lon = math.sin(lon), math.cos(lon)
        east = np.array([-sin_lon, cos_lon, 0.0])
        north = np.array([-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat])
        up = np.array([cos_lat * cos_lon, cos_lat * sin_lon, sin_lat])
        out: list[SkySample] = []
        for t in np.asarray(times):
            iso = str(np.datetime64(t, "s")).replace("T", " ")
            et = spice.utc2et(iso + " UTC")
            sun_state, _ = spice.spkcpo("SUN", et, "MOON_ME", "OBSERVER", "LT+S", obspos, "MOON", "MOON_ME")
            earth_state, _ = spice.spkcpo("EARTH", et, "MOON_ME", "OBSERVER", "LT+S", obspos, "MOON", "MOON_ME")
            sun = np.asarray(sun_state[:3], dtype=np.float64)
            earth = np.asarray(earth_state[:3], dtype=np.float64)
            sun_az, sun_el = _azel(sun, east, north, up)
            earth_az, earth_el = _azel(earth, east, north, up)
            sun_range = float(np.linalg.norm(sun))
            earth_range = float(np.linalg.norm(earth))
            out.append(
                SkySample(
                    time_utc=np.datetime64(t, "s"),
                    sun_az_deg=sun_az,
                    sun_el_deg=sun_el,
                    sun_radius_deg=math.degrees(math.atan(SUN_R_KM / sun_range)),
                    earth_az_deg=earth_az,
                    earth_el_deg=earth_el,
                    earth_radius_deg=math.degrees(math.atan(EARTH_R_KM / earth_range)),
                )
            )
        return out
