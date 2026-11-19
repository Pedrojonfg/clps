"""Relief tiles: a DEM cut into pixel-aligned compressed tiles, and windows read back from them.

Per D-20261118-pj-6fea: every model is cut into ``tile_px`` x ``tile_px`` tiles aligned to the source grid,
stored as ``<ty>_<tx>.npz`` (tile row, column; edge tiles cropped) next to one ``manifest.json`` that lists
each file's sha256 and size. Tiles that are entirely NaN are omitted. Tiles are written byte-for-byte
reproducibly (``write_npz``), so re-cutting the same source gives the same sha256 and the same store version. ``window_from_tiles`` rebuilds exactly
the window ``load_tif(path, x, y, r)`` reads from the source file, so tiled and direct reads match.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import zipfile
from pathlib import Path
from typing import Callable

import numpy as np

from moonpark.horizon.grid import Grid, fill_holes_max

SCHEMA = 1
TILE_PX = 512  # the LDEMs' internal block size
LOCAL_ROOT = Path(__file__).resolve().parents[1] / "data" / "relief_tiles"  # where scripts/cut_dems.py writes
ZIP_DATE = (1980, 1, 1, 0, 0, 0)  # fixed entry timestamp: no wall clock in the bytes
ZIP_LEVEL = 6  # zlib's default, what np.savez_compressed uses: same size as before


def write_npz(path: str | Path, **arrays) -> None:
    """``np.savez_compressed`` with reproducible bytes: fixed timestamps, level, attributes, sorted entries.

    Each entry is ``<name>.npy`` in ``np.lib.format`` (version chosen by numpy for the array, as savez does),
    deflated at ``ZIP_LEVEL``; ``np.load`` reads the result like any .npz. Written via a temp file + rename,
    so a partly written tile never replaces a good one.
    """
    path = Path(path)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for name in sorted(arrays):
            npy = io.BytesIO()
            np.lib.format.write_array(npy, np.asanyarray(arrays[name]), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix, on every OS
            info.external_attr = 0o644 << 16
            zf.writestr(info, npy.getvalue(), compresslevel=ZIP_LEVEL)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(buf.getvalue())
    os.replace(tmp, path)


def locate(rel: str) -> Path | None:
    """``relief/<stem>/<file>``: the local cut ``data/relief_tiles/<stem>/<file>`` if present, else the store.

    The store key is ``relief/<stem>/<file>`` (scripts/publish_masks.py), the local cutter output lives in
    ``LOCAL_ROOT``; anything else (or a file not cut locally) goes to ``remote.locate(rel)`` unchanged.
    """
    if rel.startswith("relief/"):
        p = LOCAL_ROOT / rel.removeprefix("relief/")
        if p.is_file():
            return p
    from moonpark.horizon import remote

    return remote.locate(rel)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cut_model(src: str | Path, out: str | Path, tile_px: int = TILE_PX) -> dict:
    """Cut ``src`` into tiles under ``out``; write and return the manifest."""
    import rasterio
    from rasterio.windows import Window

    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict] = {}
    with rasterio.open(src) as ds:
        tr = ds.transform
        if tr.b != 0 or tr.d != 0 or tr.a != -tr.e:
            raise ValueError(f"{src.name}: only north-up square-pixel grids are supported")
        w, h = ds.width, ds.height
        for ty in range(math.ceil(h / tile_px)):
            for tx in range(math.ceil(w / tile_px)):
                win = Window(tx * tile_px, ty * tile_px, min(tile_px, w - tx * tile_px), min(tile_px, h - ty * tile_px))
                z = ds.read(1, window=win).astype(np.float32)
                if ds.nodata is not None and np.isfinite(ds.nodata):
                    z[z == np.float32(ds.nodata)] = np.nan  # as load_tif does
                if not np.isfinite(z).any():
                    continue
                rel = f"{ty}_{tx}.npz"
                t = ds.window_transform(win)
                write_npz(out / rel, z=z, x0=t.c, y0=t.f, res=t.a)
                files[rel] = {"sha256": _sha256(out / rel), "size": (out / rel).stat().st_size}
    manifest = {
        "schema": SCHEMA,
        "model": src.stem,
        "tile_px": tile_px,
        "res": float(tr.a),
        "x0": float(tr.c),
        "y0": float(tr.f),
        "width": w,
        "height": h,
        "files": files,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))
    return manifest


def bounds(manifest: dict) -> tuple[float, float, float, float]:
    """(left, bottom, right, top) in map metres, like rasterio's ``dataset.bounds``."""
    res, x0, y0 = manifest["res"], manifest["x0"], manifest["y0"]
    return x0, y0 - res * manifest["height"], x0 + res * manifest["width"], y0


def window_from_tiles(manifest: dict, fetch: Callable[[str], Path], x: float, y: float, radius_m: float) -> Grid:
    """The ``load_tif(src, x, y, radius_m)`` window, assembled from tiles; ``fetch(rel)`` returns a tile's path."""
    from affine import Affine
    from rasterio.windows import from_bounds

    res, tp = manifest["res"], manifest["tile_px"]
    tr = Affine(res, 0.0, manifest["x0"], 0.0, -res, manifest["y0"])
    win = from_bounds(x - radius_m, y - radius_m, x + radius_m, y + radius_m, tr).round_offsets().round_lengths()
    c0, r0 = max(int(win.col_off), 0), max(int(win.row_off), 0)
    c1 = min(int(win.col_off + win.width), manifest["width"])
    r1 = min(int(win.row_off + win.height), manifest["height"])
    z = np.full((max(r1 - r0, 0), max(c1 - c0, 0)), np.nan, dtype=np.float32)
    for ty in range(r0 // tp, (r1 - 1) // tp + 1):
        for tx in range(c0 // tp, (c1 - 1) // tp + 1):
            rel = f"{ty}_{tx}.npz"
            if rel not in manifest["files"]:
                continue  # all-NaN tile: stays NaN, as in the source
            with np.load(fetch(rel)) as f:
                t = f["z"]
            ty0, tx0 = ty * tp, tx * tp
            a, b = max(r0, ty0), min(r1, ty0 + t.shape[0])
            c, d = max(c0, tx0), min(c1, tx0 + t.shape[1])
            z[a - r0 : b - r0, c - c0 : d - c0] = t[a - ty0 : b - ty0, c - tx0 : d - tx0]
    z, n_filled = fill_holes_max(z)  # the same hole fill as load_tif
    t0 = tr @ Affine.translation(c0, r0)
    return Grid(z, float(t0.c), float(t0.f), float(t0.a), n_filled)
