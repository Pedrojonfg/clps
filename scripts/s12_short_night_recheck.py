#!/usr/bin/env python3
"""S12 short-night re-check harness (D-39f3, D-1a9e).

Heavy DEM/mask work is overnight. This script records a run stub or SKIP
when data is missing; it does not invent pass numbers.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "docs" / "validation.md"
SITE01 = {"name": "Site01", "lat_deg": -89.46316, "lon_deg": 222.51045}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year", type=int, default=2027, help="fixed test year (pin in report)")
    p.add_argument("--json-out", type=Path, default=None)
    p.add_argument(
        "--force-run",
        action="store_true",
        help="reserved for overnight: compute schedule vs fine reference (not implemented without DEM wiring)",
    )
    args = p.parse_args()

    dem = ROOT / "data" / "dem"
    has_dem = dem.is_dir() and any(dem.glob("*.TIF"))
    status = "SKIP_NO_DEM" if not has_dem else "HARNESS_READY_AWAITING_OVERNIGHT"
    if args.force_run and not has_dem:
        print("error: --force-run needs DEM tiles under data/dem/", file=sys.stderr)
        return 2

    payload = {
        "decision": "D-20261115-pj-39f3",
        "mode": "separate_report_reopen_y_if_over_tol",
        "tolerance_h": 5,
        "bridge_h": 5,
        "year": args.year,
        "sites": [SITE01],
        "status": status,
        "note": (
            "Overnight: compare schedule mask longest_night/lit vs fine reference; "
            "if abs error > 5 h, reopen success_y via a new decision."
        ),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    print(f"\n# Update {VALIDATION} Results section after a real overnight compute.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
