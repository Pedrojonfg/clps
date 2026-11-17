# S4 + P13: layer 0 surface minima zero the score; layer 1 is Φ-slack reliability R
# times a bounded bonus (D-7af3, D-7520, D-6ce5, D-48ee); layer 2 hazard weights remain deferred.
#
# Reference formulas (tests recompute with math.erf):
#   Φ(z)   = 0.5 * (1 + erf(z / sqrt(2)))
#   p_i    = Φ(slack_i / σ_i), σ_night = 5, σ_lit = 5, σ_no_earth = 1 (hours)
#   R      = Π p_i over active terms (night, no_earth, lit iff min_continuous_lit_h > 0)
#   B      = Σ w x / Σ w, clip [0,1]; interval terms w=0.1, scalar terms w=1.0
#   raw    = R (1 + 0.25 B); score = R * 1.40 if R > 0 and (raw - R)/R > 0.40 else raw

from __future__ import annotations

import math

import pytest

from lunar_eval.score import score

# Legacy formula id before D-7520 (do not import FORMULA — it was updated).
OLD_FORMULA = "two_layer_zero_then_assurance_then_weights"

SIGMA_NIGHT = 5.0
SIGMA_LIT = 5.0
SIGMA_NO_EARTH = 1.0
BETA = 0.25  # per D-20261115-pj-48ee
MAX_UPLIFT = 0.40  # per D-20261115-pj-48ee


def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _clip01(x: float) -> float:
    return min(1.0, max(0.0, x))


def expected_score(series: dict, needs: dict, n: int | None = None) -> tuple[float, float, float]:
    """Return (score, R, B) per the D-7520 / D-6ce5 / D-48ee contract."""
    max_night = int(needs["max_night_h"])
    max_no_earth = int(needs["max_no_earth_h"])
    min_lit = int(needs.get("min_continuous_lit_h", 0))
    s_night = max_night - int(series["longest_night_h"])
    s_ne = max_no_earth - int(series["longest_no_earth_h"])

    ps = [phi(s_night / SIGMA_NIGHT), phi(s_ne / SIGMA_NO_EARTH)]
    terms = [
        (0.1, _clip01(s_night / max(max_night, 1))),
        (0.1, _clip01(s_ne / max(max_no_earth, 1))),
    ]
    if min_lit > 0:
        s_lit = int(series["longest_lit_h"]) - min_lit
        ps.append(phi(s_lit / SIGMA_LIT))
        terms.append((0.1, _clip01(s_lit / max(min_lit, 1))))
    if n is None:
        n = len(series["sun_fraction"]) if "sun_fraction" in series else 0
    n_div = max(n, 1)
    terms.append((1.0, _clip01(int(series.get("hours_sun_above_threshold", 0)) / n_div)))
    terms.append((1.0, _clip01(int(series.get("hours_earth_above_threshold", 0)) / n_div)))

    r = math.prod(ps)
    b = _clip01(sum(w * x for w, x in terms) / sum(w for w, _ in terms))
    raw = r * (1.0 + BETA * b)
    if r > 0 and (raw - r) / r > MAX_UPLIFT:
        return r * (1.0 + MAX_UPLIFT), r, b
    return raw, r, b


def _layer1(result: dict) -> tuple[float, float]:
    bd = result["breakdown"]
    if "layer1_R" in bd:
        return bd["layer1_R"], bd["layer1_B"]
    return bd["layer1"]["R"], bd["layer1"]["B"]


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


def test_feasible_plan_scores_by_phi_reliability_times_bonus() -> None:
    series = {
        "longest_night_h": 40,
        "longest_no_earth_h": 10,
        "any_both": True,
        "hours_sun_above_threshold": 100,
        "hours_earth_above_threshold": 50,
        "sun_fraction": [0.0] * 168,
    }
    needs = {"max_night_h": 50, "max_no_earth_h": 20, "require_both": False}
    result = score(series=series, hazards={}, needs=needs)

    want, want_r, want_b = expected_score(series, needs)
    assert result["feasible"] is True
    assert 0 < result["score"] < 1.5
    assert result["score"] == pytest.approx(want, rel=1e-9)
    got_r, got_b = _layer1(result)
    assert got_r == pytest.approx(want_r, rel=1e-9)
    assert got_b == pytest.approx(want_b, rel=1e-9)
    assert result["breakdown"]["layer2"] == 0
    assert result["breakdown"]["failing"] == []
    assert {"schedule_version", "score_formula"} <= result["provenance"].keys()


def test_hand_computed_numeric_anchor() -> None:
    # slack_night=10 -> Φ(2); slack_no_earth=10 -> Φ(10)≈1; n=10, both hour counts 10 -> x=1.
    series = {
        "longest_night_h": 40,
        "longest_no_earth_h": 10,
        "any_both": True,
        "hours_sun_above_threshold": 10,
        "hours_earth_above_threshold": 10,
        "sun_fraction": [1.0] * 10,
    }
    needs = {"max_night_h": 50, "max_no_earth_h": 20}
    result = score(series=series, hazards={}, needs=needs)
    r = phi(2.0) * phi(10.0)
    b = (0.1 * 0.2 + 0.1 * 0.5 + 1.0 + 1.0) / 2.2
    want = r * (1.0 + BETA * b)
    assert result["score"] == pytest.approx(want, rel=1e-9)
    assert result["score"] == pytest.approx(0.97725 * (1.0 + BETA * 0.94091), abs=1e-4)


def test_missing_hours_counts_treated_as_zero() -> None:
    series = {"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True}
    needs = {"max_night_h": 50, "max_no_earth_h": 20}
    result = score(series=series, hazards={}, needs=needs)
    want, want_r, want_b = expected_score(series, needs, n=1)
    assert result["feasible"] is True
    assert result["score"] == pytest.approx(want, rel=1e-9)
    got_r, got_b = _layer1(result)
    assert got_r == pytest.approx(want_r, rel=1e-9)
    assert got_b == pytest.approx(want_b, rel=1e-9)


def test_hours_scalars_raise_bonus_monotonically() -> None:
    base = {"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True, "sun_fraction": [0.0] * 100}
    needs = {"max_night_h": 50, "max_no_earth_h": 20}
    low = score(
        series={**base, "hours_sun_above_threshold": 0, "hours_earth_above_threshold": 0},
        hazards={},
        needs=needs,
    )
    high = score(
        series={**base, "hours_sun_above_threshold": 100, "hours_earth_above_threshold": 100},
        hazards={},
        needs=needs,
    )
    assert high["score"] > low["score"]
    assert _layer1(high)[1] > _layer1(low)[1]
    assert _layer1(high)[0] == pytest.approx(_layer1(low)[0])


def test_uplift_never_exceeds_cap_fraction_of_R() -> None:
    series = {
        "longest_night_h": 0,
        "longest_no_earth_h": 0,
        "any_both": True,
        "hours_sun_above_threshold": 50,
        "hours_earth_above_threshold": 50,
        "sun_fraction": [1.0] * 50,
    }
    needs = {"max_night_h": 50, "max_no_earth_h": 20}
    result = score(series=series, hazards={}, needs=needs)
    want, want_r, want_b = expected_score(series, needs)
    assert result["score"] == pytest.approx(want, rel=1e-9)
    r, b = _layer1(result)
    assert b == pytest.approx(want_b)
    assert result["score"] <= r * (1.0 + MAX_UPLIFT) + 1e-12


def test_uplift_ratio_stays_within_cap_band() -> None:
    # With β=0.25 and B<=1 the raw uplift is at most 25%, so the 40% cap is a disaster rail:
    # score/R must always sit in [1, 1.40].
    series = {
        "longest_night_h": 10,
        "longest_no_earth_h": 5,
        "any_both": True,
        "hours_sun_above_threshold": 30,
        "hours_earth_above_threshold": 30,
        "sun_fraction": [1.0] * 30,
    }
    needs = {"max_night_h": 50, "max_no_earth_h": 20}
    result = score(series=series, hazards={}, needs=needs)
    want, want_r, _ = expected_score(series, needs)
    assert result["score"] == pytest.approx(want, rel=1e-9)
    r, _ = _layer1(result)
    assert r > 0
    assert 1.0 <= result["score"] / r <= 1.0 + MAX_UPLIFT + 1e-12


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
    assert result["score"] == 0
    assert "dust" in result["breakdown"]["failing"]


# --- NEW `lit` layer-0 gate (D-7520) -------------------------------------------------


def test_lit_gate_fails_when_longest_lit_below_minimum() -> None:
    result = score(
        series={
            "longest_night_h": 10,
            "longest_no_earth_h": 5,
            "longest_lit_h": 7,
            "any_both": True,
        },
        hazards={},
        needs={"max_night_h": 50, "max_no_earth_h": 20, "min_continuous_lit_h": 8},
    )
    assert result["feasible"] is False
    assert result["score"] == 0
    assert "lit" in result["breakdown"]["failing"]


def test_lit_gate_boundary_equal_passes_with_slack_zero() -> None:
    series = {
        "longest_night_h": 10,
        "longest_no_earth_h": 5,
        "longest_lit_h": 8,
        "any_both": True,
        "hours_sun_above_threshold": 20,
        "hours_earth_above_threshold": 10,
        "sun_fraction": [0.0] * 40,
    }
    needs = {"max_night_h": 50, "max_no_earth_h": 20, "min_continuous_lit_h": 8}
    result = score(series=series, hazards={}, needs=needs)
    assert result["feasible"] is True
    assert "lit" not in result["breakdown"]["failing"]
    want, want_r, want_b = expected_score(series, needs)
    assert result["score"] == pytest.approx(want, rel=1e-9)
    got_r, got_b = _layer1(result)
    assert got_r == pytest.approx(want_r, rel=1e-9)  # includes Φ(0)=0.5 lit factor
    assert got_b == pytest.approx(want_b, rel=1e-9)


def test_lit_term_enters_R_and_B_when_min_positive() -> None:
    series = {
        "longest_night_h": 10,
        "longest_no_earth_h": 5,
        "longest_lit_h": 20,
        "any_both": True,
        "hours_sun_above_threshold": 40,
        "hours_earth_above_threshold": 40,
        "sun_fraction": [1.0] * 80,
    }
    needs = {"max_night_h": 50, "max_no_earth_h": 20, "min_continuous_lit_h": 10}
    result = score(series=series, hazards={}, needs=needs)
    want, want_r, want_b = expected_score(series, needs)
    # lit slack=10 -> Φ(2); B interval term slack_lit/min = 1.0
    assert want_r == pytest.approx(phi(40 / 5) * phi(15 / 1) * phi(2.0), rel=1e-9)
    assert result["score"] == pytest.approx(want, rel=1e-9)
    got_r, got_b = _layer1(result)
    assert got_r == pytest.approx(want_r, rel=1e-9)
    assert got_b == pytest.approx(want_b, rel=1e-9)


def test_default_min_lit_zero_has_no_lit_gate_or_term() -> None:
    series = {
        "longest_night_h": 10,
        "longest_no_earth_h": 5,
        "longest_lit_h": 0,
        "any_both": True,
        "hours_sun_above_threshold": 0,
        "hours_earth_above_threshold": 0,
        "sun_fraction": [0.0] * 24,
    }
    needs = {"max_night_h": 50, "max_no_earth_h": 20}
    result = score(series=series, hazards={}, needs=needs)
    assert result["feasible"] is True
    want, want_r, _ = expected_score(series, needs)
    assert _layer1(result)[0] == pytest.approx(want_r, rel=1e-9)
    assert result["score"] == pytest.approx(want, rel=1e-9)


def test_lit_gate_combines_with_other_failing_tags() -> None:
    result = score(
        series={"longest_night_h": 60, "longest_no_earth_h": 5, "longest_lit_h": 1, "any_both": True},
        hazards={},
        needs={"max_night_h": 50, "max_no_earth_h": 20, "min_continuous_lit_h": 8},
    )
    assert result["feasible"] is False
    assert {"night", "lit"} <= set(result["breakdown"]["failing"])


# --- provenance ---------------------------------------------------------------------


def test_provenance_cites_new_formula_sigmas_and_decisions() -> None:
    result = score(
        series={
            "longest_night_h": 10,
            "longest_no_earth_h": 5,
            "longest_lit_h": 20,
            "any_both": True,
            "hours_sun_above_threshold": 1,
            "hours_earth_above_threshold": 1,
            "sun_fraction": [1.0] * 2,
        },
        hazards={},
        needs={"max_night_h": 50, "max_no_earth_h": 20, "min_continuous_lit_h": 10},
    )
    prov = result["provenance"]
    assert isinstance(prov["score_formula"], str) and prov["score_formula"]
    assert prov["score_formula"] != OLD_FORMULA
    text = str(prov).lower()
    for ref in ("d-7520", "d-7af3", "d-6ce5"):
        assert ref in text
    assert "sigma" in text


# --- companion_score on infeasible (D-5577) -----------------------------------------
# Display score stays 0 when layer 0 fails; companion_score = R x bonus with the same
# Φ/σ/β/cap as the feasible path, computed even with negative slacks.

NEEDS_BASE = {"max_night_h": 50, "max_no_earth_h": 20, "require_both": False}


def test_infeasible_night_has_zero_score_and_companion_from_negative_slack() -> None:
    series = {
        "longest_night_h": 52,  # slack -2 -> Φ(-0.4)
        "longest_no_earth_h": 10,
        "any_both": True,
        "hours_sun_above_threshold": 10,
        "hours_earth_above_threshold": 5,
        "sun_fraction": [0.0] * 20,
    }
    result = score(series=series, hazards={}, needs=NEEDS_BASE)
    want, want_r, _ = expected_score(series, NEEDS_BASE)
    assert want_r == pytest.approx(phi(-0.4) * phi(10.0), rel=1e-9)
    assert result["feasible"] is False
    assert result["score"] == 0
    assert "night" in result["breakdown"]["failing"]
    assert result["companion_score"] == pytest.approx(want, rel=1e-9)
    assert result["companion_score"] > 0


def test_feasible_companion_score_equals_display_score() -> None:
    series = {"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True}
    result = score(series=series, hazards={}, needs=NEEDS_BASE)
    assert result["feasible"] is True
    assert result["companion_score"] == pytest.approx(result["score"], rel=1e-12)


def test_companion_ranks_less_bad_infeasible_higher() -> None:
    mild = score({"longest_night_h": 52, "longest_no_earth_h": 10, "any_both": True}, {}, NEEDS_BASE)
    bad = score({"longest_night_h": 70, "longest_no_earth_h": 10, "any_both": True}, {}, NEEDS_BASE)
    assert mild["score"] == bad["score"] == 0
    assert mild["companion_score"] > bad["companion_score"] > 0


def test_companion_with_multiple_failures_matches_formula_including_lit() -> None:
    series = {
        "longest_night_h": 55,
        "longest_no_earth_h": 22,
        "longest_lit_h": 6,
        "any_both": True,
        "hours_sun_above_threshold": 8,
        "hours_earth_above_threshold": 4,
        "sun_fraction": [0.0] * 30,
    }
    needs = {**NEEDS_BASE, "min_continuous_lit_h": 8}
    result = score(series=series, hazards={}, needs=needs)
    want, _, _ = expected_score(series, needs)
    assert {"night", "no_earth", "lit"} <= set(result["breakdown"]["failing"])
    assert result["score"] == 0
    assert result["companion_score"] == pytest.approx(want, rel=1e-9)


def test_surface_fail_keeps_companion_from_slacks() -> None:
    series = {"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True}
    result = score(
        series=series,
        hazards={"aggregate": {"temperature_k": 400.0, "soil_resistance": 1e6}},
        needs={**NEEDS_BASE, "max_temperature_k": 350.0},
    )
    want, _, _ = expected_score(series, NEEDS_BASE, n=1)
    assert result["feasible"] is False and result["score"] == 0
    assert result["companion_score"] == pytest.approx(want, rel=1e-9)


def test_companion_uplift_stays_within_cap() -> None:
    series = {
        "longest_night_h": 51,
        "longest_no_earth_h": 20,
        "any_both": True,
        "hours_sun_above_threshold": 50,
        "hours_earth_above_threshold": 50,
        "sun_fraction": [1.0] * 50,
    }
    result = score(series=series, hazards={}, needs=NEEDS_BASE)
    want, want_r, _ = expected_score(series, NEEDS_BASE)
    assert want_r > 0
    assert want <= want_r * (1.0 + MAX_UPLIFT) + 1e-12
    assert result["companion_score"] == pytest.approx(want, rel=1e-9)


def test_hazard_gap_star_set_for_missing_temperature_or_dust_only() -> None:
    # per D-f57e: star only when a temperature/dust requirement has no hazard value.
    series = {"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True}
    temp_gap = score(series, {}, {**NEEDS_BASE, "max_temperature_k": 350.0})
    dust_gap = score(series, {}, {**NEEDS_BASE, "min_soil_resistance": 500.0})
    no_gap = score(
        series,
        {"aggregate": {"temperature_k": 250.0, "soil_resistance": 1e6}},
        {**NEEDS_BASE, "max_temperature_k": 350.0, "min_soil_resistance": 500.0},
    )
    plain = score(series, {}, NEEDS_BASE)
    assert temp_gap["hazard_gap_star"] is True
    assert dust_gap["hazard_gap_star"] is True
    assert not no_gap.get("hazard_gap_star")
    assert not plain.get("hazard_gap_star")


def test_surface_temperature_below_planner_minimum_is_infeasible() -> None:
    """D-20261117-pj-0c5e: the coldest hour of the window is checked against the minimum."""
    result = score(
        series={"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True},
        hazards={"aggregate": {"temperature_k": 300.0, "temperature_min_k": 90.0, "soil_resistance": 1e6}},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "min_temperature_k": 120.0,
            "require_both": False,
        },
    )

    assert result["feasible"] is False
    assert "temperature_min" in result["breakdown"]["failing"]


def test_surface_temperature_inside_both_limits_stays_feasible() -> None:
    result = score(
        series={"longest_night_h": 40, "longest_no_earth_h": 10, "any_both": True},
        hazards={"aggregate": {"temperature_k": 300.0, "temperature_min_k": 150.0, "soil_resistance": 1e6}},
        needs={
            "max_night_h": 50,
            "max_no_earth_h": 20,
            "max_temperature_k": 320.0,
            "min_temperature_k": 120.0,
            "require_both": False,
        },
    )

    assert result["feasible"] is True


def test_min_total_lit_h_layer0_and_layer1() -> None:
    from lunar_eval.score import score

    series = {
        "sun_fraction": [1.0] * 10 + [0.0] * 14, "earth_fraction": [1.0] * 24, "step_min": 60,
        "longest_night_h": 4, "longest_no_earth_h": 0, "longest_lit_h": 6,
        "hours_sun_above_threshold": 10, "hours_earth_above_threshold": 24,
    }
    base = {"max_night_h": 12, "max_no_earth_h": 10}
    assert score(series, {}, base)["feasible"] is True
    off = score(series, {}, {**base, "min_total_lit_h": 0})
    assert off["score"] == score(series, {}, base)["score"]  # 0 = no requirement, no term
    fail = score(series, {}, {**base, "min_total_lit_h": 12})
    assert fail["feasible"] is False and "lit_total" in fail["breakdown"]["failing"]
    near = score(series, {}, {**base, "min_total_lit_h": 9})
    far = score(series, {}, {**base, "min_total_lit_h": 2})
    assert near["feasible"] and far["feasible"] and far["score"] > near["score"]


def _hz(temp, sigma, res=1.0):
    return {"temperature_k": temp, "temperature_min_k": temp, "temperature_sigma_k": sigma, "soil_resistance": res}


def test_hazard_margins_enter_layer1_risk() -> None:
    from lunar_eval.score import score

    series = {
        "sun_fraction": [1.0] * 24, "earth_fraction": [1.0] * 24, "step_min": 60,
        "longest_night_h": 0, "longest_no_earth_h": 0, "longest_lit_h": 24,
        "hours_sun_above_threshold": 24, "hours_earth_above_threshold": 24,
    }
    needs = {"max_night_h": 12, "max_no_earth_h": 12, "max_temperature_k": 320.0}
    far = score(series, _hz(250.0, 5.0), needs)
    close = score(series, _hz(318.0, 5.0), needs)
    assert far["feasible"] and close["feasible"]  # both under the limit: layer 0 unchanged
    assert far["score"] > close["score"]  # but the margin now counts
    assert far["provenance"]["hazard_margins"]["temperature"]["sigma_k"] == 5.0
    over = score(series, _hz(330.0, 5.0), needs)
    assert over["feasible"] is False and over["score"] == 0


def test_hazard_margin_without_sigma_stays_layer0_only() -> None:
    from lunar_eval.score import score

    series = {
        "sun_fraction": [1.0] * 24, "earth_fraction": [1.0] * 24, "step_min": 60,
        "longest_night_h": 0, "longest_no_earth_h": 0, "longest_lit_h": 24,
        "hours_sun_above_threshold": 24, "hours_earth_above_threshold": 24,
    }
    needs = {"max_night_h": 12, "max_no_earth_h": 12, "max_temperature_k": 320.0}
    a = score(series, _hz(250.0, None), needs)
    b = score(series, _hz(318.0, None), needs)
    assert a["score"] == b["score"]
    assert a["provenance"]["hazard_margins"]["temperature"] == "no_spread_layer0_only"


def test_dust_margin_is_relative_and_only_with_a_positive_limit() -> None:
    from lunar_eval.score import score

    series = {
        "sun_fraction": [1.0] * 24, "earth_fraction": [1.0] * 24, "step_min": 60,
        "longest_night_h": 0, "longest_no_earth_h": 0, "longest_lit_h": 24,
        "hours_sun_above_threshold": 24, "hours_earth_above_threshold": 24,
    }
    base = {"max_night_h": 12, "max_no_earth_h": 12}
    no_limit = score(series, _hz(250.0, 5.0, res=0.85), {**base, "min_soil_resistance": 0.0})
    assert "dust" not in no_limit["provenance"]["hazard_margins"]
    tight = score(series, _hz(250.0, 5.0, res=0.85), {**base, "min_soil_resistance": 0.80})
    ample = score(series, _hz(250.0, 5.0, res=0.85), {**base, "min_soil_resistance": 0.10})
    assert tight["feasible"] and ample["feasible"] and ample["score"] > tight["score"]
