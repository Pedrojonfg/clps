from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

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
    from lunar_eval.visibility import longest_lit_h, longest_night_h

    needs = {
        "max_night_h": 72,
        "max_no_earth_h": 48,
        "require_both": False,
        "min_continuous_lit_h": 0,
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
        "longest_lit_h": longest_lit_h(sun_frac, lit_threshold=0.0, bridge_h=5),
        "hours_sun_above_threshold": int(sum(1 for v in sun_frac if v > 0.0)),
        "hours_earth_above_threshold": int(sum(1 for v in earth_frac if v > 0.0)),
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
    min_continuous_lit_h: int = Query(0, ge=0),
    require_both: bool = Query(False),
    sun_lit_percent: float = Query(0, ge=0, le=100),
    earth_lit_percent: float = Query(0, ge=0, le=100),
    bridge_h: int = Query(5, ge=0, le=48),
    hazards_enabled: bool = Query(True),
    local_search: int = Query(0, description="1 = include local_search block"),
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
        "min_continuous_lit_h": min_continuous_lit_h,
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
            local_search=local_search == 1,
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


class DeepSearchBody(BaseModel):
    """POST /deep-search body. # per D-60a3 D-c159 D-54f0"""

    mode: str = Field(default="optimized")
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    start: str
    end: str
    window_hours: int = Field(default=24, ge=1, le=168)
    template_id: str | None = None
    start_n: int | None = None
    hazards_enabled: bool = False
    format: str = Field(default="json", description="json | csv")


def _iso_row(row: dict | None) -> dict | None:
    if row is None:
        return None
    out = dict(row)
    import numpy as np

    out["window_start"] = str(np.datetime64(row["window_start"], "s")) + "Z"
    return out


@app.post("/deep-search")
def deep_search_endpoint(body: DeepSearchBody):
    # per D-60a3 dedicated endpoint; D-54f0 modes; D-c159 rect snap
    from lunar_eval.ephemeris import SpiceEphemeris
    from lunar_eval.horizon.cap_index import (
        cap_index_available,
        mask_from_cap_tile,
        sites_in_latlon_rect,
    )
    from lunar_eval.planner_payload import kernels_available, parse_time_window
    from lunar_eval.planner_templates import template_needs
    from lunar_eval.search.deep import DEFAULT_LEADERBOARD_N, DEFAULT_TMAX_S, deep_search
    from lunar_eval.visibility import series as vis_series

    if not kernels_available():
        raise HTTPException(
            status_code=503,
            detail={"error": "kernels_missing", "message": "SPICE kernels not on disk"},
        )
    if not cap_index_available():
        raise HTTPException(
            status_code=503,
            detail={"error": "cap_missing", "message": "1 km cap index not on disk"},
        )

    tpl = template_needs(body.template_id)
    if tpl:
        needs = {
            "max_night_h": int(tpl["max_night_h"]),
            "max_no_earth_h": int(tpl["max_no_earth_h"]),
            "require_both": bool(tpl["require_both"]),
            "min_continuous_lit_h": int(tpl.get("min_continuous_lit_h", 0)),
        }
        sun_pct = float(tpl["sun_lit_percent"])
        earth_pct = float(tpl["earth_lit_percent"])
        bridge = int(tpl["bridge_h"])
    else:
        needs = {
            "max_night_h": 72,
            "max_no_earth_h": 48,
            "require_both": False,
            "min_continuous_lit_h": 0,
        }
        sun_pct, earth_pct, bridge = 0.0, 0.0, 5

    cells = sites_in_latlon_rect(body.lat_min, body.lat_max, body.lon_min, body.lon_max)
    if not cells:
        raise HTTPException(
            status_code=400,
            detail={"error": "empty_rect", "message": "No cap cells in rectangle"},
        )

    try:
        span = parse_time_window(body.start, body.end, step_h=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "bad_time", "message": str(e)}) from e

    # Window starts: hours where a full window_hours block fits in span.
    wh = int(body.window_hours)
    if len(span) < wh + 1:
        raise HTTPException(
            status_code=400,
            detail={"error": "time_too_short", "message": "end-start must cover window_hours"},
        )
    import numpy as np

    n_starts = len(span) - wh
    starts = span[:n_starts]
    sites = [c[0] for c in cells]
    site_xy = [(c[1], c[2]) for c in cells]

    eph = SpiceEphemeris()
    sun_thr = max(0.0, min(100.0, sun_pct)) / 100.0
    earth_thr = max(0.0, min(100.0, earth_pct)) / 100.0
    sky_by_site: dict[int, list] = {}

    def evaluate(candidate, start, hours: int) -> dict:
        idx = None
        for i, s in enumerate(sites):
            if s.lat_deg == candidate.lat_deg and s.lon_deg == candidate.lon_deg:
                idx = i
                break
        if idx is None:
            raise ValueError("site not in rect cells")
        _site, _x, _y, tx, ty, row = cells[idx]
        horizon = mask_from_cap_tile(tx, ty, row)
        if idx not in sky_by_site:
            sky_by_site[idx] = eph.sky(candidate, span)
        t0 = np.datetime64(start, "s")
        i0 = int((t0 - np.datetime64(span[0], "s")) / np.timedelta64(1, "h"))
        sky_win = sky_by_site[idx][i0 : i0 + int(hours) + 1]
        vis = vis_series(
            sky_win,
            horizon,
            sun_threshold=sun_thr,
            earth_threshold=earth_thr,
            bridge_h=bridge,
        )
        return {"series": vis, "hazards": {}, "hazard_gap_star": False}

    try:
        result = deep_search(
            sites,
            starts,
            wh,
            needs,
            evaluate=evaluate,
            mode=body.mode,
            start_n=body.start_n,
            tmax_s=DEFAULT_TMAX_S,
            leaderboard_n=DEFAULT_LEADERBOARD_N,
            site_xy=site_xy,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "deep_failed", "message": str(e)}) from e

    export = result.get("export_rows") or result["leaderboard"]
    payload = {
        "mode": result["mode"],
        "claim": result["claim"],
        "best": _iso_row(result["best"]),
        "leaderboard": [_iso_row(r) for r in result["leaderboard"]],
        "export_rows": [_iso_row(r) for r in export],
        "rows_evaluated": result["rows_evaluated"],
        "runtime_s": result["runtime_s"],
        "eta_s": result["eta_s"],
        "n_starts": result["n_starts"],
        "n_sites": len(sites),
        "n_window_starts": int(n_starts),
        "provisional": True,  # per D-0ee7 until megatest
    }

    if body.format == "csv":
        import csv
        import io

        buf = io.StringIO()
        fields = [
            "lat_deg",
            "lon_deg",
            "window_start",
            "window_hours",
            "feasible",
            "score",
            "companion_score",
            "hazard_gap_star",
        ]
        w = csv.DictWriter(buf, fieldnames=fields)
        w.writeheader()
        for r in export:
            w.writerow(
                {
                    "lat_deg": r["site"]["lat_deg"],
                    "lon_deg": r["site"]["lon_deg"],
                    "window_start": str(np.datetime64(r["window_start"], "s")) + "Z",
                    "window_hours": r["window_hours"],
                    "feasible": r["feasible"],
                    "score": r["score"],
                    "companion_score": r["companion_score"],
                    "hazard_gap_star": r["hazard_gap_star"],
                }
            )
        return PlainTextResponse(buf.getvalue(), media_type="text/csv")

    return payload

