# S4 + P13: layer 0 surface minima zero the score; layer 1 is normalized slack;
# layer 2 hazard weights remain deferred.

from __future__ import annotations

import pytest

from lunar_eval.score import score


def test_night_above_planner_maximum_is_infeasible() -> None:
    result = score(
        series={
            "longest_night_h": 60,
            "longest_no_earth_h": 10,
            "any_both": True,
        },
        hazards={},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "require_both": False,
        },
    )

    assert result["feasible"] is False
    assert result["score"] == 0
    assert "night" in str(result["breakdown"]).lower()


def test_feasible_plan_scores_by_smallest_normalized_slack() -> None:
    result = score(
        series={
            "longest_night_h": 40,
            "longest_no_earth_h": 10,
            "any_both": True,
        },
        hazards={},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "require_both": False,
        },
    )

    assert result["feasible"] is True
    assert 0 < result["score"] < 1
    assert result["score"] == pytest.approx(0.2)
    assert {"schedule_version", "score_formula"} & result["provenance"].keys()


def test_required_simultaneous_sun_and_earth_is_a_hard_minimum() -> None:
    result = score(
        series={
            "longest_night_h": 40,
            "longest_no_earth_h": 10,
            "any_both": False,
        },
        hazards={},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "require_both": True,
        },
    )

    assert result["feasible"] is False
    assert result["score"] == 0
    assert "both" in str(result["breakdown"]).lower()


def test_surface_temperature_above_planner_maximum_is_infeasible() -> None:
    result = score(
        series={
            "longest_night_h": 40,
            "longest_no_earth_h": 10,
            "any_both": True,
        },
        hazards={"aggregate": {"temperature_k": 400.0, "soil_resistance": 1e6}},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "max_temperature_k": 350.0,
            "require_both": False,
        },
    )

    assert result["feasible"] is False
    assert result["score"] == 0
    assert "temperature" in result["breakdown"]["failing"]


def test_surface_soil_resistance_below_minimum_is_infeasible() -> None:
    result = score(
        series={
            "longest_night_h": 40,
            "longest_no_earth_h": 10,
            "any_both": True,
        },
        hazards={"aggregate": {"temperature_k": 250.0, "soil_resistance": 100.0}},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "min_soil_resistance": 500.0,
            "require_both": False,
        },
    )

    assert result["feasible"] is False
    assert "dust" in result["breakdown"]["failing"]
