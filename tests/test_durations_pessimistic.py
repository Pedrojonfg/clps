"""Pessimistic interval durations on a closed sample grid (D-20261118-pj-9413)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from moonpark.energy import EnergyParams, soc_series
from moonpark.providers import HorizonMask, SkySample
from moonpark.score import score
from moonpark.visibility import series

RS = 0.2665
T0 = np.datetime64("2027-06-01T00:00:00")


def _horizon() -> HorizonMask:
    return HorizonMask(
        elevation_deg=np.zeros(720, dtype=np.float32),
        x_m=0.0,
        y_m=0.0,
        lat=-89.46316,
        lon=222.51045,
        h0_m=0.0,
        observer_height_m=2.0,
        schedule_version="test",
        dem_ids=(),
    )


def _sky(sun_el, earth_el=None, step_min: int = 60) -> list[SkySample]:
    """Synthetic sky over a flat 0 deg horizon: elevation +20 is fully lit, -20 fully dark."""
    earth_el = sun_el if earth_el is None else earth_el
    return [
        SkySample(
            T0 + np.timedelta64(i * step_min, "m"),
            sun_az_deg=0.0,
            sun_el_deg=float(s),
            sun_radius_deg=RS,
            earth_az_deg=0.0,
            earth_el_deg=float(e),
            earth_radius_deg=0.5,
        )
        for i, (s, e) in enumerate(zip(sun_el, earth_el, strict=True))
    ]


def _els(pattern: str) -> list[float]:
    return [20.0 if c == "L" else -20.0 for c in pattern]


def _run(pattern: str, *, earth: str | None = None, step_min: int = 60, **kw) -> dict:
    return series(
        _sky(_els(pattern), None if earth is None else _els(earth), step_min),
        _horizon(),
        step_min=step_min,
        **kw,
    )


# ---------------------------------------------------------------- maximum-type: upper bound

def test_night_is_upper_bound_hole_to_hole() -> None:
    out = _run("LDDDLL")  # 3 dark samples between lit ones: 4 h (not 3, not 2)
    assert out["longest_night_h"] == 4


def test_night_lower_bound_exposed() -> None:
    out = _run("LDDDLL")
    assert out["longest_night_h_lower"] == 2
    assert out["longest_night_h_lower"] <= out["longest_night_h"]


def test_single_dark_sample_upper_two_lower_zero() -> None:
    out = _run("LLDLL")
    assert out["longest_night_h"] == 2
    assert out["longest_night_h_lower"] == 0


def test_night_run_touching_start_edge_is_clipped_to_window() -> None:
    out = _run("DDLLL")  # run i=0..1; upper = t_2 - t_0 = 2 h
    assert out["longest_night_h"] == 2
    assert out["longest_night_h_lower"] == 1


def test_night_run_touching_end_edge_is_clipped_to_window() -> None:
    out = _run("LLLDD")  # run i=3..4; upper = t_4 - t_2 = 2 h
    assert out["longest_night_h"] == 2
    assert out["longest_night_h_lower"] == 1


def test_all_dark_window_is_whole_window_length() -> None:
    out = _run("D" * 25)
    assert out["longest_night_h"] == 24
    assert out["longest_night_h_lower"] == 24


def test_night_takes_max_over_runs() -> None:
    out = _run("LDLDDDLL")  # runs: upper 2 h and 4 h
    assert out["longest_night_h"] == 4


def test_no_earth_uses_same_upper_and_lower_bounds() -> None:
    out = _run("LLLLLL", earth="LDDDLL")
    assert out["longest_no_earth_h"] == 4
    assert out["longest_no_earth_h_lower"] == 2


def test_ten_minute_night_upper_bound() -> None:
    out = _run("LDDDLL", step_min=10)
    assert out["longest_night_h"] == pytest.approx(40 / 60)
    assert out["longest_night_h_lower"] == pytest.approx(20 / 60)


# ---------------------------------------------------------------- minimum-type: lower bound

def test_longest_lit_is_last_minus_first() -> None:
    out = _run("DLLLDD")  # 3 lit samples: 2 h (not 3)
    assert out["longest_lit_h"] == 2


def test_longest_lit_upper_bound_exposed() -> None:
    out = _run("DLLLDD")
    assert out["longest_lit_h_upper"] == 4  # t_4 - t_0
    assert out["longest_lit_h"] <= out["longest_lit_h_upper"]


def test_single_lit_sample_is_zero_hours() -> None:
    out = _run("DDLDD")
    assert out["longest_lit_h"] == 0
    assert out["hours_sun_above_threshold"] == 0
    assert out["longest_lit_h_upper"] == 2


def test_lit_run_touching_edges_clipped() -> None:
    out = _run("LLLDD")
    assert out["longest_lit_h"] == 2
    assert out["longest_lit_h_upper"] == 3  # t_3 - t_0
    out = _run("DDLLL")
    assert out["longest_lit_h"] == 2
    assert out["longest_lit_h_upper"] == 3  # t_4 (window end) - t_1


def test_total_lit_is_sum_of_per_run_lower_bounds() -> None:
    out = _run("LLDLLLDLD")  # runs: 1 h, 2 h, 0 h
    assert out["hours_sun_above_threshold"] == 3
    assert out["longest_lit_h"] == 2


def test_total_earth_is_sum_of_per_run_lower_bounds() -> None:
    out = _run("LLLLLLLLL", earth="LLDLLLDLD")
    assert out["hours_earth_above_threshold"] == 3


def test_bridge_gap_preserved_on_lower_bound() -> None:
    # A single dark hourly sample may hide a gap of up to 2 h (hole to hole), so it is bridged only by
    # bridge_h >= 2 (pessimistic bridge, reviewer fix). LL D LL bridged -> one run from sample 0 to 4 = 4 h.
    out = _run("LLDLL", bridge_h=2)
    assert out["longest_lit_h"] == 4
    # bridge_h = 1 h is shorter than the gap's upper bound (2 h): stays split, 1 h (was bridged before the fix)
    out = _run("LLDLL", bridge_h=1)
    assert out["longest_lit_h"] == 1
    # gap longer than bridge_h stays split: 1 h
    out = _run("LLDDLL", bridge_h=1)
    assert out["longest_lit_h"] == 1


def test_lit_values_ordered_lower_le_upper() -> None:
    for pat in ("DLLLDD", "LLDLLLDLD", "LDLDLDL", "L" * 7, "D" * 7):
        out = _run(pat)
        assert out["longest_lit_h"] <= out["longest_lit_h_upper"], pat


def test_threshold_is_strictly_greater() -> None:
    # fraction exactly == threshold is dark: threshold 1.0 makes fully lit samples (fraction 1.0) dark.
    out = _run("LLLL", sun_threshold=1.0)
    assert out["hours_sun_above_threshold"] == 0
    assert out["longest_night_h"] == 3  # all dark: whole window t_3 - t_0


# ---------------------------------------------------------------- resolution independence

def test_all_lit_24h_window_same_at_60_and_10_min() -> None:
    for step in (60, 10):
        n = 24 * 60 // step + 1
        out = _run("L" * n, step_min=step)
        assert out["longest_lit_h"] == pytest.approx(24), step
        assert out["hours_sun_above_threshold"] == pytest.approx(24), step
        assert out["hours_earth_above_threshold"] == pytest.approx(24), step
        assert out["longest_night_h"] == 0, step


def test_all_dark_24h_window_same_at_60_and_10_min() -> None:
    for step in (60, 10):
        n = 24 * 60 // step + 1
        out = _run("D" * n, step_min=step)
        assert out["longest_night_h"] == pytest.approx(24), step
        assert out["longest_no_earth_h"] == pytest.approx(24), step


def _curve(kind: str, step_min: int) -> list[float]:
    n = 24 * 60 // step_min + 1
    h = np.arange(n) * step_min / 60.0
    if kind == "sine_half":  # lit ~half the day
        return list(8.0 * np.sin(2 * np.pi * (h - 3.0) / 24.0))
    if kind == "sine_short_day":  # lit about 4.5 h around hour 11.3
        return list(10.0 * np.sin(2 * np.pi * (h - 5.0) / 24.0) - 9.0)
    if kind == "sine_short_night":
        return list(10.0 * np.sin(2 * np.pi * (h - 5.0) / 24.0) + 9.0)
    if kind == "two_bumps":
        return list(6.0 * np.sin(2 * np.pi * h / 12.0) - 2.5)
    if kind == "sliver":  # very short lit sliver
        return list(10.0 * np.sin(2 * np.pi * (h - 5.0) / 24.0) - 9.9)
    raise AssertionError(kind)


KINDS = ("sine_half", "sine_short_day", "sine_short_night", "two_bumps", "sliver")


@pytest.mark.parametrize("kind", KINDS)
def test_coarse_values_never_more_permissive_than_fine(kind: str) -> None:
    c = series(_sky(_curve(kind, 60)), _horizon(), step_min=60)
    f = series(_sky(_curve(kind, 10), step_min=10), _horizon(), step_min=10)
    eps = 1e-9
    assert c["longest_night_h"] >= f["longest_night_h"] - eps
    assert c["longest_no_earth_h"] >= f["longest_no_earth_h"] - eps
    assert c["longest_lit_h"] <= f["longest_lit_h"] + eps
    assert c["hours_sun_above_threshold"] <= f["hours_sun_above_threshold"] + eps
    assert c["hours_earth_above_threshold"] <= f["hours_earth_above_threshold"] + eps
    # and every value is bounded by the 24 h window length
    for o in (c, f):
        assert o["longest_night_h"] <= 24 + eps
        assert o["hours_sun_above_threshold"] <= 24 + eps


@pytest.mark.parametrize("kind", KINDS)
def test_coarse_verdict_never_more_permissive_than_fine(kind: str) -> None:
    needs_grid = [
        {"max_night_h": mn, "max_no_earth_h": mn, "min_continuous_lit_h": ml, "min_total_lit_h": ml}
        for mn in (2, 5, 8, 12, 16, 20, 24)
        for ml in (0, 1, 3, 6, 10, 14)
    ]
    c = series(_sky(_curve(kind, 60)), _horizon(), step_min=60)
    f = series(_sky(_curve(kind, 10), step_min=10), _horizon(), step_min=10)
    for needs in needs_grid:
        if score(c, {}, needs)["feasible"]:
            assert score(f, {}, needs)["feasible"], (kind, needs)


def test_series_keys_consistent_lower_value_upper() -> None:
    out = _run("LDDLLLDLDDLL")
    assert out["longest_night_h_lower"] <= out["longest_night_h"]
    assert out["longest_no_earth_h_lower"] <= out["longest_no_earth_h"]
    assert out["longest_lit_h"] <= out["longest_lit_h_upper"]


# ---------------------------------------------------------------- battery intervals

def test_soc_interval_lit_only_if_both_endpoints_lit() -> None:
    p = EnergyParams(capacity_wh=100.0, array_w=40.0, dark_w=20.0)  # +20 Wh/h lit interval, -20 Wh/h dark
    frac = np.array([1.0, 1.0, 0.0, 1.0, 1.0])
    az = np.full(5, 90.0)
    el = np.zeros(5)  # tracking vertical, cos = 1
    soc = soc_series(frac, az, el, p, step_h=1.0)
    # intervals: (0,1) lit -> cap 100 ; (1,2) dark -> 80 ; (2,3) dark -> 60 ; (3,4) lit -> 80
    np.testing.assert_allclose(soc, [1.0, 1.0, 0.8, 0.6, 0.8], atol=1e-9)
    assert len(soc) == len(frac)


def test_soc_single_lit_sample_does_not_charge() -> None:
    p = EnergyParams(capacity_wh=100.0, array_w=40.0, dark_w=20.0)
    frac = np.array([0.0, 1.0, 0.0])
    soc = soc_series(frac, np.full(3, 90.0), np.zeros(3), p, step_h=1.0)
    np.testing.assert_allclose(soc, [1.0, 0.8, 0.6], atol=1e-9)


def test_soc_charges_through_series_with_hourly_lit_run() -> None:
    p = EnergyParams(capacity_wh=100.0, array_w=40.0, dark_w=20.0)
    frac = np.array([0.0, 0.0, 1.0, 1.0, 1.0, 0.0])
    soc = soc_series(frac, np.full(6, 90.0), np.zeros(6), p, step_h=1.0)
    # dark (0,1) 80, dark (1,2) 60, lit (2,3) 80, lit (3,4) 100, dark (4,5) 80
    np.testing.assert_allclose(soc, [1.0, 0.8, 0.6, 0.8, 1.0, 0.8], atol=1e-9)


# ---------------------------------------------------------------- comparator equality

def _ser(**kw) -> dict:
    base = {
        "longest_night_h": 3,
        "longest_no_earth_h": 3,
        "longest_lit_h": 10,
        "hours_sun_above_threshold": 10,
        "hours_earth_above_threshold": 10,
        "any_both": True,
        "schedule_version": "t",
    }
    base.update(kw)
    return base


def _needs(**kw) -> dict:
    base = {"max_night_h": 10, "max_no_earth_h": 10}
    base.update(kw)
    return base


def _feasible(series_: dict, needs: dict, hazards: dict | None = None) -> bool:
    return bool(score(series_, hazards or {}, needs)["feasible"])


def test_max_night_equal_fails() -> None:
    assert _feasible(_ser(longest_night_h=9), _needs(max_night_h=10))
    assert not _feasible(_ser(longest_night_h=10), _needs(max_night_h=10))
    assert not _feasible(_ser(longest_night_h=11), _needs(max_night_h=10))


def test_max_no_earth_equal_fails() -> None:
    assert _feasible(_ser(longest_no_earth_h=9), _needs(max_no_earth_h=10))
    assert not _feasible(_ser(longest_no_earth_h=10), _needs(max_no_earth_h=10))
    assert not _feasible(_ser(longest_no_earth_h=11), _needs(max_no_earth_h=10))


def test_max_temperature_equal_fails() -> None:
    n = _needs(max_temperature_k=300)
    assert _feasible(_ser(), n, {"temperature_k": 299})
    assert not _feasible(_ser(), n, {"temperature_k": 300})
    assert not _feasible(_ser(), n, {"temperature_k": 301})


def test_min_continuous_lit_equal_passes() -> None:
    n = _needs(min_continuous_lit_h=10)
    assert not _feasible(_ser(longest_lit_h=9), n)
    assert _feasible(_ser(longest_lit_h=10), n)
    assert _feasible(_ser(longest_lit_h=11), n)


def test_min_total_lit_equal_passes() -> None:
    n = _needs(min_total_lit_h=10)
    assert not _feasible(_ser(hours_sun_above_threshold=9), n)
    assert _feasible(_ser(hours_sun_above_threshold=10), n)
    assert _feasible(_ser(hours_sun_above_threshold=11), n)


def test_min_temperature_equal_passes() -> None:
    n = _needs(min_temperature_k=100)
    assert not _feasible(_ser(), n, {"temperature_k": 101, "temperature_min_k": 99})
    assert _feasible(_ser(), n, {"temperature_k": 101, "temperature_min_k": 100})
    assert _feasible(_ser(), n, {"temperature_k": 101, "temperature_min_k": 101})


def test_min_soil_resistance_equal_passes() -> None:
    n = _needs(min_soil_resistance=50)
    assert not _feasible(_ser(), n, {"soil_resistance": 49})
    assert _feasible(_ser(), n, {"soil_resistance": 50})
    assert _feasible(_ser(), n, {"soil_resistance": 51})


def test_battery_reserve_equal_passes() -> None:
    n = _needs(energy_reserve_frac=0.25)
    assert not _feasible(_ser(soc_min=0.24), n)
    assert _feasible(_ser(soc_min=0.25), n)
    assert _feasible(_ser(soc_min=0.26), n)
