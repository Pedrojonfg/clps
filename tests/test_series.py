"""S3 glue tests for moonpark.visibility.series."""

from __future__ import annotations

import numpy as np

from moonpark.providers import HorizonMask, SkySample
from moonpark.visibility import longest_lit_h, series, sun_fraction

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

def _sample(t, *, sun_az, sun_el, earth_az, earth_el):
    return SkySample(
        t,
        sun_az_deg=sun_az,
        sun_el_deg=sun_el,
        sun_radius_deg=RS,
        earth_az_deg=earth_az,
        earth_el_deg=earth_el,
        earth_radius_deg=0.5,
    )


def _hours_samples() -> list[SkySample]:
    t = np.datetime64("2027-06-01T00:00:00")
    h = np.timedelta64(1, "h")
    return [
        # sun lit via notch (geo az 180 -> -5° mask), earth lit (az 0 -> 10° mask, el 90)
        _sample(t, sun_az=180.0, sun_el=0.0, earth_az=0.0, earth_el=90.0),
        # sun lit, earth dark
        _sample(t + h, sun_az=180.0, sun_el=0.0, earth_az=0.0, earth_el=-90.0),
        # sun dark (10° mask), earth lit
        _sample(t + 2 * h, sun_az=0.0, sun_el=0.0, earth_az=0.0, earth_el=90.0),
        # sun partially up (10.1° vs 10° mask), earth dark
        _sample(t + 3 * h, sun_az=0.0, sun_el=10.1, earth_az=0.0, earth_el=-90.0),
        # sun dark, earth dark
        _sample(t + 4 * h, sun_az=0.0, sun_el=0.0, earth_az=0.0, earth_el=-90.0),
    ]


def test_series_hours_above_threshold_keys_are_ints() -> None:
    out = series(_hours_samples(), _hand_horizon())
    for key in ("hours_sun_above_threshold", "hours_earth_above_threshold"):
        assert key in out, f"missing {key}"
        assert isinstance(out[key], int)
        assert not isinstance(out[key], bool)


def test_series_hours_above_threshold_default_thresholds() -> None:
    out = series(_hours_samples(), _hand_horizon())
    sun = np.asarray(out["sun_fraction"])
    earth = np.asarray(out["earth_fraction"])
    assert int((sun > 0.0).sum()) == 3  # hours 0, 1, 3
    assert int((earth > 0.0).sum()) == 2  # hours 0, 2
    assert out["hours_sun_above_threshold"] == int((sun > 0.0).sum())
    assert out["hours_earth_above_threshold"] == int((earth > 0.0).sum())


def test_series_hours_above_threshold_respects_custom_thresholds() -> None:
    out = series(_hours_samples(), _hand_horizon(), sun_threshold=0.99, earth_threshold=0.5)
    sun = np.asarray(out["sun_fraction"])
    earth = np.asarray(out["earth_fraction"])
    # partial sun at hour 3 is above 0 but not above 0.99 -> strict threshold matters
    assert 0.0 < sun[3] < 0.99
    assert out["hours_sun_above_threshold"] == int((sun > 0.99).sum()) == 2
    assert out["hours_earth_above_threshold"] == int((earth > 0.5).sum()) == 2


def test_series_hours_above_threshold_strict_greater_than() -> None:
    horizon = _hand_horizon()
    samples = _hours_samples()
    out0 = series(samples, horizon)
    top = float(np.asarray(out0["sun_fraction"]).max())
    assert top == 1.0
    out = series(samples, horizon, sun_threshold=top, earth_threshold=1.0)
    assert out["hours_sun_above_threshold"] == 0
    assert out["hours_earth_above_threshold"] == 0
