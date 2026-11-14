"""S3 glue tests for lunar_eval.visibility.series."""

from __future__ import annotations

import numpy as np

from lunar_eval.providers import HorizonMask, SkySample
from lunar_eval.visibility import longest_lit_h, series, sun_fraction

RS = 0.2665
SCHEDULE = "test-hand-mask-v1"


def _hand_horizon() -> HorizonMask:
    elevation = np.full(720, 10.0, dtype=np.float32)
    elevation[0] = -5.0  # mask az 0: notch toward the south pole
    return HorizonMask(
        elevation_deg=elevation,
        x_m=0.0,
        y_m=0.0,
        lat=-89.46316,
        lon=222.51045,
        h0_m=0.0,
        observer_height_m=2.0,
        schedule_version=SCHEDULE,
        dem_ids=(),
    )


def test_series_mask_az_vs_geographic_az() -> None:
    """mask az 0 = toward south pole: geo south (180°) samples the -5° notch."""
    horizon = _hand_horizon()
    t0 = np.datetime64("2027-06-01T12:00:00")
    t1 = np.datetime64("2027-06-01T13:00:00")
    south = SkySample(
        t0,
        sun_az_deg=180.0,
        sun_el_deg=0.0,
        sun_radius_deg=RS,
        earth_az_deg=90.0,
        earth_el_deg=-90.0,
        earth_radius_deg=0.5,
    )
    north = SkySample(
        t1,
        sun_az_deg=0.0,
        sun_el_deg=0.0,
        sun_radius_deg=RS,
        earth_az_deg=90.0,
        earth_el_deg=-90.0,
        earth_radius_deg=0.5,
    )

    out = series([south, north], horizon)

    want_south = float(sun_fraction(np.array([0.0]), np.array([-5.0]), RS)[0])
    want_north = float(sun_fraction(np.array([0.0]), np.array([10.0]), RS)[0])
    np.testing.assert_allclose(out["sun_fraction"][0], want_south, rtol=0, atol=1e-9)
    np.testing.assert_allclose(out["sun_fraction"][1], want_north, rtol=0, atol=1e-9)
    assert want_south == 1.0
    assert want_north == 0.0

    for key in (
        "sun_fraction",
        "earth_fraction",
        "longest_night_h",
        "longest_no_earth_h",
        "longest_lit_h",
        "any_both",
        "schedule_version",
    ):
        assert key in out
    assert out["schedule_version"] == SCHEDULE


def test_series_flags_longest_and_any_both() -> None:
    horizon = _hand_horizon()
    t = np.datetime64("2027-06-01T00:00:00")
    # Hour 0: sun fully above notch; earth invisible. Hour 1: sun below 10° mask; both dark.
    samples = [
        SkySample(
            t,
            sun_az_deg=180.0,
            sun_el_deg=0.0,
            sun_radius_deg=RS,
            earth_az_deg=180.0,
            earth_el_deg=-90.0,
            earth_radius_deg=0.5,
        ),
        SkySample(
            t + np.timedelta64(1, "h"),
            sun_az_deg=0.0,
            sun_el_deg=0.0,
            sun_radius_deg=RS,
            earth_az_deg=0.0,
            earth_el_deg=-90.0,
            earth_radius_deg=0.5,
        ),
    ]
    out = series(samples, horizon, sun_threshold=0.0, earth_threshold=0.0, bridge_h=1)
    assert out["longest_night_h"] == 1
    assert out["longest_no_earth_h"] == len(samples)
    assert out["any_both"] is False
    lit = np.asarray(out["sun_fraction"]) > 0.0
    assert out["longest_lit_h"] == longest_lit_h(out["sun_fraction"], lit_threshold=0.0, bridge_h=1)