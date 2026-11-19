#!/usr/bin/env python3
"""Cut LOLA elevation models into relief tiles for the data store (D-20261118-pj-6fea).

    python scripts/cut_dems.py --src data/dem/LDEM_80S_80MPP_ADJ.TIF --out data/relief_tiles/LDEM_80S_80MPP_ADJ
    python scripts/cut_dems.py --all            # every tiled model terrain.py knows, found in data/dem

The 5 m site mosaics (Site*_..._5mpp_surf.tif) are not cut: they stay whole files.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from moonpark import relief_tiles, terrain  # noqa: E402


def _cut(src: Path, out: Path, tile_px: int) -> None:
    t = time.monotonic()
    m = relief_tiles.cut_model(src, out, tile_px=tile_px)
    size = sum(f["size"] for f in m["files"].values())
    print(f"{src.name}: {len(m['files'])} tiles, {size / 1e6:.1f} MB, {time.monotonic() - t:.0f} s -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--tile-px", type=int, default=relief_tiles.TILE_PX)
    ap.add_argument("--all", action="store_true", help="cut every model of terrain._CANDIDATES in data/dem")
    a = ap.parse_args()
    if a.all:
        for pat in terrain._CANDIDATES:
            if "*" in pat:
                continue
            src = terrain.DEM / pat
            if src.is_file():
                _cut(src, REPO / "data" / "relief_tiles" / src.stem, a.tile_px)
            else:
                print(f"{pat}: not in {terrain.DEM}, skipped")
    elif a.src and a.out:
        _cut(a.src, a.out, a.tile_px)
    else:
        ap.error("give --src and --out, or --all")


if __name__ == "__main__":
    main()
