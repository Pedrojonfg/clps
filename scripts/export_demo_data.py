"""Export the static browser demo's data: the API's own mock-mode responses as JSON.

Usage: python scripts/export_demo_data.py <out_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from moonpark.api.app import app

# Same rows as DEMO_ROWS in web/map.js (the region map's "Load demo").
DEMO_ROWS = [
    {"lat_deg": -89.46316, "lon_deg": 222.51045, "score": 1.05, "feasible": True, "companion_score": 1.05},
    {"lat_deg": -89.52, "lon_deg": 205.0, "score": 0.62, "feasible": True, "companion_score": 0.62},
    {"lat_deg": -89.48, "lon_deg": 248.0, "score": 0.22, "feasible": True, "companion_score": 0.22},
    {"lat_deg": -89.56, "lon_deg": 218.0, "score": 0, "feasible": False, "companion_score": 0.38},
    {"lat_deg": -89.5, "lon_deg": 238.0, "score": 0, "feasible": False, "companion_score": 0.12},
]


def moon_mock_payload(client: TestClient) -> dict:
    """Whole-Moon mock deep search (total coverage), painted through the real /region-map."""
    search = client.post(
        "/deep-search",
        json={
            "mock": True,
            "mode": "total_coverage",
            "lat_min": -90,
            "lat_max": -80,
            "lon_min": 0,
            "lon_max": 360,
            "start": "2027-01-01T00:00:00Z",
            "end": "2027-01-02T00:00:00Z",
        },
    )
    if search.status_code != 200:
        raise SystemExit(f"deep-search mock failed: {search.status_code} {search.text[:300]}")
    body = search.json()
    rows = [
        {
            "lat_deg": r["site"]["lat_deg"],
            "lon_deg": r["site"]["lon_deg"],
            "score": r["score"],
            "feasible": r["feasible"],
            "companion_score": r["companion_score"],
        }
        for r in body["export_rows"]
    ]
    best = {"lat_deg": body["best"]["site"]["lat_deg"], "lon_deg": body["best"]["site"]["lon_deg"]}
    return client.post("/region-map", json={"rows": rows, "search_partial": False, "best": best})


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    responses = {
        "mission-templates.json": client.get("/mission-templates"),
        "site-mock.json": client.get("/site?mock=1&local_search=1"),
        "region-map-demo.json": client.post(
            "/region-map",
            json={"rows": DEMO_ROWS, "search_partial": True, "best": DEMO_ROWS[0]},
        ),
        "region-map-moon-mock.json": moon_mock_payload(client),
    }
    for name, res in responses.items():
        res.raise_for_status()
        (out_dir / name).write_text(json.dumps(res.json()))
        print(f"wrote {out_dir / name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/export_demo_data.py <out_dir>")
    main(Path(sys.argv[1]))
