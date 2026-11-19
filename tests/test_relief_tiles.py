"""Relief tiles (lane L5, D-20261118-pj-6fea): DEM cut into pixel-aligned tiles, read back through the store.

All data is a small synthetic float32 GeoTIFF (1200x1200 px, 20 m, metres around the south pole like the real
LDEMs), so nothing here needs data/dem. Assumptions the implementation must honour are in the docstrings.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from moonpark.horizon import load_tif, polar_stereo_xy

LAT, LON = -89.46, 222.5
MODEL = "LDEM_80S_20MPP_ADJ"  # a stem terrain.py already knows
N = 1200
RES = 20.0
HALF = N * RES / 2  # 12000 m


def _mod():
    try:
        from moonpark import relief_tiles
    except ImportError:
        pytest.fail("moonpark.relief_tiles missing")
    return relief_tiles


def _origin() -> tuple[float, float]:
    """Top-left corner of the synthetic raster: centred on the site but off the metre grid (7.3, 3.1)."""
    x, y = polar_stereo_xy(LAT, LON)
    return x - HALF + 7.3, y + HALF + 3.1


def _write_tif(path: Path, offset: float = 0.0, nan_block: tuple[slice, slice] | None = None) -> np.ndarray:
    import rasterio
    from rasterio.transform import from_origin

    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:N, 0:N]
    z = (50.0 * np.sin(xx / 90.0) + 30.0 * np.cos(yy / 70.0) + rng.normal(size=(N, N)) + offset).astype("f4")
    if nan_block is not None:
        z[nan_block] = np.nan
    x0, y0 = _origin()
    with rasterio.open(
        path, "w", driver="GTiff", height=N, width=N, count=1, dtype="float32",
        transform=from_origin(x0, y0, RES, RES),
    ) as dst:
        dst.write(z, 1)
    return z


def _px(col: float, row: float) -> tuple[float, float]:
    """Map coordinates of the corner (col, row) in pixel units."""
    x0, y0 = _origin()
    return x0 + col * RES, y0 - row * RES


@pytest.fixture()
def src(tmp_path: Path) -> Path:
    p = tmp_path / f"{MODEL}.TIF"
    _write_tif(p)
    return p


def _cut(src: Path, tmp_path: Path, **kw) -> tuple[Path, dict]:
    rt = _mod()
    out = tmp_path / "cut"
    m = rt.cut_model(src, out, **kw)
    return out, m


def _tiled(out: Path, manifest: dict, x: float, y: float, r: float, fetched: list | None = None):
    rt = _mod()

    def fetch(rel: str) -> Path:
        if fetched is not None:
            fetched.append(rel)
        return out / rel

    return rt.window_from_tiles(manifest, fetch, x, y, r)


def _assert_same(a, b) -> None:
    assert a.Z.dtype == np.float32
    assert a.Z.shape == b.Z.shape
    assert np.array_equal(a.Z, b.Z)
    assert (a.x0, a.y0, a.res) == (b.x0, b.y0, b.res)


# ---- cutting ---------------------------------------------------------------------------------------------


def test_manifest_content(src: Path, tmp_path: Path) -> None:
    out, m = _cut(src, tmp_path)
    on_disk = json.loads((out / "manifest.json").read_text())
    assert on_disk == m
    x0, y0 = _origin()
    assert m["schema"] == 1
    assert m["model"] == MODEL  # source stem, case kept
    assert m["tile_px"] == 512  # default
    assert m["res"] == pytest.approx(RES)
    assert (m["width"], m["height"]) == (N, N)
    assert m["x0"] == pytest.approx(x0) and m["y0"] == pytest.approx(y0)
    assert "version" not in m  # version-free, like the other manifests' shape
    assert len(m["files"]) == 9  # ceil(1200/512)=3 per axis
    assert sorted(m["files"]) == sorted(f"{ty}_{tx}.npz" for ty in range(3) for tx in range(3))
    for rel, meta in m["files"].items():
        data = (out / rel).read_bytes()
        assert meta["size"] == len(data)
        assert meta["sha256"] == hashlib.sha256(data).hexdigest()
    assert {p.name for p in out.glob("*.npz")} == set(m["files"])


def test_tile_naming_alignment_and_content(src: Path, tmp_path: Path) -> None:
    """`<ty>_<tx>.npz` = tile row ty, column tx; tile (ty,tx) holds source pixels [ty*512:, tx*512:]."""
    out, m = _cut(src, tmp_path)
    full = load_tif(src).Z
    for ty in range(3):
        for tx in range(3):
            with np.load(out / f"{ty}_{tx}.npz") as f:
                assert f["z"].dtype == np.float32
                z = f["z"]
                expect = full[ty * 512 : (ty + 1) * 512, tx * 512 : (tx + 1) * 512]
                # Edge tiles may be stored cropped or padded; the top-left block must be the source block.
                assert z.shape[0] >= expect.shape[0] and z.shape[1] >= expect.shape[1]
                assert np.array_equal(z[: expect.shape[0], : expect.shape[1]], expect)
                assert len(f.files) > 1  # z plus origin/transform scalars


def test_custom_tile_px(src: Path, tmp_path: Path) -> None:
    out, m = _cut(src, tmp_path, tile_px=300)
    assert m["tile_px"] == 300
    assert len(m["files"]) == 16  # ceil(1200/300)=4 per axis
    assert "3_3.npz" in m["files"]


def test_all_nan_tile_is_omitted(tmp_path: Path) -> None:
    p = tmp_path / f"{MODEL}.TIF"
    _write_tif(p, nan_block=(slice(512, 1024), slice(0, 512)))  # exactly tile row 1, col 0
    out, m = _cut(p, tmp_path)
    assert "1_0.npz" not in m["files"]
    assert not (out / "1_0.npz").exists()
    assert len(m["files"]) == 8
    assert (m["width"], m["height"]) == (N, N)  # still describes the full raster
    # a window clear of the hole still matches the direct read
    x, y = _px(900, 300)
    _assert_same(_tiled(out, m, x, y, 2000), load_tif(p, x, y, 2000))


# ---- windows ---------------------------------------------------------------------------------------------

# (centre col, centre row, radius px): inside one tile, straddling vertical / horizontal / 4-tile corner,
# and touching each file edge / corner. Edge behaviour: the window is the same pixel window rasterio
# from_bounds + round_offsets/round_lengths gives load_tif; windows reaching exactly the file border are
# returned unpadded, exactly like load_tif.
CASES = {
    "inside_one_tile": (256, 256, 100),
    "inside_centre": (600, 600, 150),
    "straddle_vertical_boundary": (512, 300, 80),
    "straddle_horizontal_boundary": (300, 1024, 80),
    "straddle_four_tiles": (512, 512, 120),
    "left_edge": (100, 600, 100),
    "top_edge": (600, 100, 100),
    "right_edge": (1100, 600, 100),
    "bottom_edge": (600, 1100, 100),
    "corner_top_left": (100, 100, 100),
    "corner_bottom_right": (1100, 1100, 100),
}


@pytest.mark.parametrize("tile_px", [512, 256, 300])
@pytest.mark.parametrize("name", list(CASES))
def test_tiled_window_equals_direct(src: Path, tmp_path: Path, name: str, tile_px: int) -> None:
    out, m = _cut(src, tmp_path, tile_px=tile_px)
    c, r, rad = CASES[name]
    x, y = _px(c, r)
    _assert_same(_tiled(out, m, x, y, rad * RES), load_tif(src, x, y, rad * RES))


def test_whole_file_window_equals_direct(src: Path, tmp_path: Path) -> None:
    out, m = _cut(src, tmp_path)
    x, y = _px(600, 600)
    _assert_same(_tiled(out, m, x, y, HALF - 40), load_tif(src, x, y, HALF - 40))


def test_window_fetches_only_the_tiles_it_needs(src: Path, tmp_path: Path) -> None:
    out, m = _cut(src, tmp_path)
    got: list[str] = []
    x, y = _px(256, 256)
    _tiled(out, m, x, y, 100 * RES, fetched=got)
    assert set(got) == {"0_0.npz"}
    got.clear()
    x, y = _px(512, 512)  # corner shared by four tiles
    _tiled(out, m, x, y, 50 * RES, fetched=got)
    assert set(got) == {"0_0.npz", "0_1.npz", "1_0.npz", "1_1.npz"}


# ---- terrain integration ---------------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A fake data store: remote.locate('relief/<model>/...') -> files under tmp/data, else None."""
    from moonpark.horizon import remote

    root = tmp_path / "data"
    asked: list[str] = []

    def locate(rel: str):
        asked.append(rel)
        p = root / rel
        return p if p.is_file() else None

    monkeypatch.setattr(remote, "locate", locate)
    # The repo's real data/relief_tiles must not leak in through relief_tiles.locate's local lookup.
    monkeypatch.setattr(_mod(), "LOCAL_ROOT", tmp_path / "no_local_relief_tiles")
    locate.root = root  # type: ignore[attr-defined]
    locate.asked = asked  # type: ignore[attr-defined]
    return locate


def _cut_into_store(src: Path, store) -> None:
    _mod().cut_model(src, store.root / "relief" / MODEL)


def _dem_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tif: Path | None) -> Path:
    from moonpark import terrain

    d = tmp_path / "dem"
    d.mkdir()
    if tif is not None:
        (d / f"{MODEL}.TIF").write_bytes(tif.read_bytes())
    monkeypatch.setattr(terrain, "DEM", d)
    terrain._cached.cache_clear()
    return d


def test_terrain_falls_back_to_store_tiles_and_matches_local(
    src: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    from moonpark import terrain

    _dem_dir(tmp_path, monkeypatch, src)
    local = terrain.build_rings(LAT, LON)
    assert local["dem"]  # sanity: the synthetic tif is usable as a tier

    _cut_into_store(src, store)
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(terrain, "DEM", empty)
    terrain._cached.cache_clear()
    tiled = terrain.build_rings(LAT, LON)

    assert any(a.startswith(f"relief/{MODEL}/") for a in store.asked)
    assert tiled["ground_m"] == local["ground_m"]
    assert tiled["radii_m"] == local["radii_m"]
    assert tiled["heights_f32_b64"] == local["heights_f32_b64"]
    assert tiled["dem"]  # names a tier


def test_terrain_endpoint_serves_relief_without_local_dem(
    src: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    from fastapi.testclient import TestClient

    from moonpark.api.app import app

    _cut_into_store(src, store)
    _dem_dir(tmp_path, monkeypatch, None)
    res = TestClient(app).get("/terrain", params={"lat": LAT, "lon": LON})
    assert res.status_code == 200
    assert res.json()["heights_f32_b64"]


def test_terrain_prefers_local_dem_over_store(
    src: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    from moonpark import terrain

    other = tmp_path / "other.tif"
    _write_tif(other, offset=1000.0)  # store tiles are 1000 m higher: distinguishable
    _cut_into_store(other, store)
    _dem_dir(tmp_path, monkeypatch, src)

    d = terrain.build_rings(LAT, LON)
    x, y = polar_stereo_xy(LAT, LON)
    assert d["ground_m"] == pytest.approx(float(load_tif(src, x, y, 100).sample(np.array([x]), np.array([y]))[0]), abs=1.0)
    assert d["ground_m"] < 500  # not the +1000 store copy
    assert not any(a.startswith("relief/") and a.endswith(".npz") for a in store.asked)


def test_terrain_unavailable_without_local_dem_or_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    from moonpark import terrain

    _dem_dir(tmp_path, monkeypatch, None)
    try:
        terrain.build_rings(LAT, LON)
    except terrain.TerrainUnavailable:
        pass
    else:
        pytest.fail("expected TerrainUnavailable")
    _mod()  # the module itself must exist for this to be a meaningful pass
