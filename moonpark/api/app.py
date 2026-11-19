from __future__ import annotations

import math
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="moonpark", version="0.2.0")

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

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
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
    from moonpark.search.local import _sort_key

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

    from moonpark.planner_payload import mask_provenance, provenance
    from moonpark.score import score
    from moonpark.visibility import (
        _mask_el_at_geo_az,
        longest_lit_bounds,
        longest_night_bounds,
        sun_fraction,
        total_lit_h,
    )

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
        "step_min": 60,
        "not_evaluated": [],
    }
    sun_arr, earth_arr = np.asarray(sun_frac), np.asarray(earth_frac)
    # Same bounds as visibility.series (D-20261118-pj-9413): maximum-type limits upper, minimum-type lower.
    night_lo, night_up = longest_night_bounds(sun_arr, 0.5)
    no_earth_lo, no_earth_up = longest_night_bounds(earth_arr, 0.5)
    lit_lo, lit_up = longest_lit_bounds(sun_arr, lit_threshold=0.5, bridge_h=5)
    series = {
        "sun_fraction": sun_frac,
        "earth_fraction": earth_frac,
        "step_min": 60,
        "longest_night_h": night_up,
        "longest_night_h_lower": night_lo,
        "longest_no_earth_h": no_earth_up,
        "longest_no_earth_h_lower": no_earth_lo,
        "longest_lit_h": lit_lo,
        "longest_lit_h_upper": lit_up,
        "hours_sun_above_threshold": total_lit_h(sun_arr, 0.5),
        "hours_earth_above_threshold": total_lit_h(earth_arr, 0.5),
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
        "hazards_status": {"status": "disabled", "unavailable": {}},
        "warnings": [],
        "provenance": provenance(
            needs=needs,
            step_min=60,
            observer_height_m=2.0,
            mask=mask_provenance(-89.46316, 222.51045, -89.46316, 222.51045, source="mock"),
            fill=None,
            hazards_enabled=False,
        ),
    }
    if local_search:
        payload["local_search"] = _mock_local_search(t0, len(sky) - 1, scored)
    return payload


class RegionMapBody(BaseModel):
    rows: list[dict[str, Any]]
    search_partial: bool
    best: dict[str, Any] | None = None


def _invalid(field: str, message: str, status: int = 422, error: str = "invalid_input") -> HTTPException:
    """Client mistake: 4xx with a message naming the field (503 stays reserved for missing data)."""
    return HTTPException(status_code=status, detail={"error": error, "field": field, "message": message})


def _utc_window(start: str, end: str) -> tuple[str, str]:
    """Parse ISO start/end (naive = UTC, offsets converted) into Z strings; ValueError when unparseable or not ordered."""
    out = []
    for name, raw in (("start", start), ("end", end)):
        try:
            t = datetime.fromisoformat(raw.strip())
        except ValueError:
            raise ValueError(f"{name} is not an ISO-8601 time: {raw!r}") from None
        t = t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)
        out.append(t)
    if out[1] <= out[0]:
        raise ValueError("end must be strictly after start")
    return tuple(f"{t:%Y-%m-%dT%H:%M:%S}Z" for t in out)  # type: ignore[return-value]


# Usage limits (D-20261118-pj-cd33): each value is the largest size measured to finish without error under a
# 3.5 GB peak (half the RAM) on one 12-core / 7 GB machine, client conditions (1 km cap masks). No time cap:
# the time budget is a target only. Measurements and method: docs/limits.md, scripts/bench_limits.py.
# None = no limit (the benchmark lifts them to measure beyond).
SITE_MAX_WINDOW_H: int | None = 70127  # /site end - start, hours: 70128 hourly steps = 2922 days (hazards off)
SITE_MAX_SAMPLES: int | None = 420763  # /site samples (end - start) / step_min + 1: 2922 days at step_min 10
LOCAL_SEARCH_MAX_WINDOW_H: int | None = 744  # /site local_search=1: window; it scores 2h+1 shifted windows
HAZARD_MAX_SPAN_H: float | None = 360.0  # hazards on: lunar local time touched, h (_hazard_span_h); 383 h > 3.5 GB
DEEP_MAX_CELLS: int | None = 145431  # /deep-search cap cells: largest rectangle measured (-89.9..-80, lon 0..180)
DEEP_MAX_EVALUATIONS: int | None = 1_680_000  # /deep-search total_coverage: cells x window starts (10000 x 168)
DEEP_MAX_SKY_SAMPLES: int | None = 1_920_000  # /deep-search total_coverage: cells x samples start..end (10000 x 192)
_SYNODIC_H = 708.734  # one lunar day in hours: 360 deg of longitude spans every local time once


def _span_h(start_z: str, end_z: str) -> float:
    """Hours from start to end of two `_utc_window` strings."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return (datetime.strptime(end_z, fmt) - datetime.strptime(start_z, fmt)).total_seconds() / 3600.0


def _hazard_span_h(span_h: float, lon_width_deg: float = 0.0) -> float:
    """Lunar local-time coverage of a request with hazards on, in hours.

    Peak memory with hazards on grows with the number of Diviner PCP local-time bins loaded (one 0.25 lunar
    hour bin ~7.4 Earth hours, ~70 MB each); a request touches the bins its time span covers, plus those its
    longitude width adds (local time shifts by one lunar day over 360 deg)."""
    return float(span_h) + min(max(float(lon_width_deg), 0.0), 360.0) / 360.0 * _SYNODIC_H


def _check_site_size(span_h: float, step_m: int, hazards_enabled: bool, local_search: bool) -> None:
    """422 naming the field when a /site request is above the measured limits (D-20261118-pj-cd33)."""
    if SITE_MAX_WINDOW_H is not None and span_h > SITE_MAX_WINDOW_H:
        raise _invalid("start/end", f"window too long: end - start is {span_h:g} h; the limit is "
                       f"{SITE_MAX_WINDOW_H} h ({SITE_MAX_WINDOW_H + 1} hourly steps)", error="limit_exceeded")
    samples = int(span_h * 60 // step_m) + 1
    if SITE_MAX_SAMPLES is not None and samples > SITE_MAX_SAMPLES:
        raise _invalid("step_min", f"too many samples: {samples} (window {span_h:g} h at step_min {step_m}); the "
                       f"limit is {SITE_MAX_SAMPLES} samples: use a larger step_min or a shorter window",
                       error="limit_exceeded")
    if local_search and LOCAL_SEARCH_MAX_WINDOW_H is not None and span_h > LOCAL_SEARCH_MAX_WINDOW_H:
        raise _invalid("local_search", f"local search window too long: end - start is {span_h:g} h; the limit "
                       f"with local_search=1 is {LOCAL_SEARCH_MAX_WINDOW_H} h", error="limit_exceeded")
    # local search scores windows shifted from start - h to start + h: its hazards cover 3 windows
    hz_span = _hazard_span_h(3 * span_h if local_search else span_h)
    if hazards_enabled and HAZARD_MAX_SPAN_H is not None and hz_span > HAZARD_MAX_SPAN_H:
        raise _invalid("start/end", f"window too long with hazards on: it covers {hz_span:g} h of lunar local "
                       f"time{' (local search: 3 windows)' if local_search else ''}; the limit is "
                       f"{HAZARD_MAX_SPAN_H:g} h: shorten the window or set hazards_enabled=false",
                       error="limit_exceeded")


def _check_deep_size(n_cells: int, n_starts: int, span_h: float, step_m: int, mode: str, hazards_enabled: bool,
                     lon_width_deg: float, start_n: int | None = None) -> None:
    """422 naming the field when a /deep-search request is above the measured limits (D-20261118-pj-cd33)."""
    if DEEP_MAX_CELLS is not None and n_cells > DEEP_MAX_CELLS:
        raise _invalid("lat_min/lat_max/lon_min/lon_max", f"region too large: {n_cells} cap cells; the limit is "
                       f"{DEEP_MAX_CELLS} cells (about {DEEP_MAX_CELLS} km2)", error="limit_exceeded")
    evals = n_cells * n_starts
    if mode == "total_coverage" and DEEP_MAX_EVALUATIONS is not None and evals > DEEP_MAX_EVALUATIONS:
        raise _invalid("start/end", f"search too large for total_coverage: {n_cells} cells x {n_starts} window "
                       f"starts = {evals} evaluations; the limit is {DEEP_MAX_EVALUATIONS}: shorten start/end, "
                       f"shrink the region or use mode optimized", error="limit_exceeded")
    if mode != "total_coverage" and start_n is not None and DEEP_MAX_EVALUATIONS is not None \
            and start_n > DEEP_MAX_EVALUATIONS:
        # optimized evaluates from its start points only (default ~60): measured cheap at any tested size
        raise _invalid("start_n", f"start_n {start_n} is above the limit of {DEEP_MAX_EVALUATIONS} evaluations",
                       error="limit_exceeded")
    sky = n_cells * (int(span_h * 60 // step_m) + 1)
    if mode == "total_coverage" and DEEP_MAX_SKY_SAMPLES is not None and sky > DEEP_MAX_SKY_SAMPLES:
        raise _invalid("step_min", f"search too large: {n_cells} cells x {int(span_h * 60 // step_m) + 1} samples "
                       f"(start to end at step_min {step_m}) = {sky}; the limit is {DEEP_MAX_SKY_SAMPLES}: use a "
                       f"larger step_min, shorten start/end or shrink the region", error="limit_exceeded")
    hz_span = _hazard_span_h(span_h, lon_width_deg)
    if hazards_enabled and HAZARD_MAX_SPAN_H is not None and hz_span > HAZARD_MAX_SPAN_H:
        raise _invalid("start/end", f"search too long with hazards on: start to end plus the region's longitude "
                       f"width ({lon_width_deg:g} deg) cover {hz_span:g} h of lunar local time; the limit is "
                       f"{HAZARD_MAX_SPAN_H:g} h: shorten start/end, narrow the longitudes or set "
                       f"hazards_enabled=false", error="limit_exceeded")


def _check_step_min(step_min: int) -> None:
    # Windows are whole hours sliced as hours*60//step_min samples (planner_payload, deep search):
    # only a step that divides 60 lands every window edge on a sample.
    if 60 % step_min:
        raise ValueError(
            f"step_min must divide 60 evenly (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30 or 60), got {step_min}"
        )


def _check_template(template_id: str | None) -> dict | None:
    from moonpark.planner_templates import TEMPLATES, template_needs

    if template_id and template_id not in TEMPLATES:
        raise _invalid("template_id", f"unknown template_id {template_id!r}; see /mission-templates")
    return template_needs(template_id)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/progress")
def progress() -> dict[str, Any]:
    """Data-store download in flight (file, bytes, totals); ``active`` false when idle."""
    from moonpark.horizon.remote import download_progress

    return download_progress()


@app.get("/store-status")
def store_status() -> dict[str, Any]:
    """Live data-store version, the minimum app version it needs, and this engine's version (D-20261118-pj-62d3)."""
    from moonpark.horizon import remote
    from moonpark.planner_payload import engine_version

    return {**remote.store_status(), "engine_version": engine_version()}


def _check_coverage(field: str, lat: float) -> None:
    from moonpark.planner_payload import COVERAGE_MAX_LAT_DEG

    # D-20261118-pj-cd33 coverage_limit: the data covers the south polar cap only.
    if lat > COVERAGE_MAX_LAT_DEG:
        raise _invalid(
            field,
            f"{field} {lat} is outside data coverage: only the south polar cap (lat <= {COVERAGE_MAX_LAT_DEG}) is covered",
            error="out_of_coverage",
        )


@app.post("/region-map")
def region_map(body: RegionMapBody) -> dict[str, Any]:
    from moonpark.region_map import build_region_map

    return build_region_map(body.rows, search_partial=body.search_partial, best=body.best)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/mission-templates")
def mission_templates() -> dict:
    from moonpark.planner_templates import list_templates

    return {"templates": list_templates()}


@app.get("/terrain")
def terrain(
    lat: float = Query(..., ge=-90, le=90, allow_inf_nan=False),
    lon: float = Query(..., allow_inf_nan=False),
) -> dict:
    """Ring-mesh relief from our own DEMs for the first-person view; 503 when no DEM covers the site."""
    from moonpark.terrain import TerrainUnavailable, rings_for

    try:
        return rings_for(lat, lon)
    except TerrainUnavailable as e:
        raise HTTPException(status_code=503, detail={"error": "terrain_unavailable", "message": str(e)})


def _request_needs(
    template_id: str | None,
    *,
    max_night_h, max_no_earth_h, require_both, min_continuous_lit_h, sun_lit_percent, earth_lit_percent,
    bridge_h, min_total_lit_h, battery_wh, array_w, dark_w, endurance_h, lit_w, panel, panel_az_deg,
    reserve_pct, charge_eff, max_temperature_k, min_temperature_k, min_soil_resistance,
) -> dict[str, Any]:
    """Effective requirements of a request, shared by /site and /deep-search (D-20261118-pj-75f1, D-70ec)."""
    from moonpark.planner_payload import resolve_needs
    from moonpark.planner_templates import HAZARD_LIMITS_DEFAULT

    explicit: dict[str, Any] = {
        "max_night_h": max_night_h,
        "max_no_earth_h": max_no_earth_h,
        "require_both": require_both,
        "min_continuous_lit_h": min_continuous_lit_h,
        "sun_lit_percent": sun_lit_percent,
        "earth_lit_percent": earth_lit_percent,
        "bridge_h": bridge_h,
    }
    needs_extra: dict[str, Any] = {}
    if min_total_lit_h > 0:
        needs_extra["min_total_lit_h"] = float(min_total_lit_h)
    energy_in = {
        "battery_wh": battery_wh, "array_w": array_w, "dark_w": dark_w, "endurance_h": endurance_h,
        "lit_w": lit_w, "panel": panel, "panel_az_deg": panel_az_deg, "reserve_pct": reserve_pct,
        "charge_eff": charge_eff,
    }
    if any(v is not None for v in energy_in.values()):
        if panel is not None and panel not in ("horizontal", "fixed_vertical", "tracking_vertical"):
            raise HTTPException(status_code=422, detail="panel must be horizontal, fixed_vertical or tracking_vertical")
        from moonpark.energy import params_from_needs

        needs_extra.update({k: v for k, v in energy_in.items() if v is not None})
        if params_from_needs(needs_extra) is None:
            raise HTTPException(
                status_code=422,
                detail="energy mode needs battery_wh, array_w and dark_w (or endurance_h)",
            )

    # per D-20261117-pj-0c5e: explicit hazard limit > template > global default; empty = off
    for key, raw in (
        ("max_temperature_k", max_temperature_k),
        ("min_temperature_k", min_temperature_k),
        ("min_soil_resistance", min_soil_resistance),
    ):
        if raw is None:
            continue
        txt = str(raw).strip().lower()
        try:
            val = None if txt in ("", "none") else float(txt)
        except ValueError:
            raise _invalid(key, f"{key} must be a number or empty") from None
        if val is not None and not math.isfinite(val):
            raise _invalid(key, f"{key} must be a finite number or empty, got {raw!r}")
        if key == "min_soil_resistance" and val is not None and val < 0:
            raise _invalid(key, f"min_soil_resistance must be >= 0, got {val}")
        explicit[key] = val
    needs = {**resolve_needs(template_id, explicit), **needs_extra}
    t_min = needs.get("min_temperature_k", HAZARD_LIMITS_DEFAULT["min_temperature_k"])
    t_max = needs.get("max_temperature_k", HAZARD_LIMITS_DEFAULT["max_temperature_k"])
    if t_min is not None and t_max is not None and float(t_min) > float(t_max):
        raise _invalid(
            "min_temperature_k",
            f"min_temperature_k ({t_min}) must not exceed max_temperature_k ({t_max})",
        )

    return needs


@app.get("/site")
def site(
    mock: int = Query(0, description="1 = CI mock only"),
    lat: float | None = Query(None, ge=-90, le=90, allow_inf_nan=False),
    lon: float | None = Query(None, allow_inf_nan=False),
    start: str | None = Query(None),
    end: str | None = Query(None),
    step_h: int = Query(1, ge=1, le=24),
    step_min: int | None = Query(None, ge=1, le=1440, description="sample step in minutes; wins over step_h"),
    template_id: str | None = Query(None),
    max_night_h: int | None = Query(None, ge=0),
    max_no_earth_h: int | None = Query(None, ge=0),
    min_continuous_lit_h: int | None = Query(None, ge=0),
    min_total_lit_h: float = Query(0, ge=0, allow_inf_nan=False, description="minimum total hours of light in the window; 0 = no requirement"),
    require_both: bool | None = Query(None),
    battery_wh: float | None = Query(None, gt=0, allow_inf_nan=False, description="energy mode: usable battery capacity (Wh)"),
    array_w: float | None = Query(None, ge=0, allow_inf_nan=False, description="energy mode: array power at normal incidence (W)"),
    dark_w: float | None = Query(None, ge=0, allow_inf_nan=False, description="energy mode: load in darkness (W)"),
    endurance_h: float | None = Query(None, gt=0, allow_inf_nan=False, description="energy mode: darkness endurance (h); dark_w = battery_wh / endurance_h"),
    lit_w: float | None = Query(None, ge=0, allow_inf_nan=False, description="load when lit (W); default = dark_w"),
    panel: str | None = Query(None, description="horizontal | fixed_vertical | tracking_vertical"),
    panel_az_deg: float | None = Query(None, ge=0, lt=360, description="fixed_vertical: geographic azimuth from north"),
    reserve_pct: float | None = Query(None, ge=0, lt=100, description="minimum battery reserve, % of capacity (default 10)"),
    charge_eff: float | None = Query(None, gt=0, le=1),
    # Absent = template value, else the global default; a value sent always wins (D-20261118-pj-70ec).
    sun_lit_percent: float | None = Query(None, ge=0, le=100),
    earth_lit_percent: float | None = Query(None, ge=0, le=100),
    bridge_h: int | None = Query(None, ge=0, le=48),
    hazards_enabled: bool = Query(True),
    local_search: int = Query(0, description="1 = include local_search block"),
    max_temperature_k: str | None = Query(None, description="K; empty/none = no limit; absent = template/default"),
    min_temperature_k: str | None = Query(None, description="K; empty/none = no limit; absent = template/default"),
    min_soil_resistance: str | None = Query(None, description="empty/none = no limit; absent = template/default"),
) -> dict:
    # per D-20261114-pj-8588: mock only when mock=1
    if mock == 1:
        return _mock_site_payload(local_search=local_search == 1)

    from moonpark.planner_payload import build_planner_payload, kernels_available, parse_time_window
    from moonpark.planner_templates import DEMO_SITE01
    from moonpark.providers import Site

    # Structural validation first: no kernel/DEM access until the request is known to be well formed.
    _check_template(template_id)
    lat_v = float(lat if lat is not None else DEMO_SITE01["lat_deg"])
    lon_v = float(lon if lon is not None else DEMO_SITE01["lon_deg"])
    _check_coverage("lat", lat_v)
    if local_search == 1 and step_h != 1:  # D-20261118-pj-cd33 local_search_step: 1 h only
        raise _invalid("step_h", f"local search runs on a 1 h step only: step_h must be 1, got {step_h}")
    step_m = int(step_min) if step_min is not None else int(step_h) * 60
    try:
        if step_min is not None:
            _check_step_min(step_m)
    except ValueError as e:
        raise _invalid("step_min", str(e)) from None
    try:
        start_v, end_v = _utc_window(start or "2027-01-01T00:00:00Z", end or "2027-01-01T23:00:00Z")
    except ValueError as e:
        raise _invalid("start/end", str(e)) from None
    _check_site_size(_span_h(start_v, end_v), step_m, bool(hazards_enabled), local_search == 1)
    try:
        times = parse_time_window(start_v, end_v, step_min=step_m)
    except ValueError as e:
        raise _invalid("start/end", str(e)) from None

    needs = _request_needs(
        template_id, max_night_h=max_night_h, max_no_earth_h=max_no_earth_h, require_both=require_both,
        min_continuous_lit_h=min_continuous_lit_h, sun_lit_percent=sun_lit_percent,
        earth_lit_percent=earth_lit_percent, bridge_h=bridge_h, min_total_lit_h=min_total_lit_h,
        battery_wh=battery_wh, array_w=array_w, dark_w=dark_w, endurance_h=endurance_h, lit_w=lit_w,
        panel=panel, panel_az_deg=panel_az_deg, reserve_pct=reserve_pct, charge_eff=charge_eff,
        max_temperature_k=max_temperature_k, min_temperature_k=min_temperature_k,
        min_soil_resistance=min_soil_resistance,
    )

    if not kernels_available():
        raise HTTPException(
            status_code=503,
            detail={"error": "kernels_missing", "message": "SPICE kernels not on disk; use mock=1 in CI."},
        )
    site_obj = Site(lat_deg=lat_v, lon_deg=lon_v, observer_height_m=2.0)
    try:
        return build_planner_payload(
            site_obj,
            times,
            needs=needs,
            sun_lit_percent=needs["sun_lit_percent"],
            earth_lit_percent=needs["earth_lit_percent"],
            bridge_h=needs["bridge_h"],
            hazards_enabled=hazards_enabled,
            local_search=local_search == 1,
            step_min=step_m,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "dem_missing", "message": str(e)},
        ) from e
    except Exception as e:  # input is validated above, so anything left is an internal fault
        raise HTTPException(
            status_code=500,
            detail={"error": "planner_failed", "message": str(e)},
        ) from e


class DeepSearchBody(BaseModel):
    """POST /deep-search body. # per D-60a3 D-c159 D-54f0; requirement fields = /site names and defaults (D-75f1)"""

    mode: str = Field(default="optimized")
    lat_min: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lat_max: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon_min: float = Field(allow_inf_nan=False)
    lon_max: float = Field(allow_inf_nan=False)
    start: str
    end: str
    window_hours: int = Field(default=24, ge=1, le=168)
    template_id: str | None = None
    start_n: int | None = None
    format: str = Field(default="json", description="json | csv")
    mock: bool = Field(default=False, description="Synthetic rows for UI checks; needs no kernels or cap index")
    step_min: int = Field(default=60, ge=1, le=60, description="sample step in minutes; 60 = coarse default, 10 = fine (D-91c6)")
    job_id: str | None = Field(default=None, description="id for POST /deep-search/stop")
    resume: dict[str, Any] | None = Field(default=None, description="checkpoint of a stopped run (D-20261118-pj-1454)")
    # The user's requirements: same names, defaults and bounds as GET /site (D-20261118-pj-75f1).
    max_night_h: int | None = Field(default=None, ge=0)
    max_no_earth_h: int | None = Field(default=None, ge=0)
    min_continuous_lit_h: int | None = Field(default=None, ge=0)
    min_total_lit_h: float = Field(default=0, ge=0, allow_inf_nan=False)
    require_both: bool | None = None
    battery_wh: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    array_w: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    dark_w: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    endurance_h: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    lit_w: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    panel: str | None = None
    panel_az_deg: float | None = Field(default=None, ge=0, lt=360)
    reserve_pct: float | None = Field(default=None, ge=0, lt=100)
    charge_eff: float | None = Field(default=None, gt=0, le=1)
    sun_lit_percent: float | None = Field(default=None, ge=0, le=100)
    earth_lit_percent: float | None = Field(default=None, ge=0, le=100)
    bridge_h: int | None = Field(default=None, ge=0, le=48)
    hazards_enabled: bool = True
    max_temperature_k: float | str | None = Field(default=None, description="K; empty/none = no limit; absent = template/default")
    min_temperature_k: float | str | None = Field(default=None, description="K; empty/none = no limit; absent = template/default")
    min_soil_resistance: float | str | None = Field(default=None, description="empty/none = no limit; absent = template/default")


class DeepSearchStopBody(BaseModel):
    job_id: str


_DEEP_JOBS: dict[str, threading.Event] = {}  # job_id -> stop flag of a running /deep-search (D-1454)
_DEEP_JOBS_LOCK = threading.Lock()


def _evaluation_needs(needs: dict, step_min: int, hazards_enabled: bool):
    """(score needs, energy params, payload needs) exactly as build_planner_payload derives them for /site."""
    from moonpark.energy import params_from_needs
    from moonpark.planner_templates import HAZARD_LIMITS_DEFAULT

    energy = params_from_needs(needs)
    score_needs: dict[str, Any] = {
        "max_night_h": int(needs.get("max_night_h", 0)),
        "max_no_earth_h": int(needs["max_no_earth_h"]),
        "require_both": bool(needs.get("require_both", False)),
        "min_continuous_lit_h": int(needs.get("min_continuous_lit_h", 0)),
        "min_total_lit_h": float(needs.get("min_total_lit_h", 0) or 0),
    }
    if energy is not None:
        score_needs["energy_reserve_frac"] = energy.reserve_frac
    if hazards_enabled:
        for key, default in HAZARD_LIMITS_DEFAULT.items():
            limit = needs[key] if key in needs else default
            if limit is not None:
                score_needs[key] = float(limit)
    sun_pct, earth_pct = float(needs["sun_lit_percent"]), float(needs["earth_lit_percent"])
    payload_needs = {
        **score_needs,
        "sun_lit_percent": sun_pct,
        "earth_lit_percent": earth_pct,
        "sun_lit_threshold": max(0.0, min(100.0, sun_pct)) / 100.0,
        "earth_lit_threshold": max(0.0, min(100.0, earth_pct)) / 100.0,
        "bridge_h": int(needs["bridge_h"]),
        "step_min": int(step_min),
        "energy_mode": energy is not None,
        **(
            {
                "battery_wh": energy.capacity_wh, "array_w": energy.array_w, "dark_w": energy.dark_w,
                "lit_w": energy.lit_w, "panel": energy.panel, "panel_az_deg": energy.panel_az_deg,
                "reserve_pct": energy.reserve_frac * 100.0, "charge_eff": energy.charge_eff,
            }
            if energy is not None
            else {}
        ),
        "template_id": needs.get("template_id"),
        "not_evaluated": [],
    }
    return score_needs, energy, payload_needs


def _requested(key: str, value: Any) -> bool:
    # A requirement is requested when it constrains anything: None/False and a minimum <= 0 mean "no requirement".
    # Same rule as hazard_status / hazard_gap_star (moonpark.score.limit_requested).
    from moonpark.score import limit_requested

    return limit_requested(key, value)


def _iso_row(row: dict | None) -> dict | None:
    if row is None:
        return None
    out = dict(row)
    import numpy as np

    out["window_start"] = str(np.datetime64(row["window_start"], "s")) + "Z"
    return out


@app.post("/deep-search/stop")
def deep_search_stop(body: DeepSearchStopBody) -> dict[str, bool]:
    """Stop a running /deep-search; it returns state 'stopped' and a checkpoint to resume (D-20261118-pj-1454)."""
    with _DEEP_JOBS_LOCK:
        ev = _DEEP_JOBS.get(body.job_id)
    if ev is None:
        return {"stopped": False}
    ev.set()
    return {"stopped": True}


@app.post("/deep-search")
def deep_search_endpoint(body: DeepSearchBody):
    # per D-60a3 dedicated endpoint; D-54f0 modes; D-c159 rect snap; D-75f1 the user's requirements; D-1454 stop/resume
    # Structural validation first: no kernel/cap access until the request is known to be well formed.
    for lo, hi in (("lat_min", "lat_max"), ("lon_min", "lon_max")):
        if getattr(body, lo) > getattr(body, hi):
            raise _invalid(lo, f"{lo} must not exceed {hi}")
    _check_coverage("lat_max", body.lat_max)  # lat_min <= lat_max, so this bounds the whole rectangle
    try:
        _check_step_min(int(body.step_min))
    except ValueError as e:
        raise _invalid("step_min", str(e)) from None
    _check_template(body.template_id)
    try:
        start_v, end_v = _utc_window(body.start, body.end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "bad_time", "message": str(e)}) from e

    from moonpark.search import deep as deep_mod

    step_m = int(body.step_min)
    needs = _request_needs(
        body.template_id, **{k: getattr(body, k) for k in (
            "max_night_h", "max_no_earth_h", "require_both", "min_continuous_lit_h", "sun_lit_percent",
            "earth_lit_percent", "bridge_h", "min_total_lit_h", "battery_wh", "array_w", "dark_w", "endurance_h",
            "lit_w", "panel", "panel_az_deg", "reserve_pct", "charge_eff", "max_temperature_k",
            "min_temperature_k", "min_soil_resistance")},
    )
    hz_on = bool(body.hazards_enabled)
    _score_all, _energy_all, requirements = _evaluation_needs(needs, step_m, hz_on)
    # D-75f1: a requested requirement no search can evaluate is warned once and left out of the evaluation.
    skipped = sorted(
        k for k in deep_mod.UNEVALUABLE_REQUIREMENTS
        if _requested(k, requirements.get(k, needs.get(k)))
    )
    warnings: list[dict] = []
    if skipped:
        requirements["not_evaluated"] = skipped
        warnings.append({
            "code": "requirement_not_evaluated",
            "fields": skipped,
            "message": f"Could not measure {', '.join(skipped)} in this search; the estimate was made as if "
            "these requirements were not set.",
        })
    eval_needs = {k: v for k, v in needs.items() if k not in skipped}
    score_needs, energy, _ = _evaluation_needs(eval_needs, step_m, hz_on)
    for k in skipped:  # hazard limits re-enter from their global default unless removed here
        score_needs.pop(k, None)

    if body.mock:
        from moonpark.search.mock_deep import mock_deep_search

        out = mock_deep_search(
            body.mode,
            body.lat_min,
            body.lat_max,
            body.lon_min,
            body.lon_max,
            start_v,
            body.window_hours,
        )
        return {**out, "requirements": requirements, "warnings": warnings, "dropped_cells": 0,
                "state": "complete", "checkpoint": None}
    from moonpark.ephemeris import SpiceEphemeris
    from moonpark.horizon.cap_index import (
        cap_index_available,
        mask_from_cap_tile,
        sites_in_latlon_rect,
    )
    from moonpark.planner_payload import hazard_status, kernels_available, parse_time_window
    from moonpark.search.deep import DEFAULT_LEADERBOARD_N, DEFAULT_TMAX_S
    from moonpark.visibility import series as vis_series

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

    cells = sites_in_latlon_rect(body.lat_min, body.lat_max, body.lon_min, body.lon_max)
    if not cells:
        raise HTTPException(
            status_code=400,
            detail={"error": "empty_rect", "message": "No cap cells in rectangle"},
        )

    try:
        span = parse_time_window(start_v, end_v, step_h=1)
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
    _check_deep_size(len(cells), n_starts, _span_h(start_v, end_v), step_m, body.mode, hz_on,
                     body.lon_max - body.lon_min, body.start_n)
    starts = span[:n_starts]
    fine_span = span if step_m == 60 else parse_time_window(start_v, end_v, step_min=step_m)
    sites = [c[0] for c in cells]
    site_xy = [(c[1], c[2]) for c in cells]
    index_of = {(s.lat_deg, s.lon_deg): i for i, s in enumerate(sites)}

    eph = SpiceEphemeris()
    sun_thr, earth_thr = requirements["sun_lit_threshold"], requirements["earth_lit_threshold"]
    bridge = 0 if energy else int(requirements["bridge_h"])  # bridge_h is the no-battery-data fallback only
    if hz_on:
        from moonpark.hazards import default_moon_hazards  # looked up per request

        hazard_provider = default_moon_hazards()
    sky_by_site: dict[int, list] = {}

    def evaluate(candidate, start, hours: int) -> dict | None:
        # Same computation as /site (build_planner_payload) on the cell's 1 km cap mask. The engine caches each
        # (cell, window start), so hazards run once per cell and window.
        idx = index_of.get((candidate.lat_deg, candidate.lon_deg))
        if idx is None:
            raise ValueError("site not in rect cells")
        _site, _x, _y, tx, ty, row = cells[idx]
        horizon = mask_from_cap_tile(tx, ty, row)
        if idx not in sky_by_site:
            sky_by_site[idx] = eph.sky(candidate, fine_span)
        i0 = int((np.datetime64(start, "s") - np.datetime64(fine_span[0], "s")) / np.timedelta64(step_m, "m"))
        n = int(hours) * 60 // step_m + 1
        vis = vis_series(
            sky_by_site[idx][i0 : i0 + n],
            horizon,
            sun_threshold=sun_thr,
            earth_threshold=earth_thr,
            bridge_h=bridge,
            step_min=step_m,
            energy=energy,
        )
        vis = {k: (np.asarray(v, dtype=float).tolist() if k in ("sun_fraction", "earth_fraction", "soc") else v)
               for k, v in vis.items()}
        hz: dict = {}
        if hz_on:
            hz = hazard_provider.hazards(candidate, fine_span[i0 : i0 + n])
            if hazard_status(True, hz, score_needs)[1]:
                return None  # D-75f1: the cell lacks hazard data this search needs -> dropped and counted
        return {"series": vis, "hazards": hz}

    job_id = body.job_id
    stop_ev = threading.Event()
    if job_id:
        with _DEEP_JOBS_LOCK:
            if job_id in _DEEP_JOBS:
                raise _invalid("job_id", f"job_id {job_id!r} is already running", status=409, error="job_running")
            _DEEP_JOBS[job_id] = stop_ev
    try:
        result = deep_mod.deep_search(
            sites,
            starts,
            wh,
            score_needs,
            evaluate=evaluate,
            mode=body.mode,
            start_n=body.start_n,
            tmax_s=DEFAULT_TMAX_S,  # a target that sizes the optimized start count, never a stop (D-1454)
            leaderboard_n=DEFAULT_LEADERBOARD_N,
            site_xy=site_xy,
            should_stop=stop_ev.is_set,
            resume=body.resume,
            # The resume fingerprint covers the whole request, not only the score needs (reviewer fix).
            fingerprint_extra={
                "requirements": requirements,  # thresholds, bridge_h, step_min, energy, hazard limits
                "hazards_enabled": hz_on,
                "rect": [body.lat_min, body.lat_max, body.lon_min, body.lon_max],
                "mode": body.mode,
                "start": start_v,
                "end": end_v,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "deep_failed", "message": str(e)}) from e
    finally:
        if job_id:
            with _DEEP_JOBS_LOCK:
                _DEEP_JOBS.pop(job_id, None)

    dropped = int(result.get("dropped_cells") or 0)
    warnings = list(warnings) + list(result.get("warnings") or [])
    if dropped:
        warnings.append({
            "code": "cells_dropped_hazard_data",
            "count": dropped,
            "message": f"{dropped} cell(s) dropped: the hazard data this search needs is not available there.",
        })
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
        "requirements": requirements,
        "warnings": warnings,
        "dropped_cells": dropped,
        "state": result.get("state", "complete"),
        "checkpoint": result.get("checkpoint"),
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

