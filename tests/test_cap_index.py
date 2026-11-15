"""Cap index queries (1 km precomputed masks)."""

from __future__ import annotations

import pytest

from lunar_eval.horizon import polar_stereo_xy
from lunar_eval.horizon.cap_index import (
    cap_index_available,
    sites_in_latlon_rect,
    sites_in_xy_rect,
)
from lunar_eval.site01 import SITE01

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
