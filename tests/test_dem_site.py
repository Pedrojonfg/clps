"""Local DEM mask for Site01. Skips in CI when data/dem is absent."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from moonpark.horizon import load_tif, mask, polar_stereo_xy
from moonpark.providers import Site

_REPO = Path(__file__).resolve().parents[1]
_SITE5 = _REPO / "data" / "dem" / "Site01_final_adj_5mpp_surf.tif"
_G80 = _REPO / "data" / "dem" / "LDEM_80S_80MPP_ADJ.TIF"
_G240 = _REPO / "data" / "dem" / "LDEM_60S_240MPP_ADJ.TIF"
SITE01 = Site(lat_deg=-89.46316, lon_deg=222.51045, observer_height_m=2.0)


@pytest.mark.skipif(not _SITE5.is_file(), reason="Site01 5 m DEM not present")
def test_site01_5m_mask_is_not_flat() -> None:
    x, y = polar_stereo_xy(SITE01.lat_deg, SITE01.lon_deg)
    g5 = load_tif(_SITE5)
    m = mask(SITE01, schedule=[(5.0, 4000.0, g5)])
    assert m.elevation_deg.shape == (720,)
    assert m.dem_ids == ()
    assert float(np.ptp(m.elevation_deg)) > 0.5
    assert m.x_m == pytest.approx(x, abs=1.0)
    assert m.y_m == pytest.approx(y, abs=1.0)


@pytest.mark.skipif(
    not (_SITE5.is_file() and _G80.is_file() and _G240.is_file()),
    reason="D-f369 DEM stack not present",
)
def test_site01_schedule_mask_plausible() -> None:
    x, y = polar_stereo_xy(SITE01.lat_deg, SITE01.lon_deg)
    g5 = load_tif(_SITE5)
    g80 = load_tif(_G80, x, y, 30_000.0)
    g240 = load_tif(_G240, x, y, 260_000.0)
    # ponytail: 80 m stands in for the 100 m band (D-f369: same result in the test)
    sched = [
        (0.0, 250.0, g5),
        (250.0, 1000.0, g5.coarsen(4)),
        (1000.0, 2000.0, g5.coarsen(8)),
        (2000.0, 5000.0, g80),
        (5000.0, 25000.0, g80),
        (25000.0, 250000.0, g240),
    ]
    m = mask(SITE01, schedule=sched)
    assert m.elevation_deg.dtype == np.float32
    assert np.all(np.isfinite(m.elevation_deg))
    assert -30.0 < float(m.elevation_deg.min()) < 30.0
    assert -30.0 < float(m.elevation_deg.max()) < 45.0
    assert float(np.ptp(m.elevation_deg)) > 1.0


_DE440 = _REPO / "data" / "kernels" / "de440s.bsp"
_FIXTURE = _REPO / "tests" / "fixtures" / "horizons" / "Site01_20270101_20270301_sun.txt"


@pytest.mark.skipif(
    not (_SITE5.is_file() and _DE440.is_file()),
    reason="Site01 DEM or kernels not present",
)
def test_site01_sky_mask_series_score_end_to_end() -> None:
    pytest.importorskip("spiceypy")
    from horizons_parse import parse_horizons_azel

    from moonpark.ephemeris import SpiceEphemeris
    from moonpark.score import score
    from moonpark.visibility import series

    rows = parse_horizons_azel(_FIXTURE)[:8]
    times = np.array([row.time_utc for row in rows], dtype="datetime64[s]")
    sky = SpiceEphemeris().sky(SITE01, times)
    g5 = load_tif(_SITE5)
    horizon = mask(SITE01, schedule=[(5.0, 4000.0, g5)])
    out = series(sky, horizon)
    assert len(sky) == 8
    assert out["sun_fraction"].shape == (8,)
    assert 0.0 <= float(out["sun_fraction"].min()) <= float(out["sun_fraction"].max()) <= 1.0
    assert 0.0 <= float(out["earth_fraction"].min()) <= float(out["earth_fraction"].max()) <= 1.0
    scored = score(out, {}, {"max_night_h": 50, "max_no_earth_h": 20, "require_both": False})
    assert scored["score"] == 0 or scored["feasible"] is True
    assert scored["provenance"]["schedule_version"] == horizon.schedule_version
