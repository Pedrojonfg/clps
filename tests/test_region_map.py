"""S9 region score map: colour scale, infeasible markers, induction, payload.

per D-20261115-pj-85bf (paint evaluated; induce only under partial search),
D-20261115-pj-8acb (infeasible black + in-query relative dots),
D-20261115-pj-7227 (absolute continuous RYG, clamp above ceiling to green),
D-20261115-pj-48ee (ceiling 1.0 * (1 + 0.40)).
D-834a (interpolate/lift) and D-4126 (3D canvas) are UI-only: no unit tests here.
"""

from __future__ import annotations

import math

import pytest

from lunar_eval.horizon import polar_stereo_xy
from lunar_eval.region_map import (
    EVALUATED_OPACITY,
    INDUCE_RADIUS_KM,
    INDUCED_OPACITY,
    SCORE_CEILING,
    build_region_map,
    feasible_score_to_rgb,
    induce_neighbours,
    infeasible_marker_t,
    sample_rgba,
)

SITE_LAT = -89.46316
SITE_LON = 222.51045


def _row(lat=SITE_LAT, lon=SITE_LON, score=0.8, feasible=True, companion=None, **extra):
    return {
        "lat_deg": lat,
        "lon_deg": lon,
        "score": score,
        "feasible": feasible,
        "companion_score": score if companion is None else companion,
        **extra,
    }


def _xy_km(row):
    x, y = polar_stereo_xy(row["lat_deg"], row["lon_deg"])
    return x / 1000.0, y / 1000.0


def _dist_km(a, b):
    ax, ay = _xy_km(a)
    bx, by = _xy_km(b)
    return math.hypot(ax - bx, ay - by)


# ---------------------------------------------------------------- constants


def test_constants():
    assert SCORE_CEILING == 1.4  # per D-7227 D-48ee (1.0 * (1 + 0.40))
    assert INDUCED_OPACITY == 0.45
    assert EVALUATED_OPACITY == 1.0
    assert INDUCE_RADIUS_KM == 1.0  # one cap cell step
    assert INDUCED_OPACITY < EVALUATED_OPACITY  # per D-85bf higher transparency


# ------------------------------------------------- feasible_score_to_rgb


def test_rgb_returns_int_triplet_in_range():
    for s in (0.0, 0.3, 0.7, 1.1, 1.4):
        rgb = feasible_score_to_rgb(s)
        assert isinstance(rgb, tuple) and len(rgb) == 3
        assert all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)


def test_rgb_red_at_zero():
    r, g, b = feasible_score_to_rgb(0.0)  # per D-7227 red near 0
    assert r > 200 and g < 80 and b < 80


def test_rgb_yellow_at_mid():
    r, g, b = feasible_score_to_rgb(0.7)  # per D-7227 yellow at mid (0.7)
    assert r > 200 and g > 200 and b < 80


def test_rgb_green_at_ceiling():
    r, g, b = feasible_score_to_rgb(SCORE_CEILING)  # per D-7227 green at ceiling
    assert g > 150 and r < 80 and b < 80


def test_rgb_clamps_above_ceiling_to_green():
    # per D-7227 values above ceiling clamp to green, no crash / NaN
    ceil = feasible_score_to_rgb(SCORE_CEILING)
    assert feasible_score_to_rgb(2.0) == ceil
    assert feasible_score_to_rgb(1e9) == ceil


def test_rgb_clamps_below_zero_to_red():
    # per D-7227 clamp surprises; negatives -> red end
    assert feasible_score_to_rgb(-0.5) == feasible_score_to_rgb(0.0)
    assert feasible_score_to_rgb(-1e9) == feasible_score_to_rgb(0.0)


def test_rgb_continuous_monotone_red_to_green():
    # per D-7227 continuous gradient (not bins): better -> greener, worse -> redder
    scores = [i * SCORE_CEILING / 28 for i in range(29)]
    rgbs = [feasible_score_to_rgb(s) for s in scores]
    greens = [c[1] for c in rgbs]
    reds = [c[0] for c in rgbs]
    assert all(b >= a for a, b in zip(greens, greens[1:]))
    # red channel falls (non-increasing) once past yellow
    mid = len(rgbs) // 2
    assert all(b <= a for a, b in zip(reds[mid:], reds[mid + 1 :]))
    # more than three distinct colours -> not three bins
    assert len(set(rgbs)) > 10


def test_rgb_never_pure_black():
    # per D-8acb black reserved for infeasible; gradient never emits it
    for i in range(0, 150):
        assert feasible_score_to_rgb(i / 100) != (0, 0, 0)


# ------------------------------------------------------------ sample_rgba


def test_sample_rgba_feasible_evaluated():
    r, g, b, a = sample_rgba(0.7, True)
    assert (r, g, b) == feasible_score_to_rgb(0.7)  # per D-8acb ui score drives colour
    assert a == EVALUATED_OPACITY


def test_sample_rgba_feasible_induced():
    r, g, b, a = sample_rgba(0.7, True, induced=True)
    assert (r, g, b) == feasible_score_to_rgb(0.7)
    assert a == INDUCED_OPACITY  # per D-85bf


def test_sample_rgba_infeasible_black_evaluated():
    r, g, b, a = sample_rgba(1.2, False)  # score ignored for fill
    assert (r, g, b) == (0, 0, 0)  # per D-8acb infeasible black
    assert a == EVALUATED_OPACITY


def test_sample_rgba_infeasible_black_induced():
    r, g, b, a = sample_rgba(1.2, False, induced=True)
    assert (r, g, b) == (0, 0, 0)
    assert a == INDUCED_OPACITY


def test_sample_rgba_ignores_companion_for_feasible_colour():
    # per D-8acb "not a silent companion swap"
    plain = sample_rgba(0.9, True)
    with_comp = sample_rgba(
        0.9, True, companion_score=0.1, infeasible_companions=[0.1, 0.2]
    )
    assert plain == with_comp


# ------------------------------------------------- infeasible_marker_t


def test_marker_t_extremes():
    comps = [0.1, 0.5, 0.9]
    assert infeasible_marker_t(0.1, comps) == pytest.approx(0.0)  # worst per D-8acb
    assert infeasible_marker_t(0.9, comps) == pytest.approx(1.0)  # best


def test_marker_t_relative_to_this_query_only():
    # same companion value gets different t in different queries (per D-8acb)
    assert infeasible_marker_t(0.5, [0.5, 0.9]) == pytest.approx(0.0)
    assert infeasible_marker_t(0.5, [0.1, 0.5]) == pytest.approx(1.0)


def test_marker_t_monotone_and_bounded():
    comps = [0.0, 0.2, 0.3, 0.8, 1.0]
    ts = [infeasible_marker_t(c, comps) for c in comps]
    assert all(0.0 <= t <= 1.0 for t in ts)
    assert ts == sorted(ts)
    assert ts[1] < ts[2] < ts[3]


def test_marker_t_empty_or_single_is_half():
    assert infeasible_marker_t(0.4, []) == 0.5
    assert infeasible_marker_t(0.4, [0.4]) == 0.5


# -------------------------------------------------- induce_neighbours


@pytest.mark.parametrize("lat", [SITE_LAT, -89.0])
def test_induce_single_site_four_stereo_neighbours(lat):
    ev = [_row(lat=lat, score=0.9, feasible=True, companion=0.9)]
    out = induce_neighbours(ev, radius_km=1.0)
    evaluated = [r for r in out if not r["induced"]]
    induced = [r for r in out if r["induced"]]
    assert len(evaluated) == 1 and len(induced) == 4  # per D-85bf, 4-neighbours

    ox, oy = _xy_km(ev[0])
    offsets = set()
    for r in induced:
        x, y = _xy_km(r)
        # exactly 1 km away in polar stereo (not ~0.009 deg lat/km approximation)
        assert math.hypot(x - ox, y - oy) == pytest.approx(1.0, abs=0.01)
        offsets.add((round(x - ox), round(y - oy)))
    assert offsets == {(1, 0), (-1, 0), (0, 1), (0, -1)}  # N/E/S/W in stereo km


def test_induce_radius_param():
    out = induce_neighbours([_row()], radius_km=2.0)
    induced = [r for r in out if r["induced"]]
    assert len(induced) == 4
    for r in induced:
        assert _dist_km(r, _row()) == pytest.approx(2.0, abs=0.02)


def test_induce_default_radius_is_one_km():
    out = induce_neighbours([_row()])
    for r in (r for r in out if r["induced"]):
        assert _dist_km(r, _row()) == pytest.approx(INDUCE_RADIUS_KM, abs=0.01)


def test_induce_evaluated_rows_flagged_false_and_preserved():
    ev = [_row(score=0.6, feasible=True, companion=0.6, window_start="t0")]
    out = induce_neighbours(ev)
    kept = [r for r in out if not r["induced"]]
    assert len(kept) == 1
    assert kept[0]["lat_deg"] == ev[0]["lat_deg"]
    assert kept[0]["lon_deg"] == ev[0]["lon_deg"]
    assert kept[0]["score"] == 0.6


def test_induce_copies_nearest_evaluated_values():
    # per D-85bf induced cells carry nearest evaluated info (not "scored")
    far_a = _row(lat=-89.46, lon=0.0, score=1.3, feasible=True, companion=1.3)
    far_b = _row(lat=-89.46, lon=180.0, score=0.0, feasible=False, companion=0.2)
    out = induce_neighbours([far_a, far_b])
    for r in (r for r in out if r["induced"]):
        parent = far_a if _dist_km(r, far_a) < _dist_km(r, far_b) else far_b
        assert r["score"] == parent["score"]
        assert r["feasible"] == parent["feasible"]
        assert r["companion_score"] == parent["companion_score"]
    assert sum(r["induced"] for r in out) == 8


def test_induce_skips_neighbour_already_evaluated():
    # B sits exactly 1 km east (stereo x) of A: shared cell must not be induced
    ax, ay = _xy_km(_row())
    # invert by search around: use induce on A alone, pick its east neighbour as B
    east = max(
        (r for r in induce_neighbours([_row()]) if r["induced"]),
        key=lambda r: _xy_km(r)[0] - ax,
    )
    b = _row(lat=east["lat_deg"], lon=east["lon_deg"], score=0.2, feasible=False, companion=0.1)
    out = induce_neighbours([_row(), b])
    induced = [r for r in out if r["induced"]]
    assert len(induced) == 6  # 3 + 3, shared cells (A east / B west) skipped
    for r in induced:
        assert _dist_km(r, _row()) > 0.1 and _dist_km(r, b) > 0.1


def test_induce_empty_input():
    assert induce_neighbours([]) == []


# -------------------------------------------------- build_region_map


def test_build_payload_shape_total_coverage():
    rows = [_row(lon=0.0), _row(lon=90.0, score=0.0, feasible=False, companion=0.3)]
    out = build_region_map(rows, search_partial=False)
    assert set(out) >= {
        "samples",
        "score_ceiling",
        "search_partial",
        "n_evaluated",
        "n_induced",
    }
    assert out["score_ceiling"] == 1.4  # per D-7227 D-48ee
    assert out["search_partial"] is False
    assert out["n_evaluated"] == 2
    assert out["n_induced"] == 0
    assert len(out["samples"]) == 2
    for s in out["samples"]:
        assert {
            "lat_deg",
            "lon_deg",
            "score",
            "feasible",
            "companion_score",
            "induced",
            "rgba",
            "is_best",
        } <= s.keys()
        assert s["induced"] is False  # per D-85bf total coverage: no induction
        assert len(s["rgba"]) == 4
        assert s["is_best"] is False


def test_build_rgba_matches_sample_rgba():
    rows = [
        _row(lon=0.0, score=0.7, feasible=True),
        _row(lon=90.0, score=0.0, feasible=False, companion=0.3),
    ]
    out = build_region_map(rows, search_partial=False)
    by_lon = {s["lon_deg"]: s for s in out["samples"]}
    assert tuple(by_lon[0.0]["rgba"][:3]) == feasible_score_to_rgb(0.7)
    assert by_lon[0.0]["rgba"][3] == EVALUATED_OPACITY
    assert tuple(by_lon[90.0]["rgba"][:3]) == (0, 0, 0)  # per D-8acb
    assert by_lon[90.0]["rgba"][3] == EVALUATED_OPACITY


def test_build_partial_adds_induced():
    out = build_region_map([_row()], search_partial=True)
    assert out["search_partial"] is True
    assert out["n_evaluated"] == 1
    assert out["n_induced"] == 4  # per D-85bf
    assert len(out["samples"]) == 5
    induced = [s for s in out["samples"] if s["induced"]]
    evaluated = [s for s in out["samples"] if not s["induced"]]
    assert len(induced) == 4 and len(evaluated) == 1
    assert all(s["rgba"][3] == INDUCED_OPACITY for s in induced)
    assert evaluated[0]["rgba"][3] == EVALUATED_OPACITY


def test_build_partial_induced_infeasible_is_black_translucent():
    out = build_region_map(
        [_row(score=0.0, feasible=False, companion=0.4)], search_partial=True
    )
    for s in (s for s in out["samples"] if s["induced"]):
        assert s["rgba"][:3] == [0, 0, 0]  # per D-8acb
        assert s["rgba"][3] == INDUCED_OPACITY


def test_build_not_partial_never_induces():
    out = build_region_map([_row()], search_partial=False)
    assert out["n_induced"] == 0
    assert not any(s["induced"] for s in out["samples"])


def test_build_dedupes_same_latlon_feasible_preferred():
    rows = [
        _row(score=0.0, feasible=False, companion=1.0, window_start="t0"),
        _row(score=0.5, feasible=True, companion=0.5, window_start="t1"),
    ]
    out = build_region_map(rows, search_partial=False)
    assert out["n_evaluated"] == 1 and len(out["samples"]) == 1
    s = out["samples"][0]
    assert s["feasible"] is True and s["score"] == 0.5


def test_build_dedupes_infeasible_higher_companion_wins():
    rows = [
        _row(score=0.0, feasible=False, companion=0.2),
        _row(score=0.0, feasible=False, companion=0.6),
        _row(score=0.0, feasible=False, companion=0.4),
    ]
    out = build_region_map(rows, search_partial=False)
    assert len(out["samples"]) == 1
    assert out["samples"][0]["companion_score"] == 0.6


def test_build_dedupes_tie_on_companion_higher_score_wins():
    rows = [
        _row(score=0.1, feasible=False, companion=0.5),
        _row(score=0.3, feasible=False, companion=0.5),
    ]
    out = build_region_map(rows, search_partial=False)
    assert len(out["samples"]) == 1
    assert out["samples"][0]["score"] == 0.3


def test_build_dedupe_order_independent():
    a = _row(score=0.0, feasible=False, companion=0.2)
    b = _row(score=0.9, feasible=True, companion=0.9)
    for rows in ([a, b], [b, a]):
        out = build_region_map(rows, search_partial=False)
        assert out["samples"][0]["feasible"] is True


def test_build_marks_best_within_tolerance():
    rows = [_row(lon=0.0), _row(lon=90.0, score=1.1)]
    best = dict(rows[1], lon_deg=90.0 + 5e-5)  # within 1e-4 deg
    out = build_region_map(rows, search_partial=False, best=best)
    flags = {s["lon_deg"]: s["is_best"] for s in out["samples"]}
    assert flags == {0.0: False, 90.0: True}


def test_build_best_outside_tolerance_not_marked():
    rows = [_row(lon=0.0)]
    best = dict(rows[0], lon_deg=0.01)
    out = build_region_map(rows, search_partial=False, best=best)
    assert not any(s["is_best"] for s in out["samples"])


def test_build_best_none_marks_nothing():
    out = build_region_map([_row()], search_partial=True, best=None)
    assert not any(s["is_best"] for s in out["samples"])


def test_build_best_not_set_on_induced_in_partial():
    rows = [_row()]
    out = build_region_map(rows, search_partial=True, best=rows[0])
    assert sum(s["is_best"] for s in out["samples"]) == 1
    assert all(not s["induced"] for s in out["samples"] if s["is_best"])


def test_build_empty_rows():
    out = build_region_map([], search_partial=True)
    assert out["samples"] == []
    assert out["n_evaluated"] == 0 and out["n_induced"] == 0
    assert out["score_ceiling"] == 1.4
