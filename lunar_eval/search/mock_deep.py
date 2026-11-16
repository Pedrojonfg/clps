"""Synthetic deep-search results for UI checks (no SPICE kernels / cap index needed).

Same response shape as POST /deep-search, but every number is made up: smooth
hotspot fields over the polar cap plus noise. Deterministic per (mode, rect).
Never a scientific result; callers must flag it as mock.
"""

from __future__ import annotations

import math
import random
import time
from typing import Any

from lunar_eval.horizon import polar_stereo_xy
from lunar_eval.horizon.mask import R_M

CAP_LAT_MAX = -80.0  # the real cap index stops here; "whole Moon" in this product = whole cap
GRID_KM = {"total_coverage": 5.0, "optimized": 5.0}
OPTIMIZED_KEEP = 0.04  # partial search evaluates a clustered few %, like hill-climb starts
_HOTSPOTS = 14


def _latlon(x_m: float, y_m: float) -> tuple[float, float]:
    rho = math.hypot(x_m, y_m)
    lat = math.degrees(2.0 * math.atan(rho / (2.0 * R_M))) - 90.0
    return lat, math.degrees(math.atan2(x_m, y_m)) % 360.0


def mock_deep_search(
    mode: str,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    window_start: str,
    window_hours: int,
    *,
    seed: int = 20261116,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    rng = random.Random(f"{seed}:{mode}")
    lo_lat, hi_lat = sorted((lat_min, lat_max))
    lo_lon, hi_lon = sorted((lon_min, lon_max))

    # Hotspots always come from the same stream so both modes agree on where the good ground is.
    hs_rng = random.Random(seed)
    hotspots = []
    for _ in range(_HOTSPOTS):
        r = 30_000.0 + 280_000.0 * math.sqrt(hs_rng.random())
        a = hs_rng.uniform(0, 2 * math.pi)
        hotspots.append((r * math.sin(a), r * math.cos(a), hs_rng.uniform(8, 35) * 1000.0, hs_rng.uniform(0.7, 1.38)))

    def field(x: float, y: float) -> float:
        return max(h * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * s * s)) for hx, hy, s, h in hotspots)

    step = GRID_KM[mode if mode in GRID_KM else "optimized"] * 1000.0
    half = 2.0 * R_M * math.tan(math.radians(90.0 + max(hi_lat, -90.0)) / 2.0) + step
    n = int(half // step)
    rows: list[dict[str, Any]] = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i * step, j * step
            lat, lon = _latlon(x, y)
            if not (lo_lat <= lat <= hi_lat and lo_lon <= lon <= hi_lon):
                continue
            if mode != "total_coverage" and rng.random() > OPTIMIZED_KEEP:
                continue
            base = field(x, y) + rng.gauss(0, 0.04)
            feasible = base > 0.2
            score = round(max(0.0, min(1.4, base)), 4) if feasible else 0.0
            rows.append(
                {
                    "site": {"lat_deg": round(lat, 5), "lon_deg": round(lon, 5)},
                    "window_start": window_start,
                    "window_hours": window_hours,
                    "feasible": feasible,
                    "score": score,
                    "companion_score": round(max(0.0, base), 4),
                    "hazard_gap_star": False,
                }
            )

    best = max(rows, key=lambda r: (r["feasible"], r["score"]), default=None)
    board = sorted(rows, key=lambda r: (r["feasible"], r["score"]), reverse=True)[:20]
    return {
        "mode": mode,
        "claim": "grid_optimum" if mode == "total_coverage" else "best_seen",
        "best": best,
        "leaderboard": board,
        "export_rows": rows,
        "rows_evaluated": len(rows),
        "runtime_s": round(time.perf_counter() - t0, 3),
        "eta_s": 0.0,
        "n_starts": 1,
        "n_sites": len(rows),
        "n_window_starts": 1,
        "provisional": True,
        "data_source": "mock",
    }
