"""L2 contract tests: LST from SPICE et2lst (D-633d) and no silent substitutes (D-b3dc)."""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pytest

from moonpark.hazards.lst import local_solar_time_h_from_utc
from moonpark.hazards.moon import MoonHazards
from moonpark.hazards.pcp import PolarPcpClimatology
from moonpark.hazards.temperature import ClimatologyTable
from moonpark.providers import Site

_REPO = Path(__file__).resolve().parents[1]
_DE440 = _REPO / "data" / "kernels" / "de440s.bsp"
_PCP = _REPO / "data" / "hazards" / "pcp"

needs_spice = pytest.mark.skipif(not _DE440.is_file(), reason="SPICE kernels not present")


def _spice():
    pytest.importorskip("spiceypy")
    import spiceypy as spice

    from moonpark.ephemeris.spice import KERNEL_DIR, _furnsh

    _furnsh(KERNEL_DIR)
    return spice


def _ref_lst_h(time_iso: str, lon_deg: float) -> float:
    """Reference LST in hours straight from SPICE et2lst (body 301, planetocentric, radians)."""
    spice = _spice()
    et = spice.utc2et(time_iso.replace("T", " ") + " UTC")
    hr, mn, sc = spice.et2lst(et, 301, math.radians(lon_deg), "PLANETOCENTRIC")[:3]
    return hr + mn / 60.0 + sc / 3600.0


def _circ_diff(a: float, b: float) -> float:
    return abs((a - b + 12.0) % 24.0 - 12.0)


def _hazard_unavailable_error():
    try:
        from moonpark.hazards import HazardDataUnavailable
    except ImportError:
        pytest.fail("HazardDataUnavailable missing")
    return HazardDataUnavailable


# ---------------------------------------------------------------- 1. LST from et2lst


@needs_spice
@pytest.mark.parametrize(
    "iso, expected",
    [
        ("2027-01-01T00:00:00", 9.293),
        ("2027-01-02T00:00:00", 10.104),
        ("2027-01-16T00:00:00", 21.471),
    ],
)
def test_lst_matches_et2lst_reference_values(iso: str, expected: float) -> None:
    got = local_solar_time_h_from_utc(np.datetime64(iso), 222.51)
    assert got == pytest.approx(expected, abs=0.01)


@needs_spice
@pytest.mark.parametrize(
    "iso, lon",
    [
        ("2026-07-01T00:00:00", 0.0),
        ("2026-07-01T13:45:00", 45.0),
        ("2027-03-20T06:10:00", 180.0),
        ("2027-06-15T23:59:00", 300.5),
        ("2028-02-29T12:00:00", 359.0),
        ("2027-01-01T00:00:00", 10.0),
    ],
)
def test_lst_matches_et2lst_computed_in_test(iso: str, lon: float) -> None:
    got = local_solar_time_h_from_utc(np.datetime64(iso), lon)
    assert 0.0 <= got < 24.0
    assert _circ_diff(got, _ref_lst_h(iso, lon)) < 0.01


@needs_spice
def test_lst_advances_only_about_point_eight_hours_per_earth_day() -> None:
    t0 = np.datetime64("2027-01-01T00:00:00")
    t1 = t0 + np.timedelta64(24, "h")
    d = (local_solar_time_h_from_utc(t1, 222.51) - local_solar_time_h_from_utc(t0, 222.51)) % 24.0
    assert 0.7 < d < 0.9, f"24 Earth hours must advance LST by ~0.8 h, got {d}"


@needs_spice
def test_lst_wraps_into_0_24() -> None:
    t0 = np.datetime64("2027-01-01T00:00:00")
    vals = [
        local_solar_time_h_from_utc(t0 + np.timedelta64(6 * k, "h"), lon)
        for k in range(0, 200)
        for lon in (0.0, 123.4, 359.9)
    ]
    assert all(0.0 <= v < 24.0 for v in vals)
    # a full synodic month sweeps (nearly) the whole day: values both near 0 and near 24 appear
    assert min(vals) < 1.0 and max(vals) > 23.0


@needs_spice
def test_lst_nearby_longitudes_differ_by_delta_lon_over_15() -> None:
    t = np.datetime64("2027-01-05T07:00:00")
    a = local_solar_time_h_from_utc(t, 100.0)
    b = local_solar_time_h_from_utc(t, 115.0)
    assert (b - a) % 24.0 == pytest.approx(1.0, abs=0.02)
    c = local_solar_time_h_from_utc(t, 100.15)
    assert (c - a) % 24.0 == pytest.approx(0.01, abs=0.005)


@needs_spice
def test_lst_keeps_minutes() -> None:
    t0 = np.datetime64("2027-01-01T00:00:00")
    t1 = np.datetime64("2027-01-01T00:30:00")
    d = local_solar_time_h_from_utc(t1, 222.51) - local_solar_time_h_from_utc(t0, 222.51)
    # 30 min of Earth time = 0.5 * (0.8/24) h of LST ~ 0.0167 h
    assert 0.005 < d < 0.03, f"minutes must not be dropped, got {d}"
    # and a time with minutes matches et2lst, not the hour-truncated one
    got = local_solar_time_h_from_utc(np.datetime64("2027-01-01T00:59:00"), 222.51)
    assert _circ_diff(got, _ref_lst_h("2027-01-01T00:59:00", 222.51)) < 0.01


# ---------------------------------------------------------------- 2. Diviner noon convention


def _hottest_local_times(season: str, points: list[tuple[float, float]]) -> list[float | None]:
    """Local time (h, LTIM=(NUM-1)*0.25) of the maximum Tbol at each point, scanning every bin file."""
    from moonpark.horizon import polar_stereo_xy
    from moonpark.horizon.mask import R_M

    step = 240.0 / R_M
    xy = [tuple(v / R_M for v in polar_stereo_xy(lat, lon)) for lat, lon in points]
    best: list[tuple[int, float] | None] = [None] * len(points)
    for f in sorted((_PCP / season).glob("ltim*.npz")):
        num = int(re.search(r"ltim(\d+)", f.name).group(1))
        with np.load(f) as z:
            x = np.asarray(z["x"], dtype=np.float64)
            y = np.asarray(z["y"], dtype=np.float64)
            t = np.asarray(z["tbol"], dtype=np.float32)
        for k, (xn, yn) in enumerate(xy):
            d2 = (x - xn) ** 2 + (y - yn) ** 2
            i = int(np.argmin(d2))
            if math.sqrt(float(d2[i])) <= 0.75 * step and (best[k] is None or float(t[i]) > best[k][1]):
                best[k] = (num, float(t[i]))
    return [None if b is None else (b[0] - 1) * 0.25 for b in best]


@pytest.mark.skipif(
    not (_PCP / "summer").is_dir() or len(list((_PCP / "summer").glob("ltim*.npz"))) < 80,
    reason="local PCP summer bins not present",
)
def test_diviner_pcp_hottest_local_time_median_is_near_noon() -> None:
    # 3 latitudes x 6 longitudes, 85-89.5 S, spread in longitude (18 points). Some points peak at 16-19 h
    # (terrain), so the assertion is on the median only (D-633d diviner_lst_noon_convention).
    points = [(lat, lon) for lat in (-85.0, -87.0, -89.5) for lon in (10.0, 70.0, 130.0, 190.0, 250.0, 310.0)]
    hot = [h for h in _hottest_local_times("summer", points) if h is not None]
    assert len(hot) >= 10, f"too few points with data: {len(hot)}"
    med = float(np.median(hot))
    assert abs(med - 12.0) <= 2.0, f"median hottest local time {med} h (all: {sorted(hot)})"


# ---------------------------------------------------------------- 3. No silent substitutes (D-b3dc)


def _break_spice(monkeypatch) -> None:
    pytest.importorskip("spiceypy")
    import spiceypy

    def boom(*a, **k):
        raise RuntimeError("simulated SPICE failure")

    for name in ("utc2et", "str2et", "spkpos", "spkezr", "spkcpo", "et2lst", "furnsh"):
        if hasattr(spiceypy, name):
            monkeypatch.setattr(spiceypy, name, boom)


@needs_spice
def test_season_failure_raises_and_is_not_cached(monkeypatch) -> None:
    from moonpark.hazards import pcp

    exc_cls = _hazard_unavailable_error()
    t = np.datetime64("2031-03-05T10:00:00")  # unlikely to be cached by other tests
    _spice()  # kernels loaded before the patch
    monkeypatch.setattr(pcp, "_SEASON_BY_DAY", {}, raising=False)
    with monkeypatch.context() as m:
        _break_spice(m)
        with pytest.raises(exc_cls):
            pcp._south_season(t)
        # never a silent summer, also through the public lookup
        pcp_clim = PolarPcpClimatology(root=_PCP)
        with pytest.raises(exc_cls):
            pcp_clim.at_site_time(t, -89.0, 0.0)
    # patch removed: must compute for real (no cached fallback from the failed call)
    assert pcp._south_season(t) in ("summer", "winter")
    cache = getattr(pcp, "_SEASON_BY_DAY", {})
    assert str(np.datetime64(t, "D")) not in cache or cache[str(np.datetime64(t, "D"))] in ("summer", "winter")


def _subsolar_is_south(iso: str) -> bool:
    spice = _spice()
    et = spice.utc2et(iso.replace("T", " ") + " UTC")
    pos, _ = spice.spkpos("SUN", et, "MOON_ME", "LT+S", "MOON")
    return float(pos[2]) < 0.0


def _write_bins(root: Path, season: str, nums, lat: float, lon: float, value: float) -> None:
    from moonpark.horizon import polar_stereo_xy
    from moonpark.horizon.mask import R_M

    x_m, y_m = polar_stereo_xy(lat, lon)
    d = root / season
    d.mkdir(parents=True, exist_ok=True)
    for n in nums:
        np.savez_compressed(
            d / f"ltim{n:02d}.npz",
            x=np.array([x_m / R_M], dtype=np.float32),
            y=np.array([y_m / R_M], dtype=np.float32),
            tbol=np.array([value], dtype=np.float32),
            r_km=np.float32(1737.4),
        )


@needs_spice
def test_missing_season_bin_does_not_fall_back_to_other_season(tmp_path) -> None:
    # Winter bins exist for every local-time bin; summer has none.
    _write_bins(tmp_path, "winter", range(1, 97), -89.0, 0.0, 111.0)
    summer_iso = next(
        f"2027-{m:02d}-15T00:00:00" for m in range(1, 13) if _subsolar_is_south(f"2027-{m:02d}-15T00:00:00")
    )
    winter_iso = next(
        f"2027-{m:02d}-15T00:00:00" for m in range(1, 13) if not _subsolar_is_south(f"2027-{m:02d}-15T00:00:00")
    )
    pcp = PolarPcpClimatology(root=tmp_path)
    temp, meta = pcp.at_site_time(np.datetime64(summer_iso), -89.0, 0.0)
    assert temp is None, f"summer request must not use winter bin (got {temp})"
    assert meta["status"] == "missing_pcp_bin"
    assert meta["season"] == "summer"
    assert pcp.sigma_at_site_time(np.datetime64(summer_iso), -89.0, 0.0) is None
    # control: a winter request is served by the winter bins
    temp_w, meta_w = pcp.at_site_time(np.datetime64(winter_iso), -89.0, 0.0)
    assert temp_w == pytest.approx(111.0)
    assert meta_w["season"] == "winter"


def _tmp_raster(path: Path, lat: float, lon: float, value: float, nodata: float | None):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin

    from moonpark.horizon import polar_stereo_xy

    x, y = polar_stereo_xy(lat, lon)
    arr = np.full((11, 11), value, dtype=np.float32)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=11,
        width=11,
        count=1,
        dtype="float32",
        transform=from_origin(x - 550.0, y + 550.0, 100.0, 100.0),
        nodata=nodata,
    ) as dst:
        dst.write(arr, 1)


def _full_table() -> ClimatologyTable:
    return ClimatologyTable(bins_k={i: 250.0 for i in range(96)}, season="summer")


_SITE = Site(lat_deg=-89.0, lon_deg=1.5)
_TIMES = np.array(["2027-01-01T00:00", "2027-01-01T06:00"], dtype="datetime64[h]")


def _assert_slope_unavailable(out: dict) -> None:
    for h in out["hours"]:
        assert h["slope_deg"] is None
        assert h["soil_resistance"] is None
    assert out["aggregate"]["slope_deg"] is None
    assert out["aggregate"]["soil_resistance"] is None
    for u in (out.get("unavailable"), out["aggregate"].get("unavailable")):
        assert u and isinstance(u.get("soil_resistance"), str) and u["soil_resistance"]
        assert "temperature" not in u  # only what is missing is listed


def test_missing_slope_file_gives_none_not_zero(tmp_path) -> None:
    mh = MoonHazards(climatology=_full_table(), slope_path=tmp_path / "nope.tif", psr_path=tmp_path / "nopsr.tif")
    out = mh.hazards(_SITE, _TIMES)
    _assert_slope_unavailable(out)
    assert out["aggregate"]["temperature_k"] == 250.0  # other fields unaffected


def test_site_outside_slope_raster_gives_none_not_zero(tmp_path) -> None:
    slope = tmp_path / "slope.tif"
    _tmp_raster(slope, -89.0, 1.5, 5.0, nodata=-9999.0)
    far = Site(lat_deg=-75.0, lon_deg=1.5)  # thousands of metres away from the 1.1 km raster
    mh = MoonHazards(climatology=_full_table(), slope_path=slope, psr_path=tmp_path / "nopsr.tif")
    _assert_slope_unavailable(mh.hazards(far, _TIMES))


def test_nodata_slope_pixel_gives_none_not_zero(tmp_path) -> None:
    slope = tmp_path / "slope.tif"
    _tmp_raster(slope, -89.0, 1.5, -9999.0, nodata=-9999.0)
    mh = MoonHazards(climatology=_full_table(), slope_path=slope, psr_path=tmp_path / "nopsr.tif")
    _assert_slope_unavailable(mh.hazards(_SITE, _TIMES))


def test_valid_slope_has_no_unavailable_entry(tmp_path) -> None:
    slope = tmp_path / "slope.tif"
    _tmp_raster(slope, -89.0, 1.5, 5.0, nodata=-9999.0)
    mh = MoonHazards(climatology=_full_table(), slope_path=slope, psr_path=tmp_path / "nopsr.tif")
    out = mh.hazards(_SITE, _TIMES)
    assert out["hours"][0]["slope_deg"] == pytest.approx(5.0)
    assert out["hours"][0]["soil_resistance"] is not None
    assert not out.get("unavailable")
    assert not out["aggregate"].get("unavailable")


def test_missing_temperature_is_listed_as_unavailable(tmp_path) -> None:
    slope = tmp_path / "slope.tif"
    _tmp_raster(slope, -89.0, 1.5, 5.0, nodata=-9999.0)
    empty_pcp = PolarPcpClimatology(root=tmp_path / "emptypcp")
    mh = MoonHazards(climatology=empty_pcp, slope_path=slope, psr_path=tmp_path / "nopsr.tif")
    out = mh.hazards(_SITE, _TIMES)
    assert out["aggregate"]["temperature_k"] is None
    for u in (out.get("unavailable"), out["aggregate"].get("unavailable")):
        assert u and isinstance(u.get("temperature"), str) and u["temperature"]
        assert "soil_resistance" not in u
    assert out["hours"][0]["soil_resistance"] is not None  # slope was fine


def test_missing_psr_map_is_silent_and_harmless(tmp_path) -> None:
    slope = tmp_path / "slope.tif"
    _tmp_raster(slope, -89.0, 1.5, 5.0, nodata=-9999.0)
    mh = MoonHazards(climatology=_full_table(), slope_path=slope, psr_path=tmp_path / "nopsr.tif")
    out = mh.hazards(_SITE, _TIMES)
    assert out["psr_precheck"]["in_psr"] is False
    assert out["aggregate"]["psr"]["in_psr"] is False
    assert not out.get("unavailable")
    assert not out["aggregate"].get("unavailable")
    assert out["aggregate"]["temperature_k"] == 250.0
    assert out["aggregate"]["slope_deg"] == pytest.approx(5.0)
    assert out["aggregate"]["soil_resistance"] is not None
