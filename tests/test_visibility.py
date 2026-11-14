"""Contract tests for lunar_eval.visibility (D-20261114-pj-9e53, D-f369)."""

from __future__ import annotations

import numpy as np
import pytest

from lunar_eval.visibility import longest_lit_h, longest_night_h, sun_fraction

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
        (np.array([1.0, 0.0, 0.0, 0.0, 1.0]), 3),
    ],
)
def test_longest_night_h(fraction: np.ndarray, expected: int) -> None:
    assert longest_night_h(fraction, lit_threshold=0.0) == expected


@pytest.mark.parametrize(
    "fraction,bridge_h,expected",
    [
        (np.array([1.0, 1.0, 0.0, 1.0, 1.0]), 0, 2),
        (np.array([1.0, 1.0, 0.0, 1.0, 1.0]), 1, 5),
        (np.array([1.0, 1.0, 0.0, 0.0, 1.0, 1.0]), 1, 2),
    ],
)
def test_longest_lit_h(fraction: np.ndarray, bridge_h: int, expected: int) -> None:
    assert longest_lit_h(fraction, lit_threshold=0.0, bridge_h=bridge_h) == expected