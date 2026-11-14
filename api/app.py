from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="lunar-eval", version="0.1.0")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

SITE01_LAT = -89.46316
SITE01_LON = 222.51045
SCHEDULE_VERSION = "D-f369-v1"
SCORE_FORMULA = "two_layer_zero_then_assurance_then_weights"


def _mock_elevation_deg() -> list[float]:
    """Jagged south-polar ridge silhouette — 720 half-degree azimuth bins."""
    elev: list[float] = []
    for i in range(720):
        az = i * 0.5
        h = 1.6 + 0.85 * math.sin(math.radians(az * 2.17))
        h += 0.38 * math.sin(math.radians(az * 5.9 + 33))
        h += 0.22 * math.cos(math.radians(az * 12.4 - 70))
        if 145 < az < 235:
            h += 2.8 * math.exp(-((az - 192) ** 2) / 180)
        if 310 < az or az < 35:
            h += 0.55 * math.sin(math.radians(az * 8))
        elev.append(round(h, 4))
    return elev


def _mock_site_payload() -> dict:
    t0 = datetime(2026, 6, 21, 0, 0, tzinfo=timezone.utc)
    sky: list[dict] = []
    sun_frac: list[float] = []
    earth_frac: list[float] = []
    mask_elev = _mock_elevation_deg()

    def mask_at(az_deg: float) -> float:
        idx = int(round(az_deg * 2)) % 720
        return mask_elev[idx]

    for h in range(24):
        ts = t0 + timedelta(hours=h)
        phase = h / 24.0
        sun_az = (phase * 360 + 12) % 360
        sun_el = -2.4 + 4.8 * max(0, math.sin(math.radians((h - 6) * 15)))
        earth_az = (sun_az + 118 + 6 * math.sin(math.radians(h * 22))) % 360
        earth_el = 4.5 + 3.2 * math.sin(math.radians(h * 18 - 40))

        sun_up = sun_el > mask_at(sun_az)
        earth_up = earth_el > 0.5
        both = sun_up and earth_up

        sky.append(
            {
                "time_utc": ts.isoformat().replace("+00:00", "Z"),
                "sun_az_deg": round(sun_az, 2),
                "sun_el_deg": round(sun_el, 3),
                "earth_az_deg": round(earth_az, 2),
                "earth_el_deg": round(earth_el, 3),
            }
        )
        sun_frac.append(1.0 if sun_up else 0.0)
        earth_frac.append(1.0 if earth_up else 0.0)

    from lunar_eval.score import score
    from lunar_eval.visibility import longest_night_h

    needs = {"max_night_h": 72, "max_no_earth_h": 48, "require_both": False}
    series = {
        "sun_fraction": sun_frac,
        "earth_fraction": earth_frac,
        "longest_night_h": longest_night_h(sun_frac),
        "longest_no_earth_h": longest_night_h(earth_frac),
        "any_both": any(sf and ef for sf, ef in zip(sun_frac, earth_frac, strict=True)),
        "schedule_version": SCHEDULE_VERSION,
    }
    scored = score(series, {}, needs)
    return {
        "mask": {
            "elevation_deg": mask_elev,
            "schedule_version": SCHEDULE_VERSION,
            "lat": SITE01_LAT,
            "lon": SITE01_LON,
        },
        "sky": sky,
        "series": series,
        "score": scored,
        "needs": needs,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/site")
def site() -> dict:
    return _mock_site_payload()