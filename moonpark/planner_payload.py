"""Build /site JSON from planner inputs. # per D-20261114-pj-aa58 D-8588 D-9e53 D-20261118-pj-b3dc D-1bc9 D-70ec"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from moonpark.horizon.mask_store import mask_for_site
from moonpark.providers import Site, SkySample


REPO = Path(__file__).resolve().parents[1]
ENGINE_VERSION_FALLBACK = "unknown"
COVERAGE_MAX_LAT_DEG = -60.0  # south polar cap only: data does not cover anything north of this (D-20261118-pj-cd33)

# Global defaults for the schedule requirements a request or template may omit (D-20261117-pj-0c5e).
SCHEDULE_DEFAULTS: dict[str, Any] = {
    "max_night_h": 72,
    "max_no_earth_h": 48,
    "require_both": False,
    "min_continuous_lit_h": 0,
    "sun_lit_percent": 0.0,
    "earth_lit_percent": 0.0,
    "bridge_h": 5,
}
# Hazard field reported missing (hazards "unavailable") -> the limits it would have checked.
_LIMITS_BY_HAZARD = {
    "temperature": ("max_temperature_k", "min_temperature_k"),
    "soil_resistance": ("min_soil_resistance",),
}


@lru_cache(maxsize=1)
def engine_version() -> str:
    """Engine version: pyproject.toml of the checkout, else installed package metadata, else a constant."""
    try:
        import tomllib

        return str(tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])
    except (OSError, KeyError, ValueError):
        pass
    try:
        from importlib.metadata import version

        return version("moonpark")
    except Exception:
        return ENGINE_VERSION_FALLBACK


def cached_data_version() -> str | None:
    """Data-store version this process already knows; never touches the network (None when off or not loaded)."""
    from moonpark.horizon import remote

    g = remote.group("data")  # None when the store is switched off; constructing it does no I/O
    return g.version if g is not None else None


def cached_cap_version() -> str | None:
    """Version of the 1 km cap mask store group when loaded (same rules as cached_data_version)."""
    from moonpark.horizon import remote

    g = remote.group("cap_1km")
    return g.version if g is not None else None


def resolve_needs(template_id: str | None, explicit: dict[str, Any]) -> dict[str, Any]:
    """Effective requirements: explicit request value > template value > global default (D-0c5e, D-70ec).

    ``explicit`` holds request values; None = not sent for schedule fields. A hazard-limit key present in
    ``explicit`` wins even when None (= limit switched off); absent, the template's limit (or nothing, so the
    global default applies later) is used. ``template_id`` survives only when every template field equals the
    template's value; otherwise the requirements are Custom (template_id None).
    """
    from moonpark.planner_templates import HAZARD_LIMIT_KEYS, template_needs

    tpl = template_needs(template_id) or {}
    out: dict[str, Any] = {}
    for key, default in SCHEDULE_DEFAULTS.items():
        v = explicit.get(key)
        out[key] = v if v is not None else tpl.get(key, default)
    for key in HAZARD_LIMIT_KEYS:
        if key in explicit:
            out[key] = explicit[key]
        elif key in tpl:
            out[key] = tpl[key]
    same = bool(tpl) and all(out.get(k) == v for k, v in tpl.items() if k != "template_id")
    out["template_id"] = template_id if same else None
    return out


def mask_provenance(req_lat: float, req_lon: float, mask_lat: float, mask_lon: float, source: str | None = None) -> dict:
    """Requested vs mask coordinates (D-1bc9). A mask computed at the requested point (own DEMs) sits within
    a metre of it; a farther one is the snapped 1 km cap cell."""
    from moonpark.horizon.mask import polar_stereo_xy

    x0, y0 = polar_stereo_xy(req_lat, req_lon)
    x1, y1 = polar_stereo_xy(mask_lat, mask_lon)
    d = float(math.hypot(x1 - x0, y1 - y0))
    return {
        "requested_lat": float(req_lat),
        "requested_lon": float(req_lon),
        "lat": float(mask_lat),
        "lon": float(mask_lon),
        "distance_m": round(d, 1),
        "source": source or ("own_dem" if d < 1.0 else "cap_cell"),
    }


def provenance(
    *, needs: dict, step_min: int, observer_height_m: float, mask: dict, fill: dict | None, hazards_enabled: bool
) -> dict:
    """How the result was computed (D-20261118-pj-1bc9 provenance_fields; D-d90c fill notice)."""
    from moonpark.score import FORMULA

    approximations = ["mask_interval_bounds_pessimistic", "score_sigmas_provisional"]
    if hazards_enabled:
        approximations.append("climatology_not_forecast")
    if mask.get("source") == "cap_cell":
        approximations.append("mask_from_nearest_1km_cap_cell")
    if fill and any(fill.values()):
        approximations.append("terrain_gaps_filled_unfavorable")
    return {
        "engine_version": engine_version(),
        "formula_version": FORMULA,
        "effective_needs": {k: v for k, v in needs.items() if k != "not_evaluated"},
        "step_min": int(step_min),
        "observer_height_m": float(observer_height_m),
        "data_version": cached_data_version(),
        "cap_version": cached_cap_version(),
        "approximations": approximations,
        "mask": mask,
        "fill": dict(fill) if fill is not None else None,
    }


def hazard_status(hazards_enabled: bool, raw_hz: dict, score_needs: dict) -> tuple[dict, list[str], list[dict]]:
    """(hazards_status, not_evaluated limits, warnings) per D-20261118-pj-b3dc / D-75f1: a limit whose data is
    missing stays in the requirements, is listed as not evaluated and gets no substitute value."""
    from moonpark.score import limit_requested

    if not hazards_enabled:
        return {"status": "disabled", "unavailable": {}}, [], []
    unavailable = dict(raw_hz.get("unavailable") or (raw_hz.get("aggregate") or {}).get("unavailable") or {})
    # A limit that constrains nothing (None, or a minimum <= 0) is not requested, so its missing data is no gap.
    not_evaluated = sorted(
        k for field in unavailable for k in _LIMITS_BY_HAZARD.get(field, ()) if limit_requested(k, score_needs.get(k))
    )
    warnings = []
    if not_evaluated:
        reasons = "; ".join(f"{f}: {r}" for f, r in unavailable.items())
        warnings.append(
            {
                "code": "hazard_data_unavailable",
                "fields": not_evaluated,
                "message": f"Not evaluated: {', '.join(not_evaluated)} ({reasons}). The result was computed as if "
                "these limits were not set; retry the data download.",
            }
        )
    return {"status": "partial" if unavailable else "ok", "unavailable": unavailable}, not_evaluated, warnings


# Outer bound on end - start, hours (2922 days, the longest window measured to work). The API checks its own
# narrower measured limits first (moonpark.api.app SITE_MAX_*, HAZARD_MAX_SPAN_H); see docs/limits.md
# (D-20261118-pj-cd33). None = no bound.
MAX_WINDOW_H: int | None = 70128


def parse_time_window(
    start_iso: str, end_iso: str, *, step_h: int = 1, step_min: int | None = None
) -> np.ndarray:
    """Inclusive sample times; `step_min` (e.g. 10) wins over `step_h`. # per D-20261117-pj-91c6"""
    start = np.datetime64(start_iso.replace("Z", "").replace(" ", "T"), "s")
    end = np.datetime64(end_iso.replace("Z", "").replace(" ", "T"), "s")
    if end < start:
        raise ValueError("end before start")
    step = max(int(step_min), 1) if step_min is not None else max(int(step_h), 1) * 60
    if MAX_WINDOW_H is not None and (end - start) / np.timedelta64(1, "h") > MAX_WINDOW_H:
        raise ValueError(f"window too long (max {MAX_WINDOW_H} h from start to end, {MAX_WINDOW_H + 1} hourly steps)")
    n = int((end - start) / np.timedelta64(step, "m")) + 1
    return start + (np.arange(n) * step).astype("timedelta64[m]")


def _iso_utc(t: np.datetime64) -> str:
    s = str(np.datetime64(t, "s"))
    if "T" not in s:
        s = s.replace(" ", "T")
    return s + ("Z" if not s.endswith("Z") else "")


def _sky_row(sample: SkySample) -> dict:
    return {
        "time_utc": _iso_utc(sample.time_utc),
        "sun_az_deg": round(sample.sun_az_deg, 2),
        "sun_el_deg": round(sample.sun_el_deg, 3),
        "earth_az_deg": round(sample.earth_az_deg, 2),
        "earth_el_deg": round(sample.earth_el_deg, 3),
    }


def _series_json(raw: dict) -> dict:
    out = dict(raw)
    for key in ("sun_fraction", "earth_fraction", "soc"):
        if key not in out:
            continue
        val = out[key]
        out[key] = np.asarray(val, dtype=float).tolist()
    return out


def build_planner_payload(
    site: Site,
    times: np.ndarray,
    *,
    needs: dict[str, Any],
    sun_lit_percent: float,
    earth_lit_percent: float,
    bridge_h: int,
    hazards_enabled: bool,
    local_search: bool = False,
    step_min: int = 60,
) -> dict:
    from moonpark.ephemeris import SpiceEphemeris
    from moonpark.hazards import ConstantHazards, default_moon_hazards
    from moonpark.planner_templates import HAZARD_LIMITS_DEFAULT
    from moonpark.score import score
    from moonpark.visibility import series

    sun_thr = max(0.0, min(100.0, float(sun_lit_percent))) / 100.0
    earth_thr = max(0.0, min(100.0, float(earth_lit_percent))) / 100.0

    horizon = mask_for_site(site)
    sky_samples = SpiceEphemeris().sky(site, times)
    from moonpark.energy import params_from_needs

    energy = params_from_needs(needs)  # tier 1 complete => energy mode (D-20261117-pj-7b2d)
    vis = series(
        sky_samples,
        horizon,
        sun_threshold=sun_thr,
        earth_threshold=earth_thr,
        bridge_h=0 if energy else int(bridge_h),  # bridge_h is the no-battery-data fallback only
        step_min=int(step_min),
        energy=energy,
    )

    hazard_provider = default_moon_hazards() if hazards_enabled else ConstantHazards()
    raw_hz = hazard_provider.hazards(site, times)
    hazards_payload = raw_hz if hazards_enabled else {}

    score_needs = {
        "max_night_h": int(needs.get("max_night_h", 0)),
        "max_no_earth_h": int(needs["max_no_earth_h"]),
        "require_both": bool(needs.get("require_both", False)),
        "min_continuous_lit_h": int(needs.get("min_continuous_lit_h", 0)),
        "min_total_lit_h": float(needs.get("min_total_lit_h", 0) or 0),
    }
    if energy is not None:
        score_needs["energy_reserve_frac"] = energy.reserve_frac
    if hazards_enabled:
        # Limits: explicit in `needs` (None = switched off), else the global default (D-20261117-pj-0c5e).
        # A limit stays in the requirements even when its data is missing (D-20261118-pj-b3dc): the missing
        # quantity is None, never a substitute, so score() leaves it out of layer 0 and the margins, flags
        # hazard_gap_star, and the payload lists the limit under needs.not_evaluated with a warning.
        for key, default in HAZARD_LIMITS_DEFAULT.items():
            limit = needs[key] if key in needs else default
            if limit is not None:
                score_needs[key] = float(limit)

    scored = score(_series_json(vis), hazards_payload, score_needs)
    if hazards_enabled:
        scored["provenance"]["hazards"] = "moon_layer_b"
    else:
        scored["provenance"]["hazards"] = "disabled"
    hz_status, not_evaluated, warnings = hazard_status(hazards_enabled, raw_hz, score_needs)

    payload: dict[str, Any] = {
        "data_source": "real",
        "mask": {
            "elevation_deg": np.asarray(horizon.elevation_deg, dtype=float).tolist(),
            # per D-20261116-pj-b43a: geographic_az = zero + sign * index_az
            "azimuth_zero_deg": 180.0,
            "azimuth_sign": -1,
            "schedule_version": horizon.schedule_version,
            "lat": site.lat_deg,
            "lon": site.lon_deg,
            "cached": True,
        },
        "sky": [_sky_row(s) for s in sky_samples],
        "series": _series_json(vis),
        "score": scored,
        "hazards_enabled": hazards_enabled,
        "hazards": hazards_payload,
        "needs": {
            **score_needs,
            "sun_lit_percent": float(sun_lit_percent),
            "earth_lit_percent": float(earth_lit_percent),
            "sun_lit_threshold": sun_thr,
            "earth_lit_threshold": earth_thr,
            "bridge_h": int(bridge_h),
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
            "not_evaluated": not_evaluated,
        },
        "hazards_status": hz_status,
        "warnings": warnings,
    }
    payload["provenance"] = provenance(
        needs=payload["needs"],
        step_min=step_min,
        observer_height_m=site.observer_height_m,
        mask=mask_provenance(site.lat_deg, site.lon_deg, horizon.lat, horizon.lon),
        fill=horizon.fill_stats,
        hazards_enabled=hazards_enabled,
    )

    if local_search:
        from moonpark.search.local import DEFAULT_RADIUS_KM, local_search as run_local_search

        # Elapsed time, not sample count: with step_min < 60 len(times)-1 is not hours.
        window_hours = max(int(round((np.datetime64(times[-1], "s") - np.datetime64(times[0], "s")) / np.timedelta64(1, "h"))), 0)
        anchor = np.datetime64(times[0], "s")
        neighbour_sites: list[Site] = []  # per D-ecc9: no 1 km grid in prod path

        def evaluate(candidate: Site, start, hours: int) -> dict:
            t0 = np.datetime64(start, "s")
            n = int(hours) + 1
            win_times = t0 + (np.arange(int(hours) * 60 // int(step_min) + 1) * np.timedelta64(int(step_min), "m"))
            sub = build_planner_payload(
                candidate,
                win_times,
                needs=needs,
                sun_lit_percent=sun_lit_percent,
                earth_lit_percent=earth_lit_percent,
                bridge_h=bridge_h,
                hazards_enabled=hazards_enabled,
                local_search=False,
                step_min=step_min,
            )
            if sub["needs"].get("not_evaluated"):
                return None  # a set limit has no data in this window: dropped and counted (D-75f1 / D-b3dc)
            hz = sub.get("hazards") or {}
            gap = bool(sub["score"].get("hazard_gap_star"))
            return {"series": sub["series"], "hazards": hz, "hazard_gap_star": gap}

        ls = run_local_search(
            site,
            anchor,
            window_hours,
            score_needs,
            evaluate=evaluate,
            neighbour_sites=neighbour_sites,
            radius_km=DEFAULT_RADIUS_KM,
        )

        def _row_json(row: dict | None) -> dict | None:
            if row is None:
                return None
            out = dict(row)
            out["window_start"] = _iso_utc(np.datetime64(row["window_start"], "s"))
            return out

        dropped = int(ls.get("dropped_windows") or 0)
        payload["local_search"] = {
            "pick": _row_json(ls["pick"]),
            "leaderboard": [_row_json(r) for r in ls["leaderboard"]],
            "dropped_windows": dropped,
        }
        if dropped:
            # The origin analysis above is never dropped (its own not-evaluated handling); only search rows are.
            payload["warnings"].append(
                {
                    "code": "windows_dropped_hazard_data",
                    "count": dropped,
                    "message": f"{dropped} window(s) dropped from the local search: the hazard data for a limit "
                    "you set is not available there.",
                }
            )

    return payload


def kernels_available() -> bool:
    from moonpark.horizon.remote import locate

    return locate("kernels/de440s.bsp") is not None