"""Needs-adapted score (P4). # per D-20261114-pj-de42 D-20261114-pj-9e53"""

from __future__ import annotations

FORMULA = "two_layer_zero_then_assurance_then_weights"


def score(series: dict, hazards: dict, needs: dict) -> dict:
    # ponytail: layer2 hazards ignored until P13; layer1 = min normalized slack in hours
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
    provenance = {"score_formula": FORMULA, "schedule_version": series.get("schedule_version", "n/a")}
    if failing:
        return {"score": 0, "feasible": False, "breakdown": {"failing": failing}, "provenance": provenance}
    slacks = [max_night - night, max_no_earth - no_earth]
    thresholds = [max(max_night, 1), max(max_no_earth, 1)]
    layer1 = min(s / t for s, t in zip(slacks, thresholds, strict=True))
    return {
        "score": float(layer1),
        "feasible": True,
        "breakdown": {"layer1": layer1, "layer2": 0.0, "failing": []},
        "provenance": provenance,
    }
