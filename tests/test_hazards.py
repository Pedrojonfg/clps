from __future__ import annotations

import numpy as np
import pytest

from moonpark.hazards.fill import fill_nodata_quadrant_idw
from moonpark.hazards.lst import lst_bin_index, local_solar_time_h_from_utc
from moonpark.hazards.moon import MoonHazards, aggregate_hazards
from moonpark.hazards.pcp import PolarPcpClimatology
from moonpark.hazards.soil import soil_resistance
from moonpark.hazards.temperature import ClimatologyTable
from moonpark.providers import Site
from moonpark.score import score


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


def test_soil_resistance_decreases_with_slope_metzger_beta() -> None:
    # D-06cb β rule, D-c82e constants: R = ρgD·cos(θ)+α in J/m³; slope must now be visible
    flat = soil_resistance(0.0)
    steep = soil_resistance(45.0)
    assert steep < flat
    assert flat == pytest.approx(1300.0 * 1.62 * (1.5 * 2.3 * 77.5e-6) + 0.289)
    assert flat == pytest.approx(0.85, abs=0.01)
    assert (flat - steep) / flat > 0.15  # with α in J/m³ the grain term is ~2/3 of the total


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
    dust = h0["provenance"]["soil_resistance"]
    assert dust["metzger_slope_factor"] == "cos_theta_on_grain_term_only"
    assert dust["label"] == "soil_erodibility_resistance_not_lofting_rate"


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


def test_polar_pcp_samples_nearest_point(tmp_path) -> None:
    # Synthetic summer ltim01 around lon=0, lat=-89 (normalized stereo).
    from moonpark.horizon import polar_stereo_xy
    from moonpark.horizon.mask import R_M

    x_m, y_m = polar_stereo_xy(-89.0, 0.0)
    xn, yn = x_m / R_M, y_m / R_M
    season_dir = tmp_path / "summer"
    season_dir.mkdir()
    np.savez_compressed(
        season_dir / "ltim01.npz",
        x=np.array([xn], dtype=np.float32),
        y=np.array([yn], dtype=np.float32),
        tbol=np.array([210.0], dtype=np.float32),
        r_km=np.float32(1737.4),
    )
    pcp = PolarPcpClimatology(root=tmp_path)
    val, meta = pcp.at_site_time(np.datetime64("2027-01-01T00:00"), -89.0, 0.0)
    assert val == pytest.approx(210.0)
    assert meta["lst_bin"] == 0
    assert meta["product"].startswith("urn:nasa:pds:lro_diviner_derived1")

def test_spread_k_is_spatial_only() -> None:
    from moonpark.hazards.pcp import R_M, _BinCache, spread_k

    n = 100
    step = 240.0 / R_M
    gx = (np.arange(n) % 10) * step
    gy = (np.arange(n) // 10) * step
    uniform = _BinCache(x=gx, y=gy, tbol=np.full(n, 85.0, dtype=np.float32))
    ramp = _BinCache(x=gx, y=gy, tbol=np.linspace(80.0, 90.0, n).astype(np.float32))
    assert spread_k(uniform, gx[0], gy[0], radii_m=(1000.0,)) == 0.0
    assert spread_k(ramp, gx[0], gy[0], radii_m=(1000.0,)) > 0.0
    # The radius widens until 4 pixels are found: a tight first radius falls through to the next one.
    assert spread_k(ramp, gx[0], gy[0], radii_m=(10.0, 1000.0)) == spread_k(ramp, gx[0], gy[0], radii_m=(1000.0,))
    # Fewer than 4 pixels near the site: no spread (the margin then stays layer 0 only).
    assert spread_k(_BinCache(x=gx[:2], y=gy[:2], tbol=ramp.tbol[:2]), gx[0], gy[0]) is None
