"""S9 region score map: colour scale, infeasible markers, induction, payload.

per D-20261115-pj-85bf, D-20261115-pj-8acb, D-20261115-pj-7227, D-20261115-pj-48ee.
"""

from __future__ import annotations

import math
from typing import Any

from lunar_eval.horizon import polar_stereo_xy
from lunar_eval.horizon.mask import R_M

SCORE_CEILING = 1.4  # per D-7227 D-48ee (1.0 * (1 + 0.40))
INDUCED_OPACITY = 0.45  # per D-85bf
EVALUATED_OPACITY = 1.0
INDUCE_RADIUS_KM = 1.0  # one cap cell step; per D-85bf

_YELLOW_ANCHOR = 0.7  # per D-7227 yellow at mid
_BEST_TOL_DEG = 1.0e-4
_INDUCED_MIN_SEP_KM = 0.1


def feasible_score_to_rgb(score: float) -> tuple[int, int, int]:
    """Absolute continuous RYG; clamp below 0 and above ceiling. per D-7227."""
    s = max(0.0, min(float(score), SCORE_CEILING))
    if s <= _YELLOW_ANCHOR:
        u = s / _YELLOW_ANCHOR if _YELLOW_ANCHOR else 0.0
        r, g, b = 255, int(round(255.0 * u)), 0
    else:
        span = SCORE_CEILING - _YELLOW_ANCHOR
        u = (s - _YELLOW_ANCHOR) / span if span else 1.0
        r, g, b = int(round(255.0 * (1.0 - u))), 255, 0
    return (
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


def sample_rgba(
    score: float,
    feasible: bool,
    *,
    induced: bool = False,
    companion_score: float | None = None,
    infeasible_companions: list[float] | None = None,
) -> tuple[int, int, int, float]:
    """RGBA for one map sample. per D-8acb / D-85bf."""
    opacity = INDUCED_OPACITY if induced else EVALUATED_OPACITY
    if not feasible:
        return 0, 0, 0, opacity
    r, g, b = feasible_score_to_rgb(score)
    return r, g, b, opacity


def infeasible_marker_t(companion_score: float, infeasible_companions: list[float]) -> float:
    """Relative dot position among infeasibles in this query only. per D-8acb."""
    if len(infeasible_companions) <= 1:
        return 0.5
    lo = min(infeasible_companions)
    hi = max(infeasible_companions)
    if hi <= lo:
        return 0.5
    return (float(companion_score) - lo) / (hi - lo)


def _polar_stereo_xy_to_latlon(x_m: float, y_m: float, radius_m: float = R_M) -> tuple[float, float]:
    """Inverse of south-polar stereographic matching mask.polar_stereo_xy."""
    rho = math.hypot(x_m, y_m)
    if rho < 1.0e-12:
        return -90.0, 0.0
    k = 2.0 * math.atan(rho / (2.0 * radius_m))
    lat_deg = math.degrees(k) - 90.0
    lon_deg = math.degrees(math.atan2(x_m, y_m)) % 360.0
    return lat_deg, lon_deg


def _stereo_km(row: dict[str, Any]) -> tuple[float, float]:
    x, y = polar_stereo_xy(row["lat_deg"], row["lon_deg"])
    return x / 1000.0, y / 1000.0


def _dist_km_stereo(a: dict[str, Any], b_lat: float, b_lon: float) -> float:
    ax, ay = _stereo_km(a)
    bx, by = polar_stereo_xy(b_lat, b_lon)
    bx, by = bx / 1000.0, by / 1000.0
    return math.hypot(ax - bx, ay - by)


def induce_neighbours(evaluated: list[dict[str, Any]], *, radius_km: float = INDUCE_RADIUS_KM) -> list[dict[str, Any]]:
    """Four cardinal neighbours in polar stereo km; partial-search fill. per D-85bf."""
    if not evaluated:
        return []

    radius_m = radius_km * 1000.0
    min_sep_m = _INDUCED_MIN_SEP_KM * 1000.0
    offsets = ((radius_m, 0.0), (-radius_m, 0.0), (0.0, radius_m), (0.0, -radius_m))

    out_eval: list[dict[str, Any]] = []
    eval_xy_m: list[tuple[float, float]] = []
    for row in evaluated:
        tagged = dict(row)
        tagged["induced"] = False
        out_eval.append(tagged)
        x, y = polar_stereo_xy(tagged["lat_deg"], tagged["lon_deg"])
        eval_xy_m.append((x, y))

    induced: list[dict[str, Any]] = []
    induced_xy_m: list[tuple[float, float]] = []

    for ev_row, (x0, y0) in zip(out_eval, eval_xy_m, strict=True):
        for dx, dy in offsets:
            xn, yn = x0 + dx, y0 + dy
            if any(math.hypot(xn - xe, yn - ye) < min_sep_m for xe, ye in eval_xy_m):
                continue
            if any(math.hypot(xn - xi, yn - yi) < min_sep_m for xi, yi in induced_xy_m):
                continue
            lat_deg, lon_deg = _polar_stereo_xy_to_latlon(xn, yn)
            parent = min(
                out_eval,
                key=lambda r: _dist_km_stereo(r, lat_deg, lon_deg),
            )
            new_row = dict(parent)
            new_row["lat_deg"] = lat_deg
            new_row["lon_deg"] = lon_deg
            new_row["induced"] = True
            induced.append(new_row)
            induced_xy_m.append((xn, yn))

    return out_eval + induced


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_key: dict[tuple[float, float], dict[str, Any]] = {}
    for row in rows:
        key = (row["lat_deg"], row["lon_deg"])
        if key not in best_by_key:
            best_by_key[key] = row
            continue
        cur = best_by_key[key]
        if _row_preferred(row, cur):
            best_by_key[key] = row
    return list(best_by_key.values())


def _row_preferred(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True if a should win over b at the same lat/lon."""
    if bool(a.get("feasible")) != bool(b.get("feasible")):
        return bool(a.get("feasible"))
    ac = float(a.get("companion_score", a.get("score", 0.0)))
    bc = float(b.get("companion_score", b.get("score", 0.0)))
    if ac != bc:
        return ac > bc
    return float(a.get("score", 0.0)) > float(b.get("score", 0.0))


def _is_best_match(sample: dict[str, Any], best: dict[str, Any] | None) -> bool:
    if best is None or sample.get("induced"):
        return False
    return (
        abs(sample["lat_deg"] - best["lat_deg"]) < _BEST_TOL_DEG
        and abs(sample["lon_deg"] - best["lon_deg"]) < _BEST_TOL_DEG
    )


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if "companion_score" not in out:
        out["companion_score"] = out.get("score", 0.0)
    out.setdefault("feasible", True)
    out.setdefault("score", float(out.get("companion_score", 0.0)))
    return out


def build_region_map(
    rows: list[dict[str, Any]],
    *,
    search_partial: bool,
    best: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build JSON payload for S9 region map."""
    normalized = [_normalize_row(r) for r in rows]
    evaluated = _dedupe_rows(normalized)

    if search_partial:
        working = induce_neighbours(evaluated)
    else:
        working = [dict(r, induced=False) for r in evaluated]

    infeas_companions = [
        float(r.get("companion_score", r.get("score", 0.0)))
        for r in working
        if not bool(r.get("feasible", True))
    ]

    samples: list[dict[str, Any]] = []
    n_induced = 0
    for row in working:
        induced = bool(row.get("induced", False))
        if induced:
            n_induced += 1
        feasible = bool(row.get("feasible", True))
        companion = float(row.get("companion_score", row["score"]))
        rgba = sample_rgba(
            float(row["score"]),
            feasible,
            induced=induced,
            companion_score=companion,
            infeasible_companions=infeas_companions,
        )
        # per D-8acb: relative badness marker among infeasibles in this query only
        marker_t = (
            None
            if feasible
            else infeasible_marker_t(companion, infeas_companions)
        )
        sample = {
            "lat_deg": row["lat_deg"],
            "lon_deg": row["lon_deg"],
            "score": row["score"],
            "feasible": feasible,
            "companion_score": companion,
            "induced": induced,
            "rgba": list(rgba),
            "is_best": _is_best_match(row, best),
            "marker_t": marker_t,
        }
        samples.append(sample)

    return {
        "samples": samples,
        "score_ceiling": SCORE_CEILING,
        "search_partial": search_partial,
        "n_evaluated": len(evaluated),
        "n_induced": n_induced,
    }