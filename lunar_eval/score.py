"""Needs-adapted score (P4). # D-7520 D-6ce5 D-7af3 D-9e53 D-5cfa"""

from __future__ import annotations

import math

FORMULA = "product_phi_slack_bonus_capped"

_SIGMA_NIGHT = 5.0
_SIGMA_LIT = 5.0
_SIGMA_NO_EARTH = 1.0
_BETA = 0.15
_MAX_UPLIFT = 0.30


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _clip01(x: float) -> float:
    return min(1.0, max(0.0, x))


def _surface_layer0(hazards: dict, needs: dict) -> list[str]:
    failing: list[str] = []
    max_temp = needs.get("max_temperature_k")
    min_res = needs.get("min_soil_resistance")
    temp_k = hazards.get("temperature_k")
    res = hazards.get("soil_resistance")
    if max_temp is not None and temp_k is not None and temp_k > float(max_temp):
        failing.append("temperature")
    if min_res is not None and res is not None and res < float(min_res):
        failing.append("dust")
    return failing


def score(series: dict, hazards: dict, needs: dict) -> dict:
    night = int(series["longest_night_h"])
    no_earth = int(series["longest_no_earth_h"])
    max_night = int(needs["max_night_h"])
    max_no_earth = int(needs["max_no_earth_h"])
    min_lit = int(needs.get("min_continuous_lit_h", 0))
    longest_lit = int(series.get("longest_lit_h", 0))
    require_both = bool(needs.get("require_both", False))
    failing: list[str] = []
    if night > max_night:
        failing.append("night")
    if no_earth > max_no_earth:
        failing.append("no_earth")
    if require_both and not series.get("any_both", False):
        failing.append("both")
    if min_lit > 0 and longest_lit < min_lit:
        failing.append("lit")
    hz = hazards.get("aggregate", hazards) if hazards else {}
    failing.extend(_surface_layer0(hz, needs))
    provenance = {
        "score_formula": FORMULA,
        "schedule_version": series.get("schedule_version", "n/a"),
        "decisions": ["D-7520", "D-6ce5", "D-7af3", "D-9e53", "D-5cfa"],
        "sigmas_h": {
            "night": _SIGMA_NIGHT,
            "lit": _SIGMA_LIT,
            "no_earth": _SIGMA_NO_EARTH,
        },
    }
    if failing:
        return {"score": 0, "feasible": False, "breakdown": {"failing": failing}, "provenance": provenance}

    slack_night = max_night - night
    slack_no_earth = max_no_earth - no_earth
    ps = [_phi(slack_night / _SIGMA_NIGHT), _phi(slack_no_earth / _SIGMA_NO_EARTH)]
    terms: list[tuple[float, float]] = [
        (0.1, _clip01(slack_night / max(max_night, 1))),
        (0.1, _clip01(slack_no_earth / max(max_no_earth, 1))),
    ]
    if min_lit > 0:
        slack_lit = longest_lit - min_lit
        ps.append(_phi(slack_lit / _SIGMA_LIT))
        terms.append((0.1, _clip01(slack_lit / max(min_lit, 1))))

    if "sun_fraction" in series:
        n_div = max(len(series["sun_fraction"]), 1)
    else:
        n_div = 1
    hours_sun = int(series.get("hours_sun_above_threshold", 0))
    hours_earth = int(series.get("hours_earth_above_threshold", 0))
    terms.append((1.0, _clip01(hours_sun / n_div)))
    terms.append((1.0, _clip01(hours_earth / n_div)))

    r = math.prod(ps)
    wsum = sum(w for w, _ in terms)
    b = _clip01(sum(w * x for w, x in terms) / wsum) if wsum > 0 else 0.0
    raw = r * (1.0 + _BETA * b)
    if r > 0 and (raw - r) / r > _MAX_UPLIFT:
        final = r * (1.0 + _MAX_UPLIFT)
    else:
        final = raw
    layer2 = 0.0
    return {
        "score": float(final),
        "feasible": True,
        "breakdown": {
            "layer1_R": r,
            "layer1_B": b,
            "layer1": final,
            "layer2": layer2,
            "failing": [],
        },
        "provenance": provenance,
    }