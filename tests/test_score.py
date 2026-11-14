# S4 locked defaults: layer 1 is normalized hours of slack, layer 2 is
# neutral (hazards ignored until P13), and feasible minima combine by minimum
# normalized slack; infeasible plans score zero, with no global-best comparison.

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


def test_surface_hazards_do_not_make_an_otherwise_valid_plan_infeasible() -> None:
    result = score(
        series={
            "longest_night_h": 40,
            "longest_no_earth_h": 10,
            "any_both": True,
        },
        hazards={"temperature": 999},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "require_both": False,
        },
    )

    assert result["feasible"] is True
    assert result["score"] == pytest.approx(0.2)
