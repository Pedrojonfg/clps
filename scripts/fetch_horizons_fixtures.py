#!/usr/bin/env python3
"""Fetch Horizons observer tables once (P7). One request at a time."""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "moonpark/0.1 (+https://github.com/Pedrojonfg/moonpark)"
OUT = Path(__file__).resolve().parent.parent / "tests/fixtures/horizons"
SITES = {
    "Site01": (-89.46316, 222.51045),
    "Site04": (-89.76681, 188.13010),
    "Site07": (-88.81101, 123.69007),
}
WINDOWS = [("2027-01-01", "2027-03-01"), ("2027-07-01", "2027-09-01")]


def fetch(command: str, lat: float, lon: float, start: str, stop: str) -> str:
    q = {
        "format": "json",
        "EPHEM_TYPE": "OBSERVER",
        "COMMAND": command,
        "CENTER": "coord@301",
        "COORD_TYPE": "GEODETIC",
        "SITE_COORD": f"'{lon},{lat},0'",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "6 hours",
        "QUANTITIES": "4",
        "ANG_FORMAT": "DEG",
        "CSV_FORMAT": "YES",
    }
    url = "https://ssd.jpl.nasa.gov/api/horizons.api?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        payload = json.loads(r.read().decode())
    return payload["result"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (lat, lon) in SITES.items():
        for start, stop in WINDOWS:
            tag = f"{name}_{start}_{stop}".replace("-", "")
            for body, cmd in ("sun", "10"), ("earth", "399"):
                dest = OUT / f"{tag}_{body}.txt"
                if dest.exists() and dest.stat().st_size > 100:
                    print("skip", dest.name)
                    continue
                print("fetch", dest.name)
                dest.write_text(fetch(cmd, lat, lon, start, stop), encoding="utf-8")
                time.sleep(1.1)


if __name__ == "__main__":
    main()
