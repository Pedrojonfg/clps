"""Build /site JSON from planner inputs. # per D-20261114-pj-aa58 D-8588 D-9e53"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from lunar_eval.horizon.mask_store import mask_for_site
from lunar_eval.providers import Site, SkySample


def parse_time_window(start_iso: str, end_iso: str, *, step_h: int = 1) -> np.ndarray:
    start = np.datetime64(start_iso.replace("Z", "").replace(" ", "T"), "s")
    end = np.datetime64(end_iso.replace("Z", "").replace(" ", "T"), "s")
    if end < start:
        raise ValueError("end before start")
    step = max(int(step_h), 1)
    n = int((end - start) / np.timedelta64(step, "h")) + 1
    if n > 744:
        raise ValueError("window too long (max 744 hourly steps)")
    return start + (np.arange(n) * step).astype("timedelta64[h]")


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
    for key in ("sun_fraction", "earth_fraction"):
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
) -> dict:
    from lunar_eval.ephemeris import SpiceEphemeris
    from lunar_eval.hazards import ConstantHazards, MoonHazards
    from lunar_eval.score import score
    from lunar_eval.visibility import series

    sun_thr = max(0.0, min(100.0, float(sun_lit_percent))) / 100.0
    earth_thr = max(0.0, min(100.0, float(earth_lit_percent))) / 100.0

    horizon = mask_for_site(site)
    sky_samples = SpiceEphemeris().sky(site, times)
    vis = series(
        sky_samples,
        horizon,
        sun_threshold=sun_thr,
        earth_threshold=earth_thr,
        bridge_h=int(bridge_h),
    )

    hazard_provider = MoonHazards() if hazards_enabled else ConstantHazards()
    raw_hz = hazard_provider.hazards(site, times)
    hazards_payload = raw_hz if hazards_enabled else {}

    score_needs = {
        "max_night_h": int(needs["max_night_h"]),
        "max_no_earth_h": int(needs["max_no_earth_h"]),
        "require_both": bool(needs.get("require_both", False)),
    }
    if hazards_enabled and raw_hz.get("aggregate"):
        agg = raw_hz["aggregate"]
        if agg.get("temperature_k") is not None:
            score_needs.setdefault("max_temperature_k", 320.0)
        if agg.get("soil_resistance") is not None:
            score_needs.setdefault("min_soil_resistance", 0.0)

    scored = score(_series_json(vis), hazards_payload, score_needs)
    if hazards_enabled:
        scored["provenance"]["hazards"] = "moon_layer_b"
    else:
        scored["provenance"]["hazards"] = "disabled"

    return {
        "data_source": "real",
        "mask": {
            "elevation_deg": np.asarray(horizon.elevation_deg, dtype=float).tolist(),
            "schedule_version": horizon.schedule_version,
            "lat": site.lat_deg,
            "lon": site.lon_deg,
            "cached": True,
        },
        "sky": [_sky_row(s) for s in sky_samples],
        "series": _series_json(vis),
        "score": scored,
        "hazards_enabled": hazards_enabled,
        "needs": {
            **score_needs,
            "sun_lit_percent": float(sun_lit_percent),
            "earth_lit_percent": float(earth_lit_percent),
            "sun_lit_threshold": sun_thr,
            "earth_lit_threshold": earth_thr,
            "bridge_h": int(bridge_h),
            "template_id": needs.get("template_id"),
        },
    }


def kernels_available() -> bool:
    return (Path(__file__).resolve().parents[1] / "data" / "kernels" / "de440s.bsp").is_file()