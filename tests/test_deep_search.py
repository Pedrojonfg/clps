"""S7 deep search: total coverage vs multi-start hill climb on 1 km × 1 h grid.

per D-54f0 (modes, claims), D-e3cf (start_n), D-cb6b (budget default), D-8a25 (T_max),
D-1ebf (±1 cell / ±1 h neighbours), D-60a3 (leaderboard_n), D-c159 (rect grid),
D-5577 (infeasible companion ranking).
"""

from __future__ import annotations

import numpy as np
import pytest

from moonpark.providers import Site
from moonpark.score import score
from moonpark.search.deep import (
    DEFAULT_LEADERBOARD_N,
    DEFAULT_TMAX_S,
    deep_search,
)

NEEDS = {"max_night_h": 50, "max_no_earth_h": 20, "require_both": False}
HOURS = 4
T0 = np.datetime64("2026-06-01T12:00", "s")
ROW_KEYS = {
    "site",
    "window_start",
    "window_hours",
    "feasible",
    "score",
    "companion_score",
    "hazard_gap_star",
}
RESULT_KEYS = {
    "mode",
    "claim",
    "best",
    "leaderboard",
    "rows_evaluated",
    "runtime_s",
    "eta_s",
    "n_starts",
}


def _t(x) -> np.datetime64:
    return np.datetime64(str(x).replace("Z", ""), "s")


def _series(night: int = 40, no_earth: int = 10) -> dict:
    return {"longest_night_h": night, "longest_no_earth_h": no_earth, "any_both": True}


def _hourly_starts(n: int, *, base: np.datetime64 = T0) -> np.ndarray:
    # ponytail: arange hours then cast — avoid timedelta×timedelta
    return base + np.arange(n, dtype="int64").astype("timedelta64[h]")


def _grid_3x3() -> tuple[list[Site], list[tuple[float, float]]]:
    sites: list[Site] = []
    xy: list[tuple[float, float]] = []
    for iy in range(3):
        for ix in range(3):
            sites.append(Site(lat_deg=-89.5 + iy * 0.001, lon_deg=ix * 0.001))
            xy.append((float(ix * 1000), float(iy * 1000)))
    return sites, xy


def _site_index(sites: list[Site], site: Site) -> int:
    for i, s in enumerate(sites):
        if s.lat_deg == site.lat_deg and s.lon_deg == site.lon_deg:
            return i
    raise ValueError("site not in grid")


def _deep_rank_key(row: dict) -> tuple:
    """Contract ranking: feasible by higher score; infeasible by higher companion."""
    if row["feasible"]:
        return (0, -row["score"])
    return (1, -row["companion_score"])


def _assert_leaderboard_ranked(board: list[dict]) -> None:
    keys = [_deep_rank_key(r) for r in board]
    assert keys == sorted(keys)


def _assert_row_shape(row: dict | None) -> None:
    if row is None:
        return
    assert ROW_KEYS <= row.keys()
    assert {"lat_deg", "lon_deg"} <= row["site"].keys()
    assert "distance_hours" not in row
    assert "distance_km" not in row


def _run(
    evaluate,
    *,
    sites,
    starts,
    mode: str = "optimized",
    start_n: int | None = 1,
    site_xy=None,
    **kwargs,
):
    return deep_search(
        sites,
        starts,
        HOURS,
        NEEDS,
        evaluate=evaluate,
        mode=mode,
        start_n=start_n,
        site_xy=site_xy,
        **kwargs,
    )


def test_module_defaults() -> None:
    """per D-8a25, D-60a3."""
    assert DEFAULT_TMAX_S == 300.0
    assert DEFAULT_LEADERBOARD_N == 20


def test_total_coverage_enumerates_and_claims_grid_optimum() -> None:
    """per D-54f0 total_coverage: full cross-product, true global feasible max."""
    sites = [
        Site(lat_deg=-89.5, lon_deg=0.0),
        Site(lat_deg=-89.5, lon_deg=0.001),
    ]
    starts = _hourly_starts(3)
    evals: list[tuple[int, int]] = []

    def evaluate(site, start, hours):
        assert hours == HOURS
        si = _site_index(sites, site)
        ti = int((np.datetime64(start, "s") - starts[0]) / np.timedelta64(1, "h"))
        evals.append((si, ti))
        # Global best: site 1 at middle hour (night 15); others worse.
        night = 15 if (si, ti) == (1, 1) else 20 + si + ti
        return {"series": _series(night=night)}

    out = _run(evaluate, sites=sites, starts=starts, mode="total_coverage", start_n=None)
    assert out["mode"] == "total_coverage"
    assert out["claim"] == "grid_optimum"
    assert out["n_starts"] == 0
    assert out["rows_evaluated"] == len(sites) * len(starts)
    assert len(evals) == len(sites) * len(starts)
    assert RESULT_KEYS <= out.keys()
    best = out["best"]
    _assert_row_shape(best)
    assert best is not None and best["feasible"] is True
    assert best["site"]["lon_deg"] == pytest.approx(sites[1].lon_deg)
    assert _t(best["window_start"]) == starts[1]
    _assert_leaderboard_ranked(out["leaderboard"])


def test_optimized_multistart_hill_climb_on_3x3_grid() -> None:
    """per D-54f0 optimized, D-1ebf ±1 cell/h; D-e3cf explicit start_n; claim best_seen."""
    sites, xy = _grid_3x3()
    starts = _hourly_starts(3)
    peak_ix, peak_iy, peak_ti = 2, 2, 2

    def evaluate(site, start, hours):
        si = _site_index(sites, site)
        ix, iy = si % 3, si // 3
        ti = int((np.datetime64(start, "s") - starts[0]) / np.timedelta64(1, "h"))
        # Unimodal toward peak: higher score (lower night) at (2,2) t2.
        night = 10 + abs(ix - peak_ix) * 8 + abs(iy - peak_iy) * 8 + abs(ti - peak_ti) * 4
        return {"series": _series(night=night)}

    out = _run(
        evaluate,
        sites=sites,
        starts=starts,
        mode="optimized",
        start_n=9,
        site_xy=xy,
        leaderboard_n=DEFAULT_LEADERBOARD_N,
    )
    assert out["mode"] == "optimized"
    assert out["claim"] == "best_seen"
    assert out["n_starts"] == 9
    assert out["rows_evaluated"] < len(sites) * len(starts)
    assert len(out["leaderboard"]) <= DEFAULT_LEADERBOARD_N
    best = out["best"]
    _assert_row_shape(best)
    assert best is not None and best["feasible"] is True
    bi = _site_index(sites, Site(**best["site"]))
    assert bi == peak_ix + 3 * peak_iy
    assert _t(best["window_start"]) == starts[peak_ti]
    expected = score(_series(night=10), {}, NEEDS)["score"]
    assert best["score"] == pytest.approx(expected)


def test_default_start_n_scales_with_tmax() -> None:
    """per D-cb6b / D-8a25: derive start_n from budget; monotonic in tmax_s."""
    sites, xy = _grid_3x3()
    starts = _hourly_starts(2)

    def evaluate(site, start, hours):
        return {"series": _series(night=30)}

    low = _run(
        evaluate,
        sites=sites,
        starts=starts,
        mode="optimized",
        start_n=None,
        site_xy=xy,
        tmax_s=60.0,
        cost_per_eval_s=0.5,
    )
    high = _run(
        evaluate,
        sites=sites,
        starts=starts,
        mode="optimized",
        start_n=None,
        site_xy=xy,
        tmax_s=600.0,
        cost_per_eval_s=0.5,
    )
    assert low["n_starts"] >= 1
    assert high["n_starts"] >= low["n_starts"]


def test_invalid_mode_raises() -> None:
    sites = [Site(lat_deg=-89.5, lon_deg=0.0)]
    starts = _hourly_starts(1)

    def evaluate(site, start, hours):
        return {"series": _series()}

    with pytest.raises(ValueError, match="mode"):
        _run(evaluate, sites=sites, starts=starts, mode="brute_force")


@pytest.mark.parametrize(
    "sites,starts",
    [
        ([], _hourly_starts(2)),
        ([Site(lat_deg=-89.5, lon_deg=0.0)], np.array([], dtype="datetime64[s]")),
    ],
)
def test_empty_sites_or_starts(sites, starts) -> None:
    def evaluate(site, start, hours):
        return {"series": _series()}

    out = _run(evaluate, sites=sites, starts=starts, mode="total_coverage")
    assert out["best"] is None
    assert out["leaderboard"] == []


def test_leaderboard_prefers_feasible_then_companion_for_infeasible() -> None:
    """per D-5577: deep board without distance_hours tie-break."""
    sites = [Site(lat_deg=-89.5, lon_deg=0.0)]
    starts = _hourly_starts(2)
    mild, bad = _series(night=55), _series(night=75)

    def evaluate(site, start, hours):
        ti = int((np.datetime64(start, "s") - starts[0]) / np.timedelta64(1, "h"))
        return {"series": mild if ti == 0 else bad}

    out = _run(evaluate, sites=sites, starts=starts, mode="total_coverage")
    board = out["leaderboard"]
    assert len(board) == 2
    assert board[0]["feasible"] is False
    assert board[0]["score"] == 0
    assert board[0]["companion_score"] > board[1]["companion_score"]