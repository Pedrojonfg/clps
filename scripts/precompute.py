#!/usr/bin/env python3
"""Overnight 1 km south-pole horizon-mask cap. # per D-f369 D-5994 P2

Stores float32[720] masks in 100 km tiles under data/masks/cap_1km/ plus a
parquet index. Resume-safe: completed tiles are skipped.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from moonpark.horizon import load_tif, mask, polar_stereo_xy  # noqa: E402
from moonpark.horizon.mask import R_M, SCHEDULE_VERSION  # noqa: E402
from moonpark.providers import Site  # noqa: E402

DEM = REPO / "data" / "dem"
OUT = REPO / "data" / "masks" / "cap_1km"
TILE_M = 100_000.0
NAZ = 720
OH = 2.0

G80 = None
G240 = None
PATH_20 = None


def latlon_from_xy(x_m: float, y_m: float) -> tuple[float, float]:
    rho = math.hypot(x_m, y_m)
    lat = 2.0 * math.degrees(math.atan(rho / (2.0 * R_M))) - 90.0
    lon = math.degrees(math.atan2(x_m, y_m)) % 360.0
    return lat, lon


def grid_points(spacing_m: float, lat_max: float = -80.0) -> list[tuple[float, float, float, float]]:
    """Return (lat, lon, x, y) on a polar-stereo grid with lat <= lat_max."""
    # rho at lat_max: rho = 2R tan((90+lat)/2)
    rho_max = 2.0 * R_M * math.tan(math.radians(90.0 + lat_max) / 2.0)
    n = int(math.ceil(rho_max / spacing_m))
    pts: list[tuple[float, float, float, float]] = []
    for iy in range(-n, n + 1):
        for ix in range(-n, n + 1):
            x = ix * spacing_m
            y = iy * spacing_m
            lat, lon = latlon_from_xy(x, y)
            if lat <= lat_max + 1e-9:
                pts.append((lat, lon, x, y))
    return pts


def tile_key(x_m: float, y_m: float) -> tuple[int, int]:
    return int(math.floor(x_m / TILE_M)), int(math.floor(y_m / TILE_M))


def _one_mask(args: tuple[float, float, float, float]) -> tuple[float, float, float, float, float, np.ndarray]:
    """Worker: parent must fork after loading G80/G240 (Linux COW)."""
    lat, lon, x, y = args
    assert G80 is not None and G240 is not None and PATH_20 is not None
    g20 = load_tif(PATH_20, x, y, 6_000.0)
    sched = [
        (0.0, 250.0, g20),
        (250.0, 1000.0, g20),
        (1000.0, 2000.0, g20.coarsen(2)),
        (2000.0, 5000.0, G80),
        (5000.0, 25000.0, G80),
        (25000.0, 250000.0, G240),
    ]
    site = Site(lat_deg=lat, lon_deg=lon, observer_height_m=OH)
    h = mask(site, schedule=sched)
    return lat, lon, x, y, float(h.h0_m), h.elevation_deg.astype(np.float32)


def write_tile(
    out_dir: Path,
    tx: int,
    ty: int,
    rows: list[tuple[float, float, float, float, float, np.ndarray]],
) -> Path:
    tile_dir = out_dir / "tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)
    elev = np.stack([r[5] for r in rows], axis=0)
    npy = tile_dir / f"t{tx}_{ty}.npy"
    np.save(npy, elev)
    meta = {
        "tile_x": tx,
        "tile_y": ty,
        "n": len(rows),
        "naz": NAZ,
        "observer_height_m": OH,
        "schedule_version": SCHEDULE_VERSION,
        "sites": [
            {"lat": r[0], "lon": r[1], "x_m": r[2], "y_m": r[3], "h0_m": r[4], "row": i}
            for i, r in enumerate(rows)
        ],
    }
    (tile_dir / f"t{tx}_{ty}.json").write_text(json.dumps(meta), encoding="utf-8")
    return npy


def rebuild_index(out_dir: Path) -> int:
    tile_dir = out_dir / "tiles"
    lats, lons, xs, ys, h0s, txs, tys, rows = [], [], [], [], [], [], [], []
    for meta_path in sorted(tile_dir.glob("t*_*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        tx, ty = meta["tile_x"], meta["tile_y"]
        for s in meta["sites"]:
            lats.append(s["lat"])
            lons.append(s["lon"])
            xs.append(s["x_m"])
            ys.append(s["y_m"])
            h0s.append(s["h0_m"])
            txs.append(tx)
            tys.append(ty)
            rows.append(s["row"])
    table = pa.table(
        {
            "lat": pa.array(lats, type=pa.float64()),
            "lon": pa.array(lons, type=pa.float64()),
            "x_m": pa.array(xs, type=pa.float64()),
            "y_m": pa.array(ys, type=pa.float64()),
            "h0_m": pa.array(h0s, type=pa.float64()),
            "tile_x": pa.array(txs, type=pa.int32()),
            "tile_y": pa.array(tys, type=pa.int32()),
            "row": pa.array(rows, type=pa.int32()),
        }
    )
    pq.write_table(table, out_dir / "index.parquet")
    return len(lats)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spacing-m", type=float, default=1000.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--lat-max", type=float, default=-80.0)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--limit-tiles", type=int, default=0, help="Smoke: only first N incomplete tiles")
    args = ap.parse_args()

    path_20 = DEM / "LDEM_80S_20MPP_ADJ.TIF"
    path_80 = DEM / "LDEM_80S_80MPP_ADJ.TIF"
    path_240 = DEM / "LDEM_60S_240MPP_ADJ.TIF"
    for p in (path_20, path_80, path_240):
        if not p.is_file():
            print(f"missing DEM: {p}", file=sys.stderr)
            return 1

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    progress_path = out / "progress.json"
    done: set[str] = set()
    if progress_path.is_file():
        done = set(json.loads(progress_path.read_text(encoding="utf-8")).get("tiles", []))

    print(f"building grid spacing={args.spacing_m} m lat<={args.lat_max} …", flush=True)
    pts = grid_points(args.spacing_m, args.lat_max)
    by_tile: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
    for lat, lon, x, y in pts:
        by_tile.setdefault(tile_key(x, y), []).append((lat, lon, x, y))
    tiles = sorted(by_tile)
    pending = [t for t in tiles if f"{t[0]}_{t[1]}" not in done]
    if args.limit_tiles > 0:
        pending = pending[: args.limit_tiles]
    print(
        f"points={len(pts)} tiles={len(tiles)} done={len(done)} pending={len(pending)} workers={args.workers}",
        flush=True,
    )

    global G80, G240, PATH_20
    print("loading 80 m + 240 m DEMs into parent (fork COW) …", flush=True)
    t_load = time.time()
    G80 = load_tif(path_80)
    G240 = load_tif(path_240)
    PATH_20 = str(path_20)
    print(f"DEM load {time.time() - t_load:.1f}s", flush=True)

    t_run = time.time()
    n_masks = 0
    ctx = mp.get_context("fork")
    # ponytail: one pool for the whole run — reloading 0.47 GB DEMs per tile was ~30 s each
    with ctx.Pool(processes=args.workers) as pool:
        for i, (tx, ty) in enumerate(pending):
            sites = by_tile[(tx, ty)]
            key = f"{tx}_{ty}"
            t0 = time.time()
            rows = pool.map(_one_mask, sites, chunksize=max(1, len(sites) // (args.workers * 4)))
            write_tile(out, tx, ty, rows)
            done.add(key)
            progress_path.write_text(json.dumps({"tiles": sorted(done)}, indent=0), encoding="utf-8")
            n_masks += len(rows)
            dt = time.time() - t0
            rate = len(rows) / dt if dt > 0 else 0.0
            eta = (len(pending) - i - 1) * dt
            print(
                f"[{i+1}/{len(pending)}] tile {key} n={len(rows)} {dt:.1f}s {rate:.1f}/s "
                f"eta_remaining≈{eta/3600:.1f}h total_masks={n_masks}",
                flush=True,
            )

    n_idx = rebuild_index(out)
    summary = {
        "spacing_m": args.spacing_m,
        "lat_max": args.lat_max,
        "observer_height_m": OH,
        "schedule_version": SCHEDULE_VERSION,
        "n_masks": n_idx,
        "n_tiles": len(done),
        "seconds": time.time() - t_run,
        "dem_ids": ["LDEM_80S_20MPP_ADJ", "LDEM_80S_80MPP_ADJ", "LDEM_60S_240MPP_ADJ"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"done index={n_idx} tiles={len(done)} wall={summary['seconds']/3600:.2f}h", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
