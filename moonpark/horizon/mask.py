"""Topographic horizon mask. # per D-20261114-pj-f369 D-20261114-pj-9e53"""

from __future__ import annotations

import math

import numpy as np

from moonpark.providers import HorizonMask, Site

SCHEDULE_VERSION = "D-f369-v1"
R_M = 1_737_400.0
NAZ = 720


def polar_stereo_xy(lat_deg: float, lon_deg: float, radius_m: float = R_M) -> tuple[float, float]:
    rho = 2.0 * radius_m * math.tan(math.radians(90.0 + lat_deg) / 2.0)
    return rho * math.sin(math.radians(lon_deg)), rho * math.cos(math.radians(lon_deg))


def mask(site: Site, schedule=None) -> HorizonMask:
    x_m, y_m = polar_stereo_xy(site.lat_deg, site.lon_deg)

    if not schedule:
        return HorizonMask(
            elevation_deg=np.zeros(NAZ, dtype=np.float32),
            x_m=x_m,
            y_m=y_m,
            lat=site.lat_deg,
            lon=site.lon_deg,
            h0_m=0.0,
            observer_height_m=site.observer_height_m,
            schedule_version=SCHEDULE_VERSION,
            dem_ids=(),
        )

    ex, ey = -x_m, -y_m
    n = math.hypot(ex, ey) or 1.0
    ex, ey = ex / n, ey / n
    nx, ny = -ey, ex

    g0 = schedule[0][2]
    h0_ground = float(g0.sample(np.array([x_m]), np.array([y_m]))[0])
    h0 = h0_ground + site.observer_height_m

    az = np.radians(np.arange(NAZ) * 0.5)
    ca, sa = np.cos(az)[:, None], np.sin(az)[:, None]
    best = np.full(NAZ, -90.0, dtype=np.float64)

    for a0, b0, g in schedule:
        step = max(g.res / 2.0, 1e-9)
        d = np.arange(max(a0, step), b0, step)
        if d.size == 0:
            continue
        X = x_m + d[None, :] * (ca * ex + sa * nx)
        Y = y_m + d[None, :] * (ca * ey + sa * ny)
        h = g.sample(X, Y)
        ang = np.degrees(np.arctan((h - h0 - d ** 2 / (2.0 * R_M)) / d))
        best = np.maximum(best, ang.max(axis=1))

    return HorizonMask(
        elevation_deg=best.astype(np.float32),
        x_m=x_m,
        y_m=y_m,
        lat=site.lat_deg,
        lon=site.lon_deg,
        h0_m=h0_ground,
        observer_height_m=site.observer_height_m,
        schedule_version=SCHEDULE_VERSION,
        dem_ids=(),
    )