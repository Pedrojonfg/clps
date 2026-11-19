"""Contract tests for moonpark.visibility (D-20261114-pj-9e53, D-f369)."""

from __future__ import annotations

import numpy as np
import pytest

from moonpark.visibility import longest_lit_h, longest_night_h, sun_fraction

RS = 0.2665


def _ref_sun_fraction(el: float, h: float, sun_radius_deg: float = RS) -> float:
    x = np.clip((el - h) / sun_radius_deg, -1.0, 1.0)
    return float(1.0 - (np.arccos(x) - x * np.sqrt(1.0 - x * x)) / np.pi)


def test_sun_fraction_disc() -> None:
    el = np.array([0.5, 0.0, 0.3])
    h = np.array([0.0, 0.5, 0.3])
    got = sun_fraction(el, h, sun_radius_deg=RS)
    want = np.array([_ref_sun_fraction(e, hi) for e, hi in zip(el, h, strict=True)])
    np.testing.assert_allclose(got, want, rtol=0, atol=1e-9)


@pytest.mark.parametrize(
    "fraction,expected",
    [
        # D-20261118-pj-9413: maximum-type, upper hole-to-hole bound t_4 - t_0 (was a sample count, 3)
        (np.array([1.0, 0.0, 0.0, 0.0, 1.0]), 4),
    ],
)
def test_longest_night_h(fraction: np.ndarray, expected: int) -> None:
    assert longest_night_h(fraction, lit_threshold=0.0) == expected


@pytest.mark.parametrize(
    "fraction,bridge_h,expected",
    [
        # D-20261118-pj-9413: minimum-type, lower bound last-minus-first lit sample (were sample counts 2, 5, 2)
        (np.array([1.0, 1.0, 0.0, 1.0, 1.0]), 0, 1),
        # D-9413 pessimistic bridge: k dark samples may last (k + 1) steps; bridged only if (k + 1) * step <= bridge_h
        (np.array([1.0, 1.0, 0.0, 1.0, 1.0]), 1, 1),  # 1 dark sample, up to 2 h > 1 h: not bridged (was 4)
        (np.array([1.0, 1.0, 0.0, 1.0, 1.0]), 2, 4),
        (np.array([1.0, 1.0, 0.0, 0.0, 1.0, 1.0]), 1, 1),
    ],
)
def test_longest_lit_h(fraction: np.ndarray, bridge_h: int, expected: int) -> None:
    assert longest_lit_h(fraction, lit_threshold=0.0, bridge_h=bridge_h) == expected

def test_series_exposes_hour_counts_consistent_with_fractions() -> None:
    """hours_*_above_threshold = sum over lit runs of (last - first lit sample) (D-20261118-pj-9413,
    superseding the sample count of D-7520)."""
    from moonpark.providers import HorizonMask, SkySample
    from moonpark.visibility import series

    elevation = np.full(720, 10.0, dtype=np.float32)
    horizon = HorizonMask(
        elevation_deg=elevation,
        x_m=0.0,
        y_m=0.0,
        lat=-89.46316,
        lon=222.51045,
        h0_m=0.0,
        observer_height_m=2.0,
        schedule_version="vis-hours-v1",
        dem_ids=(),
    )
    t = np.datetime64("2027-06-01T00:00:00")
    samples = [
        SkySample(
            t + np.timedelta64(i, "h"),
            sun_az_deg=0.0,
            sun_el_deg=el,
            sun_radius_deg=RS,
            earth_az_deg=0.0,
            earth_el_deg=eel,
            earth_radius_deg=0.5,
        )
        for i, (el, eel) in enumerate([(20.0, 90.0), (20.0, -90.0), (0.0, 90.0), (0.0, -90.0)])
    ]
    out = series(samples, horizon, sun_threshold=0.5, earth_threshold=0.5)
    assert int((np.asarray(out["sun_fraction"]) > 0.5).sum()) == 2  # one lit run, samples 0..1
    assert int((np.asarray(out["earth_fraction"]) > 0.5).sum()) == 2  # two single-sample lit runs
    assert out["hours_sun_above_threshold"] == 1
    assert out["hours_earth_above_threshold"] == 0
