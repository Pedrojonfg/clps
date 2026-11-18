"""Cap index queries (1 km precomputed masks)."""

from __future__ import annotations

import pytest

from moonpark.horizon import polar_stereo_xy
from moonpark.horizon.cap_index import (
    cap_index_available,
    sites_in_latlon_rect,
    sites_in_xy_rect,
)
from moonpark.site01 import SITE01

pytestmark = pytest.mark.skipif(not cap_index_available(), reason="cap_1km index not present")


def test_sites_in_xy_rect_near_site01_is_nonempty() -> None:
    sx, sy = polar_stereo_xy(SITE01.lat_deg, SITE01.lon_deg)
    cells = sites_in_xy_rect(sx - 5_000, sx + 5_000, sy - 5_000, sy + 5_000)
    assert len(cells) >= 20
    site, x_m, y_m, _tx, _ty, _row = cells[0]
    assert abs(x_m - sx) <= 5_000 + 1.0
    assert abs(y_m - sy) <= 5_000 + 1.0
    assert -90.0 <= site.lat_deg <= -80.0


def test_latlon_rect_still_returns_cells() -> None:
    # Near-pole lon pad is tiny in metres; still must not crash / return junk.
    cells = sites_in_latlon_rect(
        SITE01.lat_deg - 0.05,
        SITE01.lat_deg + 0.05,
        SITE01.lon_deg - 0.15,
        SITE01.lon_deg + 0.15,
    )
    assert isinstance(cells, list)
    for site, *_rest in cells:
        assert SITE01.lat_deg - 0.05 <= site.lat_deg <= SITE01.lat_deg + 0.05


def test_nearest_cap_mask_snaps_within_a_cell():
    from moonpark.horizon.cap_index import nearest_cap_mask
    from moonpark.providers import Site

    m = nearest_cap_mask(Site(lat_deg=-89.46316, lon_deg=222.51045, observer_height_m=2.0))
    assert m is not None and m.elevation_deg.shape == (720,)
    # Far outside the cap: no cell, no mask.
    assert nearest_cap_mask(Site(lat_deg=-60.0, lon_deg=0.0, observer_height_m=2.0)) is None


def test_latlon_rect_filters_by_longitude() -> None:
    lo, hi = SITE01.lon_deg - 0.5, SITE01.lon_deg + 0.5
    cells = sites_in_latlon_rect(-90.0, -80.0, lo, hi)
    assert cells
    for site, *_rest in cells:
        assert lo <= site.lon_deg <= hi
