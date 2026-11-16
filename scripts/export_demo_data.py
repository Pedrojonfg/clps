"""Export the static browser demo's data: the API's own mock-mode responses as JSON.

Usage: python scripts/export_demo_data.py <out_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import app

# Same rows as DEMO_ROWS in web/map.js (the region map's "Load demo").
DEMO_ROWS = [
    {"lat_deg": -89.46316, "lon_deg": 222.51045, "score": 1.05, "feasible": True, "companion_score": 1.05},
    {"lat_deg": -89.52, "lon_deg": 205.0, "score": 0.62, "feasible": True, "companion_score": 0.62},
    {"lat_deg": -89.48, "lon_deg": 248.0, "score": 0.22, "feasible": True, "companion_score": 0.22},
    {"lat_deg": -89.56, "lon_deg": 218.0, "score": 0, "feasible": False, "companion_score": 0.38},
    {"lat_deg": -89.5, "lon_deg": 238.0, "score": 0, "feasible": False, "companion_score": 0.12},
]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    responses = {
        "mission-templates.json": client.get("/mission-templates"),
        "site-mock.json": client.get("/site?mock=1"),
        "region-map-demo.json": client.post(
            "/region-map",
            json={"rows": DEMO_ROWS, "search_partial": True, "best": DEMO_ROWS[0]},
        ),
    }
    for name, res in responses.items():
        res.raise_for_status()
        (out_dir / name).write_text(json.dumps(res.json()))
        print(f"wrote {out_dir / name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/export_demo_data.py <out_dir>")
    main(Path(sys.argv[1]))
