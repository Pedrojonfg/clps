"""Site01 shorthand for tests. # per D-20261114-pj-da5f"""

from __future__ import annotations

from lunar_eval.planner_payload import build_planner_payload, kernels_available, parse_time_window
from lunar_eval.planner_templates import DEMO_SITE01
from lunar_eval.providers import Site

SITE01 = Site(lat_deg=DEMO_SITE01["lat_deg"], lon_deg=DEMO_SITE01["lon_deg"], observer_height_m=2.0)


def real_data_available() -> bool:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    return kernels_available() and (root / "data" / "dem" / "Site01_final_adj_5mpp_surf.tif").is_file()


def build_site01_payload() -> dict:
    times = parse_time_window("2027-01-01T00:00:00Z", "2027-01-01T23:00:00Z", step_h=1)
    needs = {"max_night_h": 72, "max_no_earth_h": 48, "require_both": False}
    return build_planner_payload(
        SITE01,
        times,
        needs=needs,
        sun_lit_percent=0,
        earth_lit_percent=0,
        bridge_h=5,
        hazards_enabled=False,
    )