"""Relief tiles in the published data store and reproducible cuts (D-20261118-pj-6fea, D-20261118-pj-62d3).

* Re-cutting the same source yields byte-identical tiles (no zip timestamps), still readable by np.load.
* The ``data`` group lists, when cut locally, ``relief/<stem>/<rel>`` (source data/relief_tiles/<stem>/<rel>)
  and ``relief/<stem>/manifest.json``; its content-derived version follows the tiles.
* ``relief_tiles.locate('relief/<stem>/...')`` finds data/relief_tiles/<stem>/... before the store.

No network and no real data: synthetic GeoTIFFs and a temp ``data/`` tree.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pytest

from moonpark import relief_tiles

REPO = Path(__file__).resolve().parents[1]
MODEL = "LDEM_80S_20MPP_ADJ"
N, RES = 1200, 20.0


def _write_tif(path: Path, offset: float = 0.0) -> np.ndarray:
    """Synthetic float32 polar-stereo GeoTIFF, N x N px at RES m (the same shape as test_relief_tiles')."""
    import rasterio
    from rasterio.transform import from_origin

    yy, xx = np.mgrid[0:N, 0:N]
    z = (50.0 * np.sin(xx / 90.0) + 30.0 * np.cos(yy / 70.0)
         + np.random.default_rng(7).normal(size=(N, N)) + offset).astype("f4")
    with rasterio.open(path, "w", driver="GTiff", height=N, width=N, count=1, dtype="float32",
                       transform=from_origin(-12007.3, 12003.1, RES, RES)) as dst:
        dst.write(z, 1)
    return z


def _digests(d: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.iterdir())}


# ---- deterministic tiles ----------------------------------------------------------------------------------


def test_recut_is_byte_identical(tmp_path: Path) -> None:
    src = tmp_path / f"{MODEL}.TIF"
    _write_tif(src)
    m1 = relief_tiles.cut_model(src, tmp_path / "a", tile_px=600)
    time.sleep(2.1)  # zip timestamps have 2 s resolution: a timestamped writer would differ now
    m2 = relief_tiles.cut_model(src, tmp_path / "b", tile_px=600)
    assert m1 == m2
    assert _digests(tmp_path / "a") == _digests(tmp_path / "b")


def test_tile_is_fixed_format_npz_readable_by_np_load(tmp_path: Path) -> None:
    src = tmp_path / f"{MODEL}.TIF"
    z_src = _write_tif(src)
    out = tmp_path / "cut"
    m = relief_tiles.cut_model(src, out, tile_px=600)
    with zipfile.ZipFile(out / "0_0.npz") as zf:
        infos = zf.infolist()
        names = [i.filename for i in infos]
        assert names == sorted(names) == ["res.npy", "x0.npy", "y0.npy", "z.npy"]
        for i in infos:
            assert i.date_time == (1980, 1, 1, 0, 0, 0)
            assert i.compress_type == zipfile.ZIP_DEFLATED
    with np.load(out / "0_0.npz") as f:
        assert sorted(f.files) == ["res", "x0", "y0", "z"]
        assert f["z"].dtype == np.float32 and f["z"].shape == (600, 600)
        assert np.array_equal(f["z"], z_src[:600, :600])
        assert float(f["res"]) == pytest.approx(m["res"])
        assert float(f["x0"]) == pytest.approx(m["x0"]) and float(f["y0"]) == pytest.approx(m["y0"])
    # size stays in the same range as np.savez_compressed (no predictor, same deflate)
    ref = tmp_path / "ref.npz"
    with np.load(out / "0_0.npz") as f:
        np.savez_compressed(ref, **{k: f[k] for k in f.files})
    assert abs((out / "0_0.npz").stat().st_size - ref.stat().st_size) < 0.02 * ref.stat().st_size


def test_recut_with_new_content_changes_sha(tmp_path: Path) -> None:
    a, b = tmp_path / "a.TIF", tmp_path / "b.TIF"
    _write_tif(a)
    _write_tif(b, offset=1.0)
    ma = relief_tiles.cut_model(a, tmp_path / "ca", tile_px=600)
    mb = relief_tiles.cut_model(b, tmp_path / "cb", tile_px=600)
    assert ma["files"]["0_0.npz"]["sha256"] != mb["files"]["0_0.npz"]["sha256"]


# ---- local locate ------------------------------------------------------------------------------------------


def test_locate_prefers_local_relief_tiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from moonpark.horizon import remote

    local = tmp_path / "relief_tiles"
    (local / MODEL).mkdir(parents=True)
    (local / MODEL / "manifest.json").write_text("{}")
    monkeypatch.setattr(relief_tiles, "LOCAL_ROOT", local)
    asked: list[str] = []
    monkeypatch.setattr(remote, "locate", lambda rel: asked.append(rel) or None)

    assert relief_tiles.locate(f"relief/{MODEL}/manifest.json") == local / MODEL / "manifest.json"
    assert asked == []  # found locally: the store is not asked
    assert relief_tiles.locate(f"relief/{MODEL}/0_0.npz") is None
    assert asked == [f"relief/{MODEL}/0_0.npz"]  # missing locally: falls through to remote.locate


# ---- publishing --------------------------------------------------------------------------------------------


@pytest.fixture()
def pm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """publish_masks with DATA pointed at a temp tree holding fake kernels/hazards/dem files."""
    path = REPO / "scripts" / "publish_masks.py"
    spec = importlib.util.spec_from_file_location("publish_masks_relief_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = tmp_path / "data"
    for n in mod.KERNELS:
        (data / "kernels").mkdir(parents=True, exist_ok=True)
        (data / "kernels" / n).write_bytes(n.encode())
    for season in ("summer", "winter"):
        (data / "hazards" / "pcp" / season).mkdir(parents=True)
        (data / "hazards" / "pcp" / season / "ltim01.npz").write_bytes(season.encode())
    (data / "dem").mkdir()
    for n in mod.DEM_FILES:
        (data / "dem" / n).write_bytes(n.encode())
    monkeypatch.setattr(mod, "DATA", data)
    monkeypatch.setitem(mod.GROUPS, "data", (data, mod.data_files))
    mod.data_dir = data
    return mod


def _cut_relief(pm, tmp_path: Path, offset: float = 0.0) -> dict:
    src = tmp_path / f"{MODEL}.TIF"
    _write_tif(src, offset=offset)
    return relief_tiles.cut_model(src, pm.data_dir / "relief_tiles" / MODEL, tile_px=600)


def test_data_group_without_relief_is_unchanged(pm) -> None:
    m = pm.build_manifest("data")
    assert not any(k.startswith("relief") for k in m["files"])
    assert len(m["files"]) == len(pm.KERNELS) + 2 + len(pm.DEM_FILES)


def test_data_group_lists_relief_tiles_and_model_manifest(pm, tmp_path: Path) -> None:
    rm = _cut_relief(pm, tmp_path)
    m = pm.build_manifest("data")
    relief = {k for k in m["files"] if k.startswith("relief/")}
    assert relief == {f"relief/{MODEL}/{r}" for r in rm["files"]} | {f"relief/{MODEL}/manifest.json"}
    assert not any(k.startswith("relief_tiles/") for k in m["files"])
    for rel, meta in rm["files"].items():
        assert m["files"][f"relief/{MODEL}/{rel}"] == meta  # same size and sha256 as the model manifest
    assert "kernels/de440s.bsp" in m["files"]  # the other data still listed


def test_relief_plan_uploads_reads_from_relief_tiles(pm, tmp_path: Path) -> None:
    _cut_relief(pm, tmp_path)
    m = pm.build_manifest("data")
    plan = pm.plan_uploads("data", m, m["version"])
    by_key = {k: Path(p) for p, k, _ in plan}
    v = m["version"]
    src = pm.data_dir / "relief_tiles" / MODEL
    assert by_key[f"data/{v}/relief/{MODEL}/manifest.json"] == src / "manifest.json"
    assert by_key[f"data/{v}/relief/{MODEL}/0_0.npz"] == src / "0_0.npz"
    assert by_key[f"data/{v}/kernels/de440s.bsp"] == pm.data_dir / "kernels" / "de440s.bsp"
    for p, k, _ in plan[:-2]:
        rel = k.removeprefix(f"data/{v}/")
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == m["files"][rel]["sha256"]
    keys = [k for _, k, _ in plan]
    assert keys[-2:] == [f"data/{v}/manifest.json", "data/latest.json"]


def test_data_version_stable_on_recut_and_changes_with_tiles(pm, tmp_path: Path) -> None:
    v0 = pm.build_manifest("data")["version"]
    _cut_relief(pm, tmp_path)
    v1 = pm.build_manifest("data")["version"]
    assert v1 != v0  # adding relief is a new version
    time.sleep(2.1)
    _cut_relief(pm, tmp_path)  # same source again
    assert pm.build_manifest("data")["version"] == v1
    _cut_relief(pm, tmp_path, offset=1.0)  # tiles change
    assert pm.build_manifest("data")["version"] != v1


def test_incomplete_relief_dir_is_not_published(pm, tmp_path: Path) -> None:
    d = pm.data_dir / "relief_tiles" / "LDEM_80S_40MPP_ADJ"
    d.mkdir(parents=True)
    (d / "0_0.npz").write_bytes(b"partial")  # no manifest.json: cut not finished
    m = pm.build_manifest("data")
    assert not any(k.startswith("relief/") for k in m["files"])


def test_relief_tile_missing_from_disk_fails(pm, tmp_path: Path) -> None:
    rm = _cut_relief(pm, tmp_path)
    (pm.data_dir / "relief_tiles" / MODEL / sorted(rm["files"])[0]).unlink()
    with pytest.raises(SystemExit):
        pm.build_manifest("data")


def test_relief_tile_not_matching_model_manifest_fails(pm, tmp_path: Path) -> None:
    rm = _cut_relief(pm, tmp_path)
    p = pm.data_dir / "relief_tiles" / MODEL / sorted(rm["files"])[0]
    b = bytearray(p.read_bytes())
    b[len(b) // 2] ^= 0xFF  # same size, different content
    p.write_bytes(bytes(b))
    with pytest.raises(SystemExit):
        pm.build_manifest("data")
