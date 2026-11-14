"""S6 local search: nearest feasible time and better neighbours (D-de42)."""

from __future__ import annotations

import numpy as np
import pytest

from lunar_eval.horizon import polar_stereo_xy
from lunar_eval.providers import Site
from lunar_eval.score import score
from lunar_eval.search import better_neighbours, nearest_feasible_time

NEEDS = {
    "max_night_h": 50,
    "max_no_earth_h": 20,
    "require_both": False,
}

HAZARDS: dict = {}


def _feasible_series(
    longest_night_h: int = 40,
    longest_no_earth_h: int = 10,
    **extra: object,
) -> dict:
    return {
        "longest_night_h": longest_night_h,
        "longest_no_earth_h": longest_no_earth_h,
        "any_both": True,
        **extra,
    }


def _infeasible_series(longest_night_h: int = 60, longest_no_earth_h: int = 10) -> dict:
    return {
        "longest_night_h": longest_night_h,
        "longest_no_earth_h": longest_no_earth_h,
        "any_both": True,
    }


def _planar_distance_km(a: Site, b: Site) -> float:
    ax, ay = polar_stereo_xy(a.lat_deg, a.lon_deg)
    bx, by = polar_stereo_xy(b.lat_deg, b.lon_deg)
    return float(np.hypot(ax - bx, ay - by) / 1000.0)


def test_nearest_feasible_time_picks_later_window_when_only_future_is_feasible() -> None:
    t0 = np.datetime64("2026-06-01T12:00")
    later = t0 + np.timedelta64(3, "h")
    times = np.array([t0, later], dtype="datetime64[ns]")
    series_per_window = [_infeasible_series(), _feasible_series()]

    result = nearest_feasible_time(times, series_per_window, NEEDS, t0)

    expected_score = score(series_per_window[1], HAZARDS, NEEDS)
    assert result is not None
    assert result["index"] == 1
    assert result["time"] == later
    assert result["score"]["feasible"] is True
    assert result["score"]["score"] == pytest.approx(expected_score["score"])


def test_nearest_feasible_time_none_when_no_window_is_feasible() -> None:
    t0 = np.datetime64("2026-06-01T12:00")
    times = np.array(
        [t0 - np.timedelta64(1, "h"), t0, t0 + np.timedelta64(2, "h")],
        dtype="datetime64[ns]",
    )
    series_per_window = [_infeasible_series() for _ in times]

    assert nearest_feasible_time(times, series_per_window, NEEDS, t0) is None


def test_nearest_feasible_time_prefers_closer_past_over_farther_future() -> None:
    t0 = np.datetime64("2026-06-01T12:00")
    earlier = t0 - np.timedelta64(1, "h")
    later = t0 + np.timedelta64(3, "h")
    times = np.array([earlier, t0, later], dtype="datetime64[ns]")
    series_per_window = [
        _feasible_series(),
        _infeasible_series(),
        _feasible_series(longest_night_h=35),
    ]

    result = nearest_feasible_time(times, series_per_window, NEEDS, t0)

    assert result is not None
    assert result["index"] == 0
    assert result["time"] == earlier


def test_better_neighbours_returns_feasible_candidate_inside_radius() -> None:
    origin = Site(lat_deg=-89.5, lon_deg=0.0)
    neighbour = Site(lat_deg=-89.5, lon_deg=0.01)
    assert _planar_distance_km(origin, neighbour) < 5.0

    feasible = _feasible_series()
    candidates = [(neighbour, feasible)]

    result = better_neighbours(origin, candidates, NEEDS, radius_km=5.0)

    expected_score = score(feasible, HAZARDS, NEEDS)
    assert result is not None
    assert result["site"] == neighbour
    assert result["series"] is feasible
    assert result["score"]["feasible"] is True
    assert result["score"]["score"] == pytest.approx(expected_score["score"])


def test_better_neighbours_none_when_only_feasible_candidate_outside_radius() -> None:
    origin = Site(lat_deg=-89.5, lon_deg=0.0)
    distant = Site(lat_deg=-89.5, lon_deg=2.0)
    dist_km = _planar_distance_km(origin, distant)
    radius_km = dist_km * 0.5

    infeasible_near = Site(lat_deg=-89.5, lon_deg=0.005)
    assert _planar_distance_km(origin, infeasible_near) <= radius_km

    candidates = [
        (infeasible_near, _infeasible_series()),
        (distant, _feasible_series()),
    ]

    assert better_neighbours(origin, candidates, NEEDS, radius_km=radius_km) is None


def test_better_neighbours_picks_higher_score_among_feasible_inside_radius() -> None:
    origin = Site(lat_deg=-89.5, lon_deg=0.0)
    site_low = Site(lat_deg=-89.5, lon_deg=0.008)
    site_high = Site(lat_deg=-89.5, lon_deg=0.012)
    for site in (site_low, site_high):
        assert _planar_distance_km(origin, site) < 2.0

    series_low = _feasible_series(longest_night_h=40, longest_no_earth_h=10)
    series_high = _feasible_series(longest_night_h=25, longest_no_earth_h=5)
    assert score(series_high, HAZARDS, NEEDS)["score"] > score(series_low, HAZARDS, NEEDS)["score"]

    candidates = [(site_low, series_low), (site_high, series_high)]

    result = better_neighbours(origin, candidates, NEEDS, radius_km=2.0)

    expected_score = score(series_high, HAZARDS, NEEDS)
    assert result is not None
    assert result["site"] == site_high
    assert result["series"] is series_high
    assert result["score"]["score"] == pytest.approx(expected_score["score"])