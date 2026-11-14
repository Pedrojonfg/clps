"""Body-agnostic provider seams (P1, P2, P5). Moon is the only implemented body.

# per D-20261114-pj-9e53
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Body:
    name: str
    radius_m: float
    frame: str


MOON = Body(name="moon", radius_m=1_737_400.0, frame="MOON_ME")


@dataclass(frozen=True)
class Site:
    lat_deg: float
    lon_deg: float
    height_m: float = 0.0
    observer_height_m: float = 2.0


@dataclass(frozen=True)
class SkySample:
    time_utc: np.datetime64
    sun_az_deg: float
    sun_el_deg: float
    sun_radius_deg: float
    earth_az_deg: float
    earth_el_deg: float
    earth_radius_deg: float


@dataclass(frozen=True)
class HorizonMask:
    elevation_deg: NDArray[np.float32]
    x_m: float
    y_m: float
    lat: float
    lon: float
    h0_m: float
    observer_height_m: float
    schedule_version: str
    dem_ids: tuple[str, ...]


class EphemerisProvider(Protocol):
    """P1: azimuth from north through east; elevation above the smooth horizon."""

    def sky(self, site: Site, times: NDArray[np.datetime64]) -> list[SkySample]: ...


class HorizonProvider(Protocol):
    """P2: 720 bins of 0.5° from north through east."""

    def mask(self, site: Site) -> HorizonMask: ...


class SurfaceHazardProvider(Protocol):
    """P5: temperature, dust and related site hazards at a site×time."""

    def hazards(self, site: Site, times: NDArray[np.datetime64]) -> dict: ...
