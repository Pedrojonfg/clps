"""S6 local search: neighbours x time slide, ranked pick + leaderboard.

per D-9cc5 (time slide, distance_hours, leaderboard), D-72bc (radius 5 km, neighbours
always scanned, pick ordering), D-f57e (same hazards as request, hazard_gap_star rows kept),
D-5577 (infeasible rows carry display score 0 + companion_score).
"""

from __future__ import annotations

import numpy as np
import pytest

from moonpark.horizon import polar_stereo_xy
from moonpark.providers import Site
from moonpark.score import score
from moonpark.search.local import DEFAULT_RADIUS_KM, local_search, window_slide_starts

NEEDS = {"max_night_h": 50, "max_no_earth_h": 20, "require_both": False}
RADIUS_KM = 5.0  # per D-72bc local_neighbour_radius_km=5
HOURS = 4
A = np.datetime64("2026-06-01T12:00", "s")
ORIGIN = Site(lat_deg=-89.5, lon_deg=0.0)
NEAR = Site(lat_deg=-89.5, lon_deg=0.01)
NEAR_B = Site(lat_deg=-89.5, lon_deg=0.02)
FAR = Site(lat_deg=-89.5, lon_deg=20.0)  # well outside 5 km (asserted below)


def _series(night: int = 40, no_earth: int = 10) -> dict:
    return {"longest_night_h": night, "longest_no_earth_h": no_earth, "any_both": True}


def _km(a: Site, b: Site) -> float:
    ax, ay = polar_stereo_xy(a.lat_deg, a.lon_deg)
    bx, by = polar_stereo_xy(b.lat_deg, b.lon_deg)
    return float(np.hypot(ax - bx, ay - by) / 1000.0)


def _t(x) -> np.datetime64:
    return np.datetime64(str(x).replace("Z", ""), "s")


def _is_origin(site: Site) -> bool:
    return (site.lat_deg, site.lon_deg) == (ORIGIN.lat_deg, ORIGIN.lon_deg)


def _make_eval(fn):
    """fn(site, start_dt64) -> series dict (origin is forced infeasible so neighbours decide)."""

    def evaluate(site, start, hours):
        assert hours == HOURS
        if _is_origin(site):
            return {"series": _series(night=100), "hazards": {}, "hazard_gap_star": False}
        return {"series": fn(site, _t(start)), "hazards": {}, "hazard_gap_star": False}

    return evaluate


def _run(evaluate, neighbours=(NEAR,)):
    return local_search(
        ORIGIN, A, HOURS, NEEDS, evaluate=evaluate, neighbour_sites=list(neighbours), radius_km=RADIUS_KM
    )


def test_default_radius_is_five_km() -> None:
    assert DEFAULT_RADIUS_KM == 5.0
    assert _km(ORIGIN, NEAR) < RADIUS_KM < _km(ORIGIN, FAR)


def test_window_slide_starts_span_a_minus_h_to_a_plus_h_hourly() -> None:
    starts = np.asarray(window_slide_starts(A, 3)).astype("datetime64[s]")
    assert len(starts) == 7
    assert starts[0] == A - np.timedelta64(3, "h")
    assert starts[-1] == A + np.timedelta64(3, "h")
    assert A in starts
    assert set(np.diff(starts).astype("timedelta64[h]").astype(int)) == {1}


def test_pick_is_min_distance_hours_among_feasible_even_if_score_is_worse() -> None:
    # Feasible at a-1h (poor score) and a+2h (great score): nearest time wins.
    def fn(site, start):
        if start == A - np.timedelta64(1, "h"):
            return _series(night=49)
        if start == A + np.timedelta64(2, "h"):
            return _series(night=5, no_earth=1)
        return _series(night=100)

    result = _run(_make_eval(fn))
    pick = result["pick"]
    assert pick["feasible"] is True
    assert _t(pick["window_start"]) == A - np.timedelta64(1, "h")
    assert pick["distance_hours"] == pytest.approx(1.0)
    assert pick["window_hours"] == HOURS


def test_pick_tie_on_distance_hours_takes_earliest_start() -> None:
    def fn(site, start):
        if start in (A - np.timedelta64(1, "h"), A + np.timedelta64(1, "h")):
            return _series(night=40)
        return _series(night=100)

    pick = _run(_make_eval(fn))["pick"]
    assert pick["distance_hours"] == pytest.approx(1.0)
    assert _t(pick["window_start"]) == A - np.timedelta64(1, "h")


def test_same_distance_hours_prefers_higher_score_over_closer_site() -> None:
    low, high = _series(night=45), _series(night=10, no_earth=2)
    assert score(high, {}, NEEDS)["score"] > score(low, {}, NEEDS)["score"]

    def fn(site, start):
        if start != A:
            return _series(night=100)
        return low if site == NEAR else high

    pick = _run(_make_eval(fn), neighbours=(NEAR, NEAR_B))["pick"]
    assert pick["site"]["lon_deg"] == pytest.approx(NEAR_B.lon_deg)
    assert pick["score"] == pytest.approx(score(high, {}, NEEDS)["score"])


def test_equal_score_and_time_prefers_nearer_site_by_km() -> None:
    def fn(site, start):
        return _series(night=40) if start == A else _series(night=100)

    pick = _run(_make_eval(fn), neighbours=(NEAR_B, NEAR))["pick"]
    assert pick["site"]["lon_deg"] == pytest.approx(NEAR.lon_deg)
    assert pick["distance_km"] == pytest.approx(_km(ORIGIN, NEAR), rel=1e-3)


def test_no_feasible_pick_has_max_companion_with_zero_display_score() -> None:
    # per D-5577: infeasible display score 0, rank by companion_score.
    mild, bad = _series(night=52), _series(night=70)

    def fn(site, start):
        return mild if site == NEAR_B else bad

    result = _run(_make_eval(fn), neighbours=(NEAR, NEAR_B))
    pick = result["pick"]
    assert pick["feasible"] is False
    assert pick["score"] == 0
    assert pick["companion_score"] == pytest.approx(score(mild, {}, NEEDS)["companion_score"])
    assert pick["companion_score"] > score(bad, {}, NEEDS)["companion_score"] > 0
    assert pick["site"]["lon_deg"] == pytest.approx(NEAR_B.lon_deg)


def test_no_feasible_companion_tie_prefers_min_distance_hours_then_earliest() -> None:
    def fn(site, start):
        if start in (A - np.timedelta64(1, "h"), A + np.timedelta64(1, "h")):
            return _series(night=55)
        return _series(night=75)

    pick = _run(_make_eval(fn))["pick"]
    assert pick["feasible"] is False
    assert pick["distance_hours"] == pytest.approx(1.0)
    assert _t(pick["window_start"]) == A - np.timedelta64(1, "h")


def test_leaderboard_first_row_is_pick_with_required_keys_and_slide_coverage() -> None:
    def fn(site, start):
        return _series(night=40) if start == A else _series(night=100)

    result = _run(_make_eval(fn))
    board = result["leaderboard"]
    assert board and board[0] == result["pick"]
    for row in board:
        assert {
            "site",
            "window_start",
            "window_hours",
            "feasible",
            "score",
            "companion_score",
            "hazard_gap_star",
            "distance_hours",
            "distance_km",
        } <= row.keys()
        assert {"lat_deg", "lon_deg"} <= row["site"].keys()
    neighbour_starts = {
        _t(r["window_start"]) for r in board if r["site"]["lon_deg"] == pytest.approx(NEAR.lon_deg)
    }
    assert neighbour_starts == set(np.asarray(window_slide_starts(A, HOURS)).astype("datetime64[s]"))


def test_neighbour_outside_radius_is_never_scanned_or_picked() -> None:
    # Feasible far site must lose to an infeasible near site: radius filter, not score, decides.
    def fn(site, start):
        return _series(night=40) if site == FAR else _series(night=60)

    result = _run(_make_eval(fn), neighbours=(NEAR, FAR))
    assert all(r["site"]["lon_deg"] != pytest.approx(FAR.lon_deg) for r in result["leaderboard"])
    assert result["pick"]["feasible"] is False


def test_hazards_from_evaluate_gate_feasibility_and_gap_star_rows_are_kept() -> None:
    # per D-f57e: same hazards as the request; starred rows stay in the leaderboard.
    needs = {**NEEDS, "max_temperature_k": 350.0}

    def evaluate(site, start, hours):
        if _is_origin(site):
            return {"series": _series(night=100), "hazards": {}, "hazard_gap_star": False}
        if site == NEAR:
            return {
                "series": _series(),
                "hazards": {"aggregate": {"temperature_k": 400.0, "soil_resistance": 1e6}},
                "hazard_gap_star": False,
            }
        return {"series": _series(), "hazards": {}, "hazard_gap_star": True}

    result = local_search(
        ORIGIN, A, HOURS, needs, evaluate=evaluate, neighbour_sites=[NEAR, NEAR_B], radius_km=RADIUS_KM
    )
    hot = [r for r in result["leaderboard"] if r["site"]["lon_deg"] == pytest.approx(NEAR.lon_deg)]
    starred = [r for r in result["leaderboard"] if r["site"]["lon_deg"] == pytest.approx(NEAR_B.lon_deg)]
    assert hot and all(r["feasible"] is False and r["score"] == 0 and r["companion_score"] > 0 for r in hot)
    assert starred and all(r["hazard_gap_star"] is True for r in starred)
    assert result["pick"]["hazard_gap_star"] is True
    assert result["pick"]["feasible"] is True


def test_empty_neighbour_list_does_not_raise() -> None:
    # per D-72bc: no grid in prod path -> empty neighbours OK.
    result = _run(_make_eval(lambda s, t: _series()), neighbours=())
    assert set(result) >= {"pick", "leaderboard"}
