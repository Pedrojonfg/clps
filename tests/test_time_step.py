"""Time step is a parameter (D-20261117-pj-91c6): metrics are in hours whatever the sample spacing."""

from __future__ import annotations

import numpy as np
import pytest

from moonpark.planner_payload import parse_time_window
from moonpark.providers import HorizonMask, SkySample
from moonpark.score import score
from moonpark.visibility import longest_lit_h, longest_night_h, series

TEN_MIN_H = 10 / 60


def test_longest_night_counts_hours_not_samples() -> None:
    fraction = np.array([1.0] * 3 + [0.0] * 12 + [1.0] * 3)
    assert longest_night_h(fraction, 0.0) == 12  # hourly: 12 samples = 12 h
    assert longest_night_h(fraction, 0.0, step_h=TEN_MIN_H) == 2  # 10 min: 12 samples = 2 h


def test_longest_lit_bridge_is_in_hours() -> None:
    fraction = np.array([1.0, 1.0] + [0.0] * 6 + [1.0, 1.0])  # 1 h gap at 10 min
    assert longest_lit_h(fraction, 0.0, bridge_h=0, step_h=TEN_MIN_H) < 2
    assert longest_lit_h(fraction, 0.0, bridge_h=1, step_h=TEN_MIN_H) == pytest.approx(len(fraction) * TEN_MIN_H, abs=1e-5)
    assert longest_lit_h(fraction, 0.0, bridge_h=0.5, step_h=TEN_MIN_H) < len(fraction) * TEN_MIN_H


def test_parse_time_window_step_min() -> None:
    hourly = parse_time_window("2027-01-01T00:00:00Z", "2027-01-01T23:00:00Z")
    fine = parse_time_window("2027-01-01T00:00:00Z", "2027-01-01T23:00:00Z", step_min=10)
    assert len(hourly) == 24
    assert len(fine) == 23 * 6 + 1
    assert (fine[1] - fine[0]) == np.timedelta64(10, "m")
    assert fine[0] == hourly[0] and fine[-1] == hourly[-1]


def _flat_horizon() -> HorizonMask:
    return HorizonMask(
        elevation_deg=np.full(720, 0.0, dtype=np.float32),
        x_m=0.0, y_m=0.0, lat=-89.46316, lon=222.51045, h0_m=0.0,
        observer_height_m=2.0, schedule_version="t", dem_ids=(),
    )


def _samples(step_min: int, els: list[float]) -> list[SkySample]:
    t0 = np.datetime64("2027-06-01T00:00:00")
    return [
        SkySample(t0 + np.timedelta64(i * step_min, "m"), 90.0, e, 0.2665, 90.0, -90.0, 0.5)
        for i, e in enumerate(els)
    ]


def test_series_reports_step_and_hours() -> None:
    els = [1.0] * 6 + [-1.0] * 18  # 1 h lit, 3 h dark at 10 min
    out = series(_samples(10, els), _flat_horizon(), sun_threshold=0.5, step_min=10)
    assert out["step_min"] == 10
    assert out["longest_night_h"] == 3
    assert out["hours_sun_above_threshold"] == 1


def test_bonus_fraction_does_not_depend_on_step() -> None:
    needs = {"max_night_h": 10, "max_no_earth_h": 10}
    base = {
        "sun_fraction": [1.0] * 12 + [0.0] * 12,
        "earth_fraction": [1.0] * 24,
        "longest_night_h": 3, "longest_no_earth_h": 0, "longest_lit_h": 3,
        "hours_sun_above_threshold": 12, "hours_earth_above_threshold": 24,
    }
    hourly = score({**base, "step_min": 60}, {}, needs)
    fine = score(
        {**base, "step_min": 10, "hours_sun_above_threshold": 2, "hours_earth_above_threshold": 4},
        {}, needs,
    )
    assert abs(hourly["breakdown"]["layer1_B"] - fine["breakdown"]["layer1_B"]) < 1e-9
