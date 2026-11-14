"""Needs-adapted score (P4). # per D-20261114-pj-de42 D-20261114-pj-9e53 D-5cfa"""

from __future__ import annotations

FORMULA = "two_layer_zero_then_assurance_then_weights"


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
    require_both = bool(needs.get("require_both", False))
    failing: list[str] = []
    if night > max_night:
        failing.append("night")
    if no_earth > max_no_earth:
        failing.append("no_earth")
    if require_both and not series.get("any_both", False):
        failing.append("both")
    hz = hazards.get("aggregate", hazards) if hazards else {}
    failing.extend(_surface_layer0(hz, needs))
    provenance = {"score_formula": FORMULA, "schedule_version": series.get("schedule_version", "n/a")}
    if failing:
        return {"score": 0, "feasible": False, "breakdown": {"failing": failing}, "provenance": provenance}
    slacks = [max_night - night, max_no_earth - no_earth]
    thresholds = [max(max_night, 1), max(max_no_earth, 1)]
    layer1 = min(s / t for s, t in zip(slacks, thresholds, strict=True))
    layer2 = 0.0  # ponytail: layer-2 hazard weights deferred (D-de42)
    return {
        "score": float(layer1),
        "feasible": True,
        "breakdown": {"layer1": layer1, "layer2": layer2, "failing": []},
        "provenance": provenance,
    }