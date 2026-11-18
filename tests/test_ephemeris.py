"""Success X: SpiceEphemeris.sky against saved Horizons apparent az/el.

D-20261114-pj-9e53, D-20261114-pj-4ffe, D-20261114-pj-41fa.
Azimuth is from north through east. Elevation is above the smooth horizon.
0.05 deg is a working bound, about one fifth of the solar radius. The
D-4ffe tolerance remains deferred.

Skipped only when data/kernels/de440s.bsp or spiceypy is absent (CI).
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from horizons_parse import HorizonsRow, parse_horizons_azel
from moonpark.ephemeris import SpiceEphemeris
from moonpark.providers import Site, SkySample

_REPO = Path(__file__).resolve().parents[1]
_DE440 = _REPO / "data" / "kernels" / "de440s.bsp"
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "horizons"

# Working comparison bound. D-4ffe has not locked a tolerance yet.
WORKING_BOUND_DEG = 0.05

SITES = {
    "Site01": Site(lat_deg=-89.46316, lon_deg=222.51045, height_m=0.0),
    "Site04": Site(lat_deg=-89.76681, lon_deg=188.13010, height_m=0.0),
    "Site07": Site(lat_deg=-88.81101, lon_deg=123.69007, height_m=0.0),
}

# site, window start, window stop (inclusive), 6 h step.
CASES = [
    ("Site01", "2027-01-01", "2027-03-01"),
    ("Site07", "2027-07-01", "2027-09-01"),
    ("Site04", "2027-01-01", "2027-03-01"),
    ("Site04", "2027-07-01", "2027-09-01"),
    ("Site01", "2027-07-01", "2027-09-01"),
    ("Site07", "2027-01-01", "2027-03-01"),
]


def circular_abs_delta_deg(a: float, b: float) -> float:
    """Circular |Δaz| = min(|d|, 360-|d|), with d folded into [0, 360)."""
    d = abs(float(a) - float(b)) % 360.0
    return min(d, 360.0 - d)


def _require_spice_kernels() -> None:
    if not _DE440.is_file():
        pytest.skip("data/kernels/de440s.bsp is not present")
    pytest.importorskip("spiceypy")


def _stamp(iso_date: str) -> str:
    return iso_date.replace("-", "")


def _fixture(site_name: str, start: str, stop: str, body: str) -> Path:
    name = f"{site_name}_{_stamp(start)}_{_stamp(stop)}_{body}.txt"
    return _FIXTURES / name


def _inclusive_step_count(start: str, stop: str, step_h: int = 6) -> int:
    t0 = np.datetime64(start, "s")
    t1 = np.datetime64(stop, "s")
    steps = (t1 - t0) / np.timedelta64(step_h, "h")
    return int(steps) + 1


def test_circular_az_delta_359_vs_1_is_2_deg() -> None:
    assert circular_abs_delta_deg(359.0, 1.0) == pytest.approx(2.0)
    assert circular_abs_delta_deg(1.0, 359.0) == pytest.approx(2.0)
    assert circular_abs_delta_deg(10.0, 12.5) == pytest.approx(2.5)
    assert circular_abs_delta_deg(0.0, 180.0) == pytest.approx(180.0)


@pytest.mark.parametrize(
    ("site_name", "start", "stop"),
    CASES,
    ids=[f"{site}-{start[:7]}" for site, start, _stop in CASES],
)
def test_sky_matches_horizons_apparent_azel(
    site_name: str, start: str, stop: str
) -> None:
    _require_spice_kernels()
    label = f"{site_name} {start}..{stop}"
    site = SITES[site_name]
    sun_path = _fixture(site_name, start, stop, "sun")
    earth_path = _fixture(site_name, start, stop, "earth")
    for path in (sun_path, earth_path):
        text = path.read_text(encoding="utf-8")
        assert "Azi_(a-app)" in text, label
        assert "Elev_(a-app)" in text, label
        assert "MEAN_ME" in text, label
        assert "AIRLESS" in text, label

    sun_rows = parse_horizons_azel(sun_path)
    earth_rows = parse_horizons_azel(earth_path)
    n = _inclusive_step_count(start, stop)
    assert len(sun_rows) == n, f"{label}: sun fixture has {len(sun_rows)} rows, window has {n}"
    assert len(earth_rows) == n, (
        f"{label}: earth fixture has {len(earth_rows)} rows, window has {n}"
    )
    assert [row.time_utc for row in sun_rows] == [row.time_utc for row in earth_rows], (
        f"{label}: sun and earth timestamps differ"
    )

    times = np.array([row.time_utc for row in sun_rows], dtype="datetime64[s]")
    sky = SpiceEphemeris().sky(site, times)

    assert len(sky) == n, (
        f"{label}: SpiceEphemeris.sky returned {len(sky)} samples; "
        f"Horizons fixture has {n} paired sun/earth timestamps"
    )
    _assert_samples(label, sky, sun_rows, earth_rows)
    _assert_within_working_bound(label, sky, sun_rows, earth_rows)


def _assert_samples(
    label: str,
    sky: list[SkySample],
    sun_rows: list[HorizonsRow],
    earth_rows: list[HorizonsRow],
) -> None:
    for i, (sample, sun, earth) in enumerate(
        zip(sky, sun_rows, earth_rows, strict=True)
    ):
        assert isinstance(sample, SkySample), label
        got_t = np.datetime64(sample.time_utc, "s")
        assert got_t == sun.time_utc, f"{label} sample {i} time {got_t} != {sun.time_utc}"
        assert got_t == earth.time_utc
        for field in (
            "sun_az_deg",
            "sun_el_deg",
            "earth_az_deg",
            "earth_el_deg",
            "sun_radius_deg",
            "earth_radius_deg",
        ):
            value = float(getattr(sample, field))
            assert math.isfinite(value), f"{label} sample {i} {field}={value!r}"
        assert sample.sun_radius_deg > 0, (
            f"{label} sample {i} sun_radius_deg={sample.sun_radius_deg}"
        )
        assert sample.earth_radius_deg > 0, (
            f"{label} sample {i} earth_radius_deg={sample.earth_radius_deg}"
        )


def _assert_within_working_bound(
    label: str,
    sky: list[SkySample],
    sun_rows: list[HorizonsRow],
    earth_rows: list[HorizonsRow],
) -> None:
    max_sun_az = max(
        circular_abs_delta_deg(sample.sun_az_deg, row.az_deg)
        for sample, row in zip(sky, sun_rows, strict=True)
    )
    max_earth_az = max(
        circular_abs_delta_deg(sample.earth_az_deg, row.az_deg)
        for sample, row in zip(sky, earth_rows, strict=True)
    )
    max_sun_el = max(
        abs(sample.sun_el_deg - row.el_deg)
        for sample, row in zip(sky, sun_rows, strict=True)
    )
    max_earth_el = max(
        abs(sample.earth_el_deg - row.el_deg)
        for sample, row in zip(sky, earth_rows, strict=True)
    )
    worst = max(max_sun_az, max_earth_az, max_sun_el, max_earth_el)
    assert worst < WORKING_BOUND_DEG, (
        f"{label}: working bound {WORKING_BOUND_DEG} deg "
        f"(D-4ffe tolerance remains deferred). "
        f"measured max |Δel| sun={max_sun_el:.6f} earth={max_earth_el:.6f} deg; "
        f"max circular |Δaz| sun={max_sun_az:.6f} earth={max_earth_az:.6f} deg"
    )
