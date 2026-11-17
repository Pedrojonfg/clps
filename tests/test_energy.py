"""Energy balance (D-20261117-pj-7b2d)."""

from __future__ import annotations

import numpy as np
import pytest

from lunar_eval.energy import EnergyParams, incidence_cos, params_from_needs, soc_series
from lunar_eval.score import score

TEN_MIN_H = 10 / 60


def test_incidence_panels() -> None:
    az, el = np.array([90.0]), np.array([1.0])
    assert incidence_cos(az, el, "horizontal", 0.0)[0] == pytest.approx(np.sin(np.radians(1.0)))
    assert incidence_cos(az, el, "tracking_vertical", 0.0)[0] == pytest.approx(np.cos(np.radians(1.0)))


def test_fixed_vertical_peaks_when_sun_az_equals_panel_az() -> None:
    az = np.arange(0.0, 360.0, 5.0)
    got = incidence_cos(az, np.full_like(az, 1.0), "fixed_vertical", 135.0)
    assert az[int(np.argmax(got))] == 135.0
    assert incidence_cos(np.array([315.0]), np.array([1.0]), "fixed_vertical", 135.0)[0] == 0.0  # back of the panel


def _scenario(dark_h_a: float, lit_h: float, dark_h_b: float):
    n = lambda h: int(round(h / TEN_MIN_H))  # noqa: E731
    frac = np.array([0.0] * n(dark_h_a) + [1.0] * n(lit_h) + [0.0] * n(dark_h_b))
    az = np.full(len(frac), 90.0)
    el = np.full(len(frac), 0.0)  # tracking vertical: cos(0) = 1
    return frac, az, el


PARAMS = EnergyParams(capacity_wh=100.0, array_w=40.0, dark_w=20.0)  # 5 h endurance


def test_four_hours_twenty_minutes_four_hours_drains_the_battery() -> None:
    frac, az, el = _scenario(4, 1 / 3, 4)
    soc = soc_series(frac, az, el, PARAMS, step_h=TEN_MIN_H)
    assert soc[0] == 1.0
    assert soc.min() == 0.0  # 100 -> 20 -> ~27 -> empty: 20 min of light does not refill it


def test_long_light_refills_the_battery() -> None:
    frac, az, el = _scenario(4, 4, 4)
    soc = soc_series(frac, az, el, PARAMS, step_h=TEN_MIN_H)
    assert soc.min() == pytest.approx(0.2, abs=0.01)  # first night 100 -> 20 %, never lower


def test_score_energy_mode_fails_where_the_night_proxy_passes() -> None:
    frac, az, el = _scenario(4, 1 / 3, 4)
    soc = soc_series(frac, az, el, PARAMS, step_h=TEN_MIN_H)
    base = {
        "sun_fraction": frac.tolist(), "earth_fraction": [1.0] * len(frac), "step_min": 10,
        "longest_night_h": 4, "longest_no_earth_h": 0, "longest_lit_h": 1,
        "hours_sun_above_threshold": 1, "hours_earth_above_threshold": 8,
    }
    needs = {"max_night_h": 5, "max_no_earth_h": 10}
    assert score(base, {}, needs)["feasible"] is True  # proxy: 4 h <= 5 h

    energy = {**base, "soc_min": float(soc.min())}
    out = score(energy, {}, {**needs, "energy_reserve_frac": 0.10})
    assert out["feasible"] is False and "battery" in out["breakdown"]["failing"]


def test_energy_mode_ignores_max_night_and_credits_margin_via_phi() -> None:
    base = {
        "sun_fraction": [1.0] * 10, "earth_fraction": [1.0] * 10, "step_min": 60,
        "longest_night_h": 99, "longest_no_earth_h": 0, "longest_lit_h": 10,
        "hours_sun_above_threshold": 10, "hours_earth_above_threshold": 10,
    }
    needs = {"max_night_h": 1, "max_no_earth_h": 10, "energy_reserve_frac": 0.10}
    near = score({**base, "soc_min": 0.12}, {}, needs)
    far = score({**base, "soc_min": 0.90}, {}, needs)
    assert near["feasible"] and far["feasible"]  # longest_night_h=99 > max_night_h=1 does not matter here
    assert far["score"] > near["score"]
    ample = score({**base, "soc_min": 1.0}, {}, needs)
    assert ample["breakdown"]["layer1_R"] - far["breakdown"]["layer1_R"] < 0.01  # Phi saturates


def test_params_from_needs_endurance_form_and_tier1() -> None:
    p = params_from_needs({"battery_wh": 1000, "array_w": 300, "endurance_h": 50})
    assert p is not None and p.dark_w == pytest.approx(20.0) and p.reserve_frac == 0.10
    assert params_from_needs({"battery_wh": 1000}) is None
    assert params_from_needs({"max_night_h": 72}) is None
