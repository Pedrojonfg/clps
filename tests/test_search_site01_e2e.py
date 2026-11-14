"""Site01 local search E2E (D-52bd). Skipped without kernels/DEM."""

from __future__ import annotations

import numpy as np
import pytest

from lunar_eval.planner_payload import build_planner_payload
from lunar_eval.providers import Site
from lunar_eval.search.local import local_search
from lunar_eval.site01 import SITE01, real_data_available

pytestmark = pytest.mark.skipif(not real_data_available(), reason="Site01 DEM or kernels not present")

NEEDS = {"max_night_h": 72, "max_no_earth_h": 48, "require_both": False}
HOURS = 24
A = np.datetime64("2027-01-01T00:00:00", "s")


def _evaluate(site, start, hours):
    start = np.datetime64(str(start).replace("Z", ""), "s")
    times = start + (np.arange(hours + 1) * 3600).astype("timedelta64[s]")
    payload = build_planner_payload(
        site, times, needs=NEEDS, sun_lit_percent=0, earth_lit_percent=0, bridge_h=5, hazards_enabled=False
    )
    return {"series": payload["series"], "hazards": {}, "hazard_gap_star": False}


def test_site01_local_search_returns_ranked_leaderboard_within_slide() -> None:
    neighbour = Site(lat_deg=SITE01.lat_deg, lon_deg=SITE01.lon_deg + 0.0005, observer_height_m=2.0)
    result = local_search(
        SITE01, A, HOURS, NEEDS, evaluate=_evaluate, neighbour_sites=[neighbour], radius_km=5.0
    )
    board = result["leaderboard"]
    assert board and board[0] == result["pick"]
    assert all(0 <= r["distance_hours"] <= HOURS for r in board)
    assert all(r["distance_km"] <= 5.0 for r in board)
    assert all(r["feasible"] or r["score"] == 0 for r in board)
