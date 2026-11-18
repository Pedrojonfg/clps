"""Site01 first-week aggregate golden (D-beb5). # per D-7520 D-6ce5"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from moonpark.planner_payload import build_planner_payload, parse_time_window
from moonpark.site01 import SITE01, real_data_available

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "fixtures" / "site01_week_aggregates.json"

AGG_KEYS = (
    "longest_night_h",
    "longest_no_earth_h",
    "longest_lit_h",
    "hours_sun_above_threshold",
    "hours_earth_above_threshold",
)

pytestmark = pytest.mark.skipif(not real_data_available(), reason="Site01 DEM or kernels not present")


def _week_payload() -> dict:
    times = parse_time_window("2027-01-01T00:00:00Z", "2027-01-07T23:00:00Z", step_h=1)
    return build_planner_payload(
        SITE01,
        times,
        needs={"max_night_h": 72, "max_no_earth_h": 48, "require_both": False, "min_continuous_lit_h": 0},
        sun_lit_percent=0,
        earth_lit_percent=0,
        bridge_h=5,
        hazards_enabled=False,
    )


def test_week_series_has_aggregate_keys_and_bounds() -> None:
    s = _week_payload()["series"]
    n = len(s["sun_fraction"])
    assert n == 7 * 24
    for key in AGG_KEYS:
        assert key in s, f"series missing {key}"
        assert isinstance(s[key], int)
        assert 0 <= s[key] <= n
    assert s["hours_sun_above_threshold"] == sum(1 for v in s["sun_fraction"] if v > 0.0)
    assert s["hours_earth_above_threshold"] == sum(1 for v in s["earth_fraction"] if v > 0.0)


@pytest.mark.skipif(not GOLDEN.is_file(), reason="golden fixture not generated yet")
def test_week_series_matches_golden_fixture() -> None:
    golden = json.loads(GOLDEN.read_text())
    payload = _week_payload()
    s = payload["series"]
    sc = payload["score"]
    for key in AGG_KEYS:
        assert s[key] == golden[key], key
    assert s["any_both"] is golden["any_both"]
    assert sc["feasible"] is golden["feasible"]
    assert sc["score"] == pytest.approx(golden["score"], abs=1e-9)
    assert sc["breakdown"].get("failing", []) == golden.get("failing", [])
    if golden.get("feasible"):
        assert sc["breakdown"]["layer1_R"] == pytest.approx(golden["layer1_R"], abs=1e-9)
        assert sc["breakdown"]["layer1_B"] == pytest.approx(golden["layer1_B"], abs=1e-9)
