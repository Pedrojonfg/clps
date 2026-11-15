#!/usr/bin/env python3
"""S12 PGDA 69 comparison harness (D-9ab3, D-fe17, D-1a9e).

Full ~18.6 y site loop is overnight. Without the PGDA 69 map on disk this
exits 0 with SKIP and does not claim validation numbers.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "docs" / "validation.md"


def _find_pgda69() -> Path | None:
    for base in (ROOT / "data" / "pgda69", ROOT / "data" / "illumination", ROOT / "data"):
        if not base.is_dir():
            continue
        for pat in ("*AVGVISIB*S*", "*avgvisib*s*", "*PGDA*69*"):
            hits = list(base.rglob(pat))
            if hits:
                return hits[0]
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json-out", type=Path, default=None)
    p.add_argument(
        "--force-run",
        action="store_true",
        help="reserved for overnight full comparison (needs PGDA 69 file + masks)",
    )
    args = p.parse_args()

    pgda = _find_pgda69()
    status = "SKIP_NO_PGDA69_FILE" if pgda is None else "HARNESS_READY_AWAITING_OVERNIGHT"
    if args.force_run and pgda is None:
        print("error: place PGDA 69 average solar illumination under data/", file=sys.stderr)
        return 2

    payload = {
        "decision": "D-20261115-pj-9ab3",
        "role": "validation_report_and_readme_only",
        "product": "average_solar_illumination_south",
        "span": "~18.6y_or_product_label_span",
        "metric": "delta_percentage_points_per_site",
        "pass_fail": "none_v1_report_only",
        "pgda69_path": str(pgda) if pgda else None,
        "sites": "pgda78_5m_schedule_set",
        "status": status,
        "deltas": [],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    print(f"\n# Do not claim README 'validated with PGDA 69' until deltas are filled ({VALIDATION}).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
