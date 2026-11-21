"""Cap masks carry the terrain fill stats written at precompute time (D-d90c)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

from moonpark.horizon import cap_index

_PRE = Path(__file__).resolve().parents[1] / "scripts" / "precompute.py"


def _load_precompute():
    spec = importlib.util.spec_from_file_location("precompute_under_test", _PRE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _patch_tile(monkeypatch, tmp_path: Path, rows) -> None:
    pre = _load_precompute()
    pre.write_tile(tmp_path, 0, 0, rows)
    elev = np.load(tmp_path / "tiles" / "t0_0.npy")
    meta = json.loads((tmp_path / "tiles" / "t0_0.json").read_text())
    monkeypatch.setattr(cap_index, "_tile_elev", lambda tx, ty: elev)
    monkeypatch.setattr(cap_index, "_tile_meta", lambda tx, ty: meta)


def test_fill_stats_roundtrip_through_tile_meta(monkeypatch, tmp_path) -> None:
    el = np.zeros(720, dtype=np.float32)
    fill = {"filled_pixels": 3, "out_of_coverage_samples": 7}
    _patch_tile(monkeypatch, tmp_path, [(-89.0, 10.0, 1000.0, 2000.0, 12.5, el, fill)])
    m = cap_index.mask_from_cap_tile(0, 0, 0)
    assert m.fill_stats == fill


def test_tile_without_fill_key_loads_as_none(monkeypatch, tmp_path) -> None:
    el = np.zeros(720, dtype=np.float32)
    _patch_tile(monkeypatch, tmp_path, [(-89.0, 10.0, 1000.0, 2000.0, 12.5, el, None)])
    meta = json.loads((tmp_path / "tiles" / "t0_0.json").read_text())
    del meta["sites"][0]["fill"]  # a tile written before D-d90c
    monkeypatch.setattr(cap_index, "_tile_meta", lambda tx, ty: meta)
    assert cap_index.mask_from_cap_tile(0, 0, 0).fill_stats is None
