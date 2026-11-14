from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

app = FastAPI(title="lunar-eval", version="0.2.0")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
SCHEDULE_VERSION = "D-f369-v1"


def _mock_site_payload() -> dict:
    """Explicit CI-only mock. # ponytail: legacy shape for contract tests."""
    t0 = datetime(2026, 6, 21, 0, 0, tzinfo=timezone.utc)
    sky: list[dict] = []
    sun_frac: list[float] = []
    earth_frac: list[float] = []
    mask_elev = []
    for i in range(720):
        az = i * 0.5
        h = 1.6 + 0.85 * math.sin(math.radians(az * 2.17))
        if 145 < az < 235:
            h += 2.8 * math.exp(-((az - 192) ** 2) / 180)
        mask_elev.append(round(h, 4))

    def mask_at(az_deg: float) -> float:
        return mask_elev[int(round(az_deg * 2)) % 720]

    for h in range(24):
        ts = t0 + timedelta(hours=h)
        sun_az = ((h / 24.0) * 360 + 12) % 360
        sun_el = -2.4 + 4.8 * max(0, math.sin(math.radians((h - 6) * 15)))
        earth_az = (sun_az + 118) % 360
        earth_el = 4.5 + 3.2 * math.sin(math.radians(h * 18 - 40))
        sky.append(
            {
                "time_utc": ts.isoformat().replace("+00:00", "Z"),
                "sun_az_deg": round(sun_az, 2),
                "sun_el_deg": round(sun_el, 3),
                "earth_az_deg": round(earth_az, 2),
                "earth_el_deg": round(earth_el, 3),
            }
        )
        sun_frac.append(1.0 if sun_el > mask_at(sun_az) else 0.0)
        earth_frac.append(1.0 if earth_el > 0.5 else 0.0)

    from lunar_eval.score import score
    from lunar_eval.visibility import longest_night_h

    needs = {
        "max_night_h": 72,
        "max_no_earth_h": 48,
        "require_both": False,
        "sun_lit_percent": 50,
        "earth_lit_percent": 50,
        "sun_lit_threshold": 0.5,
        "earth_lit_threshold": 0.5,
        "bridge_h": 5,
    }
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
        "data_source": "mock",
        "mask": {
            "elevation_deg": mask_elev,
            "schedule_version": SCHEDULE_VERSION,
            "lat": -89.46316,
            "lon": 222.51045,
        },
        "sky": sky,
        "series": series,
        "score": scored,
        "hazards_enabled": False,
        "needs": needs,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/mission-templates")
def mission_templates() -> dict:
    from lunar_eval.planner_templates import list_templates

    return {"templates": list_templates()}


@app.get("/site")
def site(
    mock: int = Query(0, description="1 = CI mock only"),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    start: str | None = Query(None),
    end: str | None = Query(None),
    step_h: int = Query(1, ge=1, le=24),
    template_id: str | None = Query(None),
    max_night_h: int | None = Query(None),
    max_no_earth_h: int | None = Query(None),
    require_both: bool = Query(False),
    sun_lit_percent: float = Query(0, ge=0, le=100),
    earth_lit_percent: float = Query(0, ge=0, le=100),
    bridge_h: int = Query(5, ge=0, le=48),
    hazards_enabled: bool = Query(True),
) -> dict:
    # per D-20261114-pj-8588: mock only when mock=1
    if mock == 1:
        return _mock_site_payload()

    from lunar_eval.planner_payload import build_planner_payload, kernels_available, parse_time_window
    from lunar_eval.planner_templates import DEMO_SITE01, template_needs
    from lunar_eval.providers import Site

    if not kernels_available():
        raise HTTPException(
            status_code=503,
            detail={"error": "kernels_missing", "message": "SPICE kernels not on disk; use mock=1 in CI."},
        )

    tpl = template_needs(template_id)
    lat_v = float(lat if lat is not None else DEMO_SITE01["lat_deg"])
    lon_v = float(lon if lon is not None else DEMO_SITE01["lon_deg"])
    start_v = start or "2027-01-01T00:00:00Z"
    end_v = end or "2027-01-01T23:00:00Z"

    needs = tpl or {
        "max_night_h": max_night_h if max_night_h is not None else 72,
        "max_no_earth_h": max_no_earth_h if max_no_earth_h is not None else 48,
        "require_both": require_both,
    }
    if tpl:
        sun_pct = tpl["sun_lit_percent"]
        earth_pct = tpl["earth_lit_percent"]
        bridge = tpl["bridge_h"]
    else:
        sun_pct = sun_lit_percent
        earth_pct = earth_lit_percent
        bridge = bridge_h

    site_obj = Site(lat_deg=lat_v, lon_deg=lon_v, observer_height_m=2.0)
    try:
        times = parse_time_window(start_v, end_v, step_h=step_h)
        return build_planner_payload(
            site_obj,
            times,
            needs=needs,
            sun_lit_percent=sun_pct,
            earth_lit_percent=earth_pct,
            bridge_h=bridge,
            hazards_enabled=hazards_enabled,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "dem_missing", "message": str(e)},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "planner_failed", "message": str(e)},
        ) from e