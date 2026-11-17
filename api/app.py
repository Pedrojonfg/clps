from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="lunar-eval", version="0.2.0")

# The desktop app (Tauri webview) and the Pages build call a hosted API cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "https://pedrojonfg.github.io",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
SCHEDULE_VERSION = "D-f369-v1"


@app.get("/map.html")
def map_page() -> FileResponse:
    """S9 region map page. # per D-4126"""
    return FileResponse(WEB_DIR / "map.html")


@app.get("/map.js")
def map_js() -> FileResponse:
    return FileResponse(WEB_DIR / "map.js", media_type="text/javascript")


@app.get("/firstperson.html")
def firstperson_page() -> FileResponse:
    """S10 first-person Cesium view."""
    return FileResponse(WEB_DIR / "firstperson.html")


@app.get("/firstperson.js")
def firstperson_js() -> FileResponse:
    return FileResponse(WEB_DIR / "firstperson.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="web-assets")


MASK_AZIMUTH_ZERO_DEG = 180.0  # per D-20261116-pj-b43a: geographic az of mask index 0
MASK_AZIMUTH_SIGN = -1  # geographic_az = zero + sign * index_az (see visibility._mask_el_at_geo_az)


def _mock_local_search(anchor: datetime, window_hours: int, scored: dict) -> dict:
    """Synthetic time-slide leaderboard in the real shape and order. # per D-20261116-pj-4902"""
    from lunar_eval.search.local import _sort_key

    base = float(scored["score"]) if scored["feasible"] else 0.9
    rows = []
    for off in range(-window_hours, window_hours + 1):
        # Smooth made-up quality over the slide, with an infeasible stretch on one side.
        q = 0.78 + 0.22 * math.cos(math.radians(off * 9.0 + 25.0)) - 0.004 * abs(off)
        feasible = scored["feasible"] if off == 0 else not (-19 <= off <= -12)
        companion = base * q if off else float(scored.get("companion_score", base))
        rows.append(
            {
                "site": {"lat_deg": -89.46316, "lon_deg": 222.51045},
                "window_start": anchor + timedelta(hours=off),
                "window_hours": window_hours,
                "feasible": feasible,
                "score": round(companion, 4) if feasible else 0.0,
                "companion_score": round(companion if feasible else 0.35 * companion, 4),
                "hazard_gap_star": off in (7, 8),
                "distance_hours": float(abs(off)),
                "distance_km": 0.0,
            }
        )
    board = sorted(rows, key=_sort_key)
    for r in board:
        r["window_start"] = r["window_start"].isoformat().replace("+00:00", "Z")
    return {"pick": board[0], "leaderboard": board}


def _mock_site_payload(local_search: bool = False) -> dict:
    """Explicit mock: made-up horizon and sky, scored by the real series and score code."""
    import numpy as np

    from lunar_eval.score import score
    from lunar_eval.visibility import _mask_el_at_geo_az, longest_lit_h, longest_night_h, sun_fraction

    t0 = datetime(2026, 6, 21, 0, 0, tzinfo=timezone.utc)

    def horizon_geo(az: float) -> float:
        h = 0.9 + 0.7 * math.sin(math.radians(az * 2.17))
        if 145 < az < 235:
            h += 2.6 * math.exp(-((az - 192) ** 2) / 180)
        return h

    # Stored like real masks: index azimuth runs from the pole direction, mirrored (D-b43a).
    mask_elev = [
        round(horizon_geo((MASK_AZIMUTH_ZERO_DEG + MASK_AZIMUTH_SIGN * i * 0.5) % 360.0), 4)
        for i in range(720)
    ]

    sky: list[dict] = []
    for h in range(24):
        ts = t0 + timedelta(hours=h)
        sky.append(
            {
                "time_utc": ts.isoformat().replace("+00:00", "Z"),
                "sun_az_deg": round(((h / 24.0) * 360 + 12) % 360, 2),
                "sun_el_deg": round(1.25 + 0.95 * math.sin(math.radians((h - 3) * 15)), 3),
                "earth_az_deg": round(20 + 6 * math.sin(math.radians(h * 15)), 2),
                "earth_el_deg": round(2.2 + 2.0 * math.sin(math.radians(h * 15 - 40)), 3),
            }
        )

    elev = np.asarray(mask_elev)
    sun_frac = sun_fraction(
        np.array([s["sun_el_deg"] for s in sky]),
        _mask_el_at_geo_az(np.array([s["sun_az_deg"] for s in sky]), elev),
        0.2665,
    )
    earth_frac = sun_fraction(
        np.array([s["earth_el_deg"] for s in sky]),
        _mask_el_at_geo_az(np.array([s["earth_az_deg"] for s in sky]), elev),
        0.95,
    )
    sun_frac = [round(float(v), 4) for v in sun_frac]
    earth_frac = [round(float(v), 4) for v in earth_frac]

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
    sun_arr, earth_arr = np.asarray(sun_frac), np.asarray(earth_frac)
    series = {
        "sun_fraction": sun_frac,
        "earth_fraction": earth_frac,
        "longest_night_h": longest_night_h(sun_arr, 0.5),
        "longest_no_earth_h": longest_night_h(earth_arr, 0.5),
        "longest_lit_h": longest_lit_h(sun_arr, lit_threshold=0.5, bridge_h=5),
        "hours_sun_above_threshold": int(np.sum(sun_arr > 0.5)),
        "hours_earth_above_threshold": int(np.sum(earth_arr > 0.5)),
        "any_both": bool(np.any((sun_arr > 0.5) & (earth_arr > 0.5))),
        "schedule_version": SCHEDULE_VERSION,
    }
    scored = score(series, {}, needs)
    payload = {
        "data_source": "mock",
        "mask": {
            "elevation_deg": mask_elev,
            "azimuth_zero_deg": MASK_AZIMUTH_ZERO_DEG,
            "azimuth_sign": MASK_AZIMUTH_SIGN,
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
    if local_search:
        payload["local_search"] = _mock_local_search(t0, len(sky) - 1, scored)
    return payload


class RegionMapBody(BaseModel):
    rows: list[dict[str, Any]]
    search_partial: bool
    best: dict[str, Any] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/region-map")
def region_map(body: RegionMapBody) -> dict[str, Any]:
    from lunar_eval.region_map import build_region_map

    return build_region_map(body.rows, search_partial=body.search_partial, best=body.best)


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
    max_temperature_k: str | None = Query(None, description="K; empty/none = no limit; absent = template/default"),
    min_temperature_k: str | None = Query(None, description="K; empty/none = no limit; absent = template/default"),
    min_soil_resistance: str | None = Query(None, description="empty/none = no limit; absent = template/default"),
) -> dict:
    # per D-20261114-pj-8588: mock only when mock=1
    if mock == 1:
        return _mock_site_payload(local_search=local_search == 1)

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
    # per D-20261117-pj-0c5e: explicit hazard limit > template > global default; empty = off
    for key, raw in (
        ("max_temperature_k", max_temperature_k),
        ("min_temperature_k", min_temperature_k),
        ("min_soil_resistance", min_soil_resistance),
    ):
        if raw is None:
            continue
        txt = raw.strip().lower()
        try:
            needs[key] = None if txt in ("", "none") else float(txt)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"{key} must be a number or empty") from None
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
    mock: bool = Field(default=False, description="Synthetic rows for UI checks; needs no kernels or cap index")


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
    if body.mock:
        from lunar_eval.search.mock_deep import mock_deep_search

        return mock_deep_search(
            body.mode,
            body.lat_min,
            body.lat_max,
            body.lon_min,
            body.lon_max,
            body.start,
            body.window_hours,
        )
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

