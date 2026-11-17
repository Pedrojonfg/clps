"""Needs-adapted score (P4). # D-7520 D-6ce5 D-48ee D-7af3 D-9e53 D-5cfa D-5577 D-f57e"""

from __future__ import annotations

import math

FORMULA = "product_phi_slack_bonus_capped"

_SIGMA_NIGHT = 5.0  # per D-7520
_SIGMA_LIT = 5.0  # per D-7520
_SIGMA_NO_EARTH = 1.0  # per D-7520
_BETA = 0.25  # per D-20261115-pj-48ee
_MAX_UPLIFT = 0.40  # per D-20261115-pj-48ee
_SIGMA_TOTAL_LIT = 5.0  # per D-20261117-pj-7b2d (provisional, same as the continuous-lit sigma)


def _energy_mode(series: dict) -> bool:
    """Energy mode: the series carries the lowest state of charge (D-20261117-pj-7b2d)."""
    return series.get("soc_min") is not None


def _reserve(needs: dict) -> float:
    from lunar_eval.energy import RESERVE_DEFAULT

    r = needs.get("energy_reserve_frac")
    return RESERVE_DEFAULT if r is None else float(r)


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _clip01(x: float) -> float:
    return min(1.0, max(0.0, x))


def _hazard_field(hazards: dict, key: str):
    if not hazards:
        return None
    if hazards.get(key) is not None:
        return hazards[key]
    agg = hazards.get("aggregate") or {}
    return agg.get(key)


def _hazard_gap_star(hazards: dict, needs: dict) -> bool:
    # per D-f57e: star only when requirement set but hazard value absent (temperature/dust).
    if needs.get("max_temperature_k") is not None and _hazard_field(hazards, "temperature_k") is None:
        return True
    if needs.get("min_soil_resistance") is not None and _hazard_field(hazards, "soil_resistance") is None:
        return True
    return False


def _surface_layer0(hazards: dict, needs: dict) -> list[str]:
    failing: list[str] = []
    max_temp = needs.get("max_temperature_k")
    min_res = needs.get("min_soil_resistance")
    temp_k = _hazard_field(hazards, "temperature_k")
    res = _hazard_field(hazards, "soil_resistance")
    if max_temp is not None and temp_k is not None and temp_k > float(max_temp):
        failing.append("temperature")
    min_temp = needs.get("min_temperature_k")
    temp_min_k = _hazard_field(hazards, "temperature_min_k")
    if temp_min_k is None:
        temp_min_k = temp_k  # a single-value payload is both its own peak and its own trough
    if min_temp is not None and temp_min_k is not None and temp_min_k < float(min_temp):
        failing.append("temperature_min")
    if min_res is not None and res is not None and res < float(min_res):
        failing.append("dust")
    return failing


def _schedule_layer0(series: dict, needs: dict) -> list[str]:
    failing: list[str] = []
    no_earth = float(series["longest_no_earth_h"])
    max_no_earth = int(needs["max_no_earth_h"])
    min_lit = int(needs.get("min_continuous_lit_h", 0))
    min_total_lit = float(needs.get("min_total_lit_h", 0) or 0)
    longest_lit = float(series.get("longest_lit_h", 0))
    require_both = bool(needs.get("require_both", False))
    if _energy_mode(series):
        if float(series["soc_min"]) < _reserve(needs):
            failing.append("battery")
    elif float(series["longest_night_h"]) > int(needs["max_night_h"]):
        failing.append("night")
    if no_earth > max_no_earth:
        failing.append("no_earth")
    if require_both and not series.get("any_both", False):
        failing.append("both")
    if min_lit > 0 and longest_lit < min_lit:
        failing.append("lit")
    if min_total_lit > 0 and float(series.get("hours_sun_above_threshold", 0)) < min_total_lit:
        failing.append("lit_total")
    return failing


_SIGMA_LN_DUST = 0.6  # relative spread of the soil-resistance proxy (D-20261117-pj-e3a7, provisional)


def _hazard_margin_ps(hazards: dict, needs: dict) -> tuple[list[float], dict]:
    """Layer-1 margin terms for temperature and dust (D-20261117-pj-e3a7). Only for limits the user set;
    temperature needs a spread (none -> layer 0 only, noted in provenance)."""
    ps: list[float] = []
    used: dict = {}
    sigma_t = _hazard_field(hazards, "temperature_sigma_k")  # at the hottest hour
    sigma_t_min = _hazard_field(hazards, "temperature_min_sigma_k")  # at the coldest hour
    if sigma_t_min is None:
        sigma_t_min = sigma_t
    temp_k = _hazard_field(hazards, "temperature_k")
    temp_min = _hazard_field(hazards, "temperature_min_k")
    if temp_min is None:
        temp_min = temp_k
    max_t, min_t = needs.get("max_temperature_k"), needs.get("min_temperature_k")
    if (max_t is not None or min_t is not None) and temp_k is not None:
        if sigma_t is None or float(sigma_t) <= 0:
            used["temperature"] = "no_spread_layer0_only"
        else:
            used["temperature"] = {"sigma_k": float(sigma_t), "source": "pcp_spatial_spread_v1"}
            if max_t is not None:
                ps.append(_phi((float(max_t) - float(temp_k)) / float(sigma_t)))
            if min_t is not None and temp_min is not None and float(sigma_t_min) > 0:
                ps.append(_phi((float(temp_min) - float(min_t)) / float(sigma_t_min)))
    min_res = needs.get("min_soil_resistance")
    res = _hazard_field(hazards, "soil_resistance")
    if min_res is not None and float(min_res) > 0 and res is not None and float(res) > 0:
        used["dust"] = {"sigma_ln": _SIGMA_LN_DUST, "source": "metzger_2024_input_ranges_provisional"}
        ps.append(_phi(math.log(float(res) / float(min_res)) / _SIGMA_LN_DUST))
    return ps, used


def _layer1_score(series: dict, needs: dict, hazards: dict | None = None) -> tuple[float, float, float]:
    """R, B, capped R*(1+βB) — computed even when layer-0 slacks are negative. # D-5577"""
    max_no_earth = int(needs["max_no_earth_h"])
    min_lit = int(needs.get("min_continuous_lit_h", 0))
    min_total_lit = float(needs.get("min_total_lit_h", 0) or 0)
    no_earth = float(series["longest_no_earth_h"])
    longest_lit = float(series.get("longest_lit_h", 0))
    slack_no_earth = max_no_earth - no_earth

    if _energy_mode(series):
        # Battery margin replaces the night term in R; surplus battery is not credited in B (D-7b2d).
        slack_soc = float(series["soc_min"]) - _reserve(needs)
        from lunar_eval.energy import SIGMA_SOC_DEFAULT

        ps = [_phi(slack_soc / SIGMA_SOC_DEFAULT), _phi(slack_no_earth / _SIGMA_NO_EARTH)]
        terms: list[tuple[float, float]] = [(0.1, _clip01(slack_no_earth / max(max_no_earth, 1)))]
    else:
        max_night = int(needs["max_night_h"])
        slack_night = max_night - float(series["longest_night_h"])
        ps = [_phi(slack_night / _SIGMA_NIGHT), _phi(slack_no_earth / _SIGMA_NO_EARTH)]
        terms = [
            (0.1, _clip01(slack_night / max(max_night, 1))),
            (0.1, _clip01(slack_no_earth / max(max_no_earth, 1))),
        ]
    if min_lit > 0:
        slack_lit = longest_lit - min_lit
        ps.append(_phi(slack_lit / _SIGMA_LIT))
        terms.append((0.1, _clip01(slack_lit / max(min_lit, 1))))
    if min_total_lit > 0:
        slack_total = float(series.get("hours_sun_above_threshold", 0)) - min_total_lit
        ps.append(_phi(slack_total / _SIGMA_TOTAL_LIT))
        terms.append((0.1, _clip01(slack_total / max(min_total_lit, 1))))

    hz_ps, _ = _hazard_margin_ps(hazards or {}, needs)
    ps.extend(hz_ps)

    if "sun_fraction" in series:
        n_div = max(len(series["sun_fraction"]) * float(series.get("step_min", 60)) / 60.0, 1.0)
    else:
        n_div = 1.0
    hours_sun = float(series.get("hours_sun_above_threshold", 0))
    hours_earth = float(series.get("hours_earth_above_threshold", 0))
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
    return r, b, float(final)


def score(series: dict, hazards: dict, needs: dict) -> dict:
    failing = _schedule_layer0(series, needs)
    failing.extend(_surface_layer0(hazards, needs))
    r, b, companion = _layer1_score(series, needs, hazards)
    _, hazard_margins = _hazard_margin_ps(hazards or {}, needs)
    gap_star = _hazard_gap_star(hazards, needs)

    provenance = {
        "score_formula": FORMULA,
        "schedule_version": series.get("schedule_version", "n/a"),
        "decisions": ["D-7520", "D-6ce5", "D-48ee", "D-7af3", "D-9e53", "D-5cfa", "D-5577", "D-f57e"],
        "hazard_margins": hazard_margins,
        "sigmas_h": {
            "night": _SIGMA_NIGHT,
            "lit": _SIGMA_LIT,
            "no_earth": _SIGMA_NO_EARTH,
        },
    }

    base: dict = {
        "companion_score": companion,
        "provenance": provenance,
    }
    if gap_star:
        base["hazard_gap_star"] = True

    if failing:
        return {
            **base,
            "score": 0,
            "feasible": False,
            "breakdown": {"failing": failing, "layer1_R": r, "layer1_B": b},
        }

    layer2 = 0.0
    return {
        **base,
        "score": companion,
        "feasible": True,
        "breakdown": {
            "layer1_R": r,
            "layer1_B": b,
            "layer1": companion,
            "layer2": layer2,
            "failing": [],
        },
    }