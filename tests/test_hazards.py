from __future__ import annotations

import numpy as np
import pytest

from lunar_eval.hazards.fill import fill_nodata_quadrant_idw
from lunar_eval.hazards.lst import lst_bin_index, local_solar_time_h_from_utc
from lunar_eval.hazards.moon import MoonHazards, aggregate_hazards
from lunar_eval.hazards.soil import soil_resistance
from lunar_eval.hazards.temperature import ClimatologyTable
from lunar_eval.providers import Site
from lunar_eval.score import score


def test_quadrant_idw_fills_centre_from_neighbors() -> None:
    g = np.full((5, 5), np.nan)
    g[0, 0] = 10.0
    g[0, 4] = 20.0
    g[4, 4] = 30.0
    g[4, 0] = 40.0
    val, meta = fill_nodata_quadrant_idw(g)
    assert val is not None
    assert meta["fill"] == "four_quadrant_inverse_distance"
    assert val == pytest.approx(25.0)


def test_soil_resistance_increases_with_slope() -> None:
    flat = soil_resistance(0.0)
    steep = soil_resistance(45.0)
    assert steep > flat


def test_climatology_lookup_by_lst_bin() -> None:
    table = ClimatologyTable(bins_k={0: 100.0, 1: 110.0}, season="summer")
    k, prov = table.at_lst(0.1)
    assert k == 100.0
    assert prov["lst_bin"] == 0
    k2, _ = table.at_lst(0.26)
    assert k2 == 110.0


def test_moon_hazards_returns_hourly_contract() -> None:
    site = Site(lat_deg=-89.0, lon_deg=1.5)
    times = np.array(["2026-07-01T00:00"], dtype="datetime64[h]")
    table = ClimatologyTable(bins_k={0: 250.0}, season="summer")
    mh = MoonHazards(climatology=table, slope_path=None, psr_path=None)
    out = mh.hazards(site, times)
    assert len(out["hours"]) == 1
    h0 = out["hours"][0]
    assert set(h0) >= {"temperature_k", "soil_resistance", "slope_deg", "psr", "provenance"}
    assert out["aggregate"]["temperature_k"] == 250.0


def test_score_uses_worst_temperature_across_hours() -> None:
    hours = [
        {"temperature_k": 300.0, "soil_resistance": 1e6},
        {"temperature_k": 360.0, "soil_resistance": 1e6},
    ]
    agg = aggregate_hazards([{**h, "slope_deg": 0, "psr": {}} for h in hours])
    result = score(
        series={"longest_night_h": 1, "longest_no_earth_h": 1, "any_both": True},
        hazards={"aggregate": agg},
        needs={"max_night_h": 50, "max_no_earth_h": 50, "max_temperature_k": 350.0},
    )
    assert result["feasible"] is False


def test_lst_bin_index_wraps_daily_grid() -> None:
    assert lst_bin_index(23.9) == lst_bin_index(23.9 % 24)


def test_local_solar_time_shifts_with_longitude() -> None:
    t = np.datetime64("2026-01-01T00:00")
    lst0 = local_solar_time_h_from_utc(t, 0.0)
    lst_east = local_solar_time_h_from_utc(t, 90.0)
    assert lst_east == pytest.approx((lst0 + 6.0) % 24.0)