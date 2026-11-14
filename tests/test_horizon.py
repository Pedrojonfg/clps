"""Contract tests for lunar_eval.horizon (D-20261114-pj-f369, D-9e53).

polar_stereo_xy must match the south-polar formula in /tmp/masktest.py.
mask() has no sampler seam yet, so default tests cover xy, shape and
metadata only — they must not open 15 GB DEMs. A local-east peak vs north
geometry case waits on an injectable sampler.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from lunar_eval.horizon import Grid, mask, polar_stereo_xy
from lunar_eval.providers import Site

R_M = 1_737_400.0  # 1737.4e3 m


def _ref_xy(
    lat_deg: float, lon_deg: float, radius_m: float = R_M
) -> tuple[float, float]:
    rho = 2.0 * radius_m * math.tan(math.radians(90.0 + lat_deg) / 2.0)
    x = rho * math.sin(math.radians(lon_deg))
    y = rho * math.cos(math.radians(lon_deg))
    return x, y


def test_polar_stereo_xy_south_pole_is_origin() -> None:
    for lon in (0.0, 90.0, 222.7, 359.0):
        x, y = polar_stereo_xy(-90.0, lon)
        assert x == pytest.approx(0.0, abs=1e-9)
        assert y == pytest.approx(0.0, abs=1e-9)


def test_polar_stereo_xy_lat_minus_89_5_lon_0_positive_y() -> None:
    x, y = polar_stereo_xy(-89.5, 0.0)
    rho = 2.0 * R_M * math.tan(math.radians(90.0 + -89.5) / 2.0)
    assert x == pytest.approx(0.0, abs=1e-6)
    assert y > 0.0
    assert y == pytest.approx(rho, abs=1e-6)


@pytest.mark.parametrize(
    "lat, lon",
    [
        (-90.0, 0.0),
        (-90.0, 180.0),
        (-89.5, 0.0),
        (-89.5, 90.0),
        (-89.5, 180.0),
        (-89.5, 270.0),
        (-89.46316, 222.51045),
        (-88.81101, 123.69007),
        (-85.0, 45.0),
        (-80.0, 359.0),
    ],
)
def test_polar_stereo_xy_matches_south_polar_formula(lat: float, lon: float) -> None:
    got = polar_stereo_xy(lat, lon)
    want = _ref_xy(lat, lon)
    np.testing.assert_allclose(got, want, rtol=0.0, atol=1e-6)


def test_polar_stereo_xy_minus_89_5_cardinal_longitudes() -> None:
    rho = 2.0 * R_M * math.tan(math.radians(90.0 + -89.5) / 2.0)
    x, y = polar_stereo_xy(-89.5, 90.0)
    assert x == pytest.approx(rho, abs=1e-6)
    assert y == pytest.approx(0.0, abs=1e-6)
    x, y = polar_stereo_xy(-89.5, 180.0)
    assert x == pytest.approx(0.0, abs=1e-6)
    assert y == pytest.approx(-rho, abs=1e-6)
    x, y = polar_stereo_xy(-89.5, 270.0)
    assert x == pytest.approx(-rho, abs=1e-6)
    assert y == pytest.approx(0.0, abs=1e-6)


def test_polar_stereo_xy_scales_with_radius_m() -> None:
    got = polar_stereo_xy(-89.5, 45.0, radius_m=1000.0)
    np.testing.assert_allclose(got, _ref_xy(-89.5, 45.0, 1000.0), rtol=0.0, atol=1e-9)


def test_mask_elevation_deg_shape_and_dtype() -> None:
    m = mask(Site(lat_deg=-89.5, lon_deg=0.0))
    assert m.elevation_deg.shape == (720,)
    assert m.elevation_deg.dtype == np.float32


def test_mask_schedule_version() -> None:
    m = mask(Site(lat_deg=-89.5, lon_deg=0.0))
    assert m.schedule_version == "D-f369-v1"


def test_mask_records_site_and_stereo_xy() -> None:
    site = Site(lat_deg=-89.5, lon_deg=0.0, observer_height_m=2.0)
    m = mask(site)
    assert m.lat == site.lat_deg
    assert m.lon == site.lon_deg
    assert m.observer_height_m == site.observer_height_m
    x, y = polar_stereo_xy(site.lat_deg, site.lon_deg)
    assert m.x_m == pytest.approx(x, abs=1e-6)
    assert m.y_m == pytest.approx(y, abs=1e-6)


def _synthetic_grid(
    lat_deg: float,
    lon_deg: float,
    *,
    res: float = 50.0,
    half_extent_m: float = 2500.0,
    peak_east_m: float | None = None,
    peak_height_m: float = 0.0,
) -> Grid:
    """Flat DEM window in polar stereo centred on the site; optional +X peak (local east at lon 0)."""
    sx, sy = polar_stereo_xy(lat_deg, lon_deg)
    n = int(2 * half_extent_m / res) + 1
    x0 = sx - half_extent_m
    y0 = sy + half_extent_m
    z = np.zeros((n, n), dtype=np.float32)
    if peak_east_m is not None and peak_height_m > 0.0:
        px = sx + peak_east_m
        py = sy
        col = int(round((px - x0) / res - 0.5))
        row = int(round((y0 - py) / res - 0.5))
        z[row, col] = np.float32(peak_height_m)
    return Grid(z, x0, y0, res)


# East horizon bin (az=90°); north toward pole is 0; west is 270° → index 540.
_AZ_EAST = 180
_AZ_NORTH = 0
_AZ_WEST = 540
_PEAK_DIST_M = 500.0
_PEAK_HEIGHT_M = 1000.0


def test_mask_east_peak_raises_east_azimuth() -> None:
    site = Site(lat_deg=-89.5, lon_deg=0.0, observer_height_m=2.0)
    grid = _synthetic_grid(
        site.lat_deg,
        site.lon_deg,
        peak_east_m=_PEAK_DIST_M,
        peak_height_m=_PEAK_HEIGHT_M,
    )
    m = mask(site, schedule=[(50.0, 800.0, grid)])
    assert m.elevation_deg.dtype == np.float32
    assert m.elevation_deg.shape == (720,)
    elev = m.elevation_deg
    assert elev[_AZ_EAST] > elev[_AZ_NORTH] + 30.0
    assert elev[_AZ_EAST] > elev[_AZ_WEST] + 30.0
    # 1-pixel peak is bilinear-smoothed; lock direction and a tall-east range, not atan(h/500).
    assert 40.0 < float(elev[_AZ_EAST]) < 80.0


def test_mask_flat_dem_near_zero() -> None:
    site = Site(lat_deg=-89.5, lon_deg=0.0, observer_height_m=2.0)
    grid = _synthetic_grid(site.lat_deg, site.lon_deg)
    m = mask(site, schedule=[(50.0, 800.0, grid)])
    assert m.elevation_deg.dtype == np.float32
    assert m.elevation_deg.shape == (720,)
    # 2 m observer on a 50 m first sample: atan(-2/50) ≈ -2.3°. Bound is physics, not 1°.
    assert np.all(np.abs(m.elevation_deg) < 3.0)
