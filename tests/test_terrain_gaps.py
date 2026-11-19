"""Terrain holes and edges: fill on the unfavorable side and report it.

Contract: D-20261118-pj-d90c (lane L3).

Public API these tests pin down (names chosen by the test author):
  * ``Grid.n_filled`` (int): pixels filled by ``load_tif`` (0 when none).
  * ``Grid.sample_with_stats(x, y) -> (values, n_out_of_coverage)``; the old
    ``Grid.sample`` keeps its return type (ndarray) and in-coverage values.
  * ``HorizonMask.fill_stats`` -> {'filled_pixels': int, 'out_of_coverage_samples': int};
    also written under the key ``fill_stats`` in the mask .json meta.

Assumptions (see lane report): fill proceeds in rings; in each ring a hole pixel
takes the max of the neighbours (8-neighbourhood) that were finite at the START
of that ring, so the result is independent of scan order. "Within 5 pixels" for
edge extension is taken inclusively (+-5 px along the edge), so tests accept 4 or 5.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from moonpark.horizon import grid as grid_mod
from moonpark.horizon import load_tif, mask, polar_stereo_xy
from moonpark.horizon import mask_store
from moonpark.providers import Site

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin  # noqa: E402

_REPO = Path(__file__).resolve().parents[1]
_SITE5 = _REPO / "data" / "dem" / "Site01_final_adj_5mpp_surf.tif"
SITE01 = Site(lat_deg=-89.46316, lon_deg=222.51045, observer_height_m=2.0)


def _write_tif(path, z, x0=0.0, y0=None, res=1.0, nodata=None):
    z = np.asarray(z, dtype=np.float32)
    y0 = float(z.shape[0]) * res if y0 is None else y0
    with rasterio.open(
        path, "w", driver="GTiff", height=z.shape[0], width=z.shape[1], count=1,
        dtype="float32", transform=from_origin(x0, y0, res, res), nodata=nodata,
    ) as dst:
        dst.write(z, 1)
    return path


def _n_filled(g) -> int:
    v = getattr(g, "n_filled", None)
    if v is None:
        pytest.fail("Grid has no n_filled attribute (fill count not exposed)")
    return v


# ---------------------------------------------------------------- 1. load_tif

def test_single_pixel_hole_on_ridge_takes_neighbour_max(tmp_path):
    z = np.zeros((11, 11), np.float32)
    z[:, 5] = 100.0  # N-S ridge through the hole
    z[5, 5] = np.nan
    g = load_tif(_write_tif(tmp_path / "a.tif", z))
    assert g.Z[5, 5] == pytest.approx(100.0), "hole on a ridge must take the neighbour max, not the window mean"
    assert np.isfinite(g.Z).all()
    assert _n_filled(g) == 1


def test_no_hole_reports_zero_filled(tmp_path):
    g = load_tif(_write_tif(tmp_path / "a.tif", np.ones((6, 6), np.float32)))
    assert _n_filled(g) == 0


def test_3x3_hole_fills_ring_by_ring_without_order_dependence(tmp_path):
    z = np.zeros((11, 11), np.float32)
    z[3, 3] = 70.0  # touches only hole corner (4,4)
    z[4:7, 4:7] = np.nan
    g = load_tif(_write_tif(tmp_path / "a.tif", z))
    assert np.isfinite(g.Z).all()
    assert _n_filled(g) == 9
    assert g.Z[4, 4] == pytest.approx(70.0)   # ring 1: max of finite neighbours
    assert g.Z[4, 5] == pytest.approx(0.0)    # ring 1 must NOT see (4,4) filled this step
    assert g.Z[5, 5] == pytest.approx(70.0)   # ring 2: centre sees ring-1 values
    assert g.Z[4:7, 4:7].min() >= 0.0 and g.Z.max() <= 70.0  # never window mean/new extremes


def test_hole_at_window_corner(tmp_path):
    z = np.array([[np.nan, 5, 0], [9, 2, 0], [0, 0, 0]], np.float32)
    g = load_tif(_write_tif(tmp_path / "a.tif", z))
    assert g.Z[0, 0] == pytest.approx(9.0)
    assert _n_filled(g) == 1


def test_nodata_value_treated_as_hole(tmp_path):
    z = np.zeros((9, 9), np.float32)
    z[:, 4] = 80.0
    z[4, 4] = -9999.0
    p = _write_tif(tmp_path / "a.tif", z, nodata=-9999.0)
    g = load_tif(p)
    assert g.Z[4, 4] == pytest.approx(80.0)
    assert g.Z.min() >= 0.0
    assert _n_filled(g) == 1


def test_hole_without_any_finite_neighbour_raises(tmp_path):
    p = _write_tif(tmp_path / "a.tif", np.full((3, 3), np.nan, np.float32))
    with pytest.raises(ValueError):
        load_tif(p)


# ------------------------------------------------------------- 2. Grid.sample

def _edge_grid():
    z = np.zeros((20, 20), np.float32)
    z[:, 0] = np.arange(20, dtype=np.float32)  # west edge rises southward (row index)
    return grid_mod.Grid(z, 0.0, 20.0, 1.0)


def test_out_of_coverage_sample_takes_max_over_edge_segment():
    g = _edge_grid()
    # row 10 centre: y = 20 - 10.5; 3 m west of the grid
    v = g.sample(np.array([-3.0]), np.array([9.5]))
    assert v[0] >= 14.0, f"expected max over +-5 px edge segment (~15), got nearest-edge value {v[0]}"
    assert v[0] <= 15.0


def test_sample_with_stats_counts_out_of_coverage():
    g = _edge_grid()
    fn = getattr(g, "sample_with_stats", None)
    if fn is None:
        pytest.fail("Grid.sample_with_stats missing")
    x = np.array([-3.0, 5.0, 25.0])
    y = np.array([9.5, 9.5, 9.5])
    vals, n_out = fn(x, y)
    assert n_out == 2
    assert vals.shape == x.shape
    fn2 = g.sample_with_stats(np.array([5.0]), np.array([9.5]))
    assert fn2[1] == 0


def test_in_coverage_sample_unchanged():
    g = _edge_grid()
    x, y = np.array([[5.0, 6.5], [10.2, 3.3]]), np.array([[9.5, 4.1], [12.0, 18.0]])
    out = g.sample(x, y)
    assert isinstance(out, np.ndarray) and out.shape == x.shape
    from scipy.ndimage import map_coordinates
    col = (x - 0.0) / 1.0 - 0.5
    row = (20.0 - y) / 1.0 - 0.5
    ref = map_coordinates(g.Z, [row.ravel(), col.ravel()], order=1, mode="nearest").reshape(x.shape)
    np.testing.assert_allclose(out, ref, rtol=1e-6)


# ------------------------------------------------------- 3. mask provenance

def _site_grid(tmp_path, half=50.0, nan_at=None, res=5.0):
    x_m, y_m = polar_stereo_xy(SITE01.lat_deg, SITE01.lon_deg)
    n = int(2 * half / res)
    z = np.zeros((n, n), np.float32)
    z[: n // 4, :] = 20.0  # a wall on one side so the horizon is not flat
    if nan_at is not None:
        z[nan_at] = np.nan
    p = _write_tif(tmp_path / "s.tif", z, x0=x_m - half, y0=y_m + half, res=res)
    return load_tif(p)


def _stats(m):
    s = getattr(m, "fill_stats", None)
    if s is None:
        pytest.fail("HorizonMask has no fill_stats")
    return s


def test_mask_reports_filled_pixels_and_out_of_coverage(tmp_path):
    g = _site_grid(tmp_path, half=50.0, nan_at=(2, 2))
    m = mask(SITE01, schedule=[(5.0, 400.0, g)])  # 400 m rays leave a 100 m grid
    s = _stats(m)
    assert s["filled_pixels"] == 1
    assert s["out_of_coverage_samples"] > 0


def test_mask_without_fill_or_edges_has_zero_stats(tmp_path):
    g = _site_grid(tmp_path, half=1000.0)
    m = mask(SITE01, schedule=[(5.0, 100.0, g)])
    s = getattr(m, "fill_stats", None) or {}
    assert s.get("filled_pixels", 0) == 0
    assert s.get("out_of_coverage_samples", 0) == 0


def test_fill_stats_written_to_json_meta_and_roundtrip(tmp_path, monkeypatch):
    g = _site_grid(tmp_path, half=50.0, nan_at=(2, 2))
    m = mask(SITE01, schedule=[(5.0, 400.0, g)])
    _stats(m)
    monkeypatch.setattr(mask_store, "MASK_DIR", tmp_path / "masks")
    mask_store.save_mask(SITE01, m)
    meta = json.loads(next((tmp_path / "masks").glob("*.json")).read_text(encoding="utf-8"))
    assert meta.get("fill_stats", {}).get("filled_pixels") == 1
    assert meta["fill_stats"]["out_of_coverage_samples"] == m.fill_stats["out_of_coverage_samples"]
    back = mask_store.load_cached_mask(SITE01)
    assert getattr(back, "fill_stats", None) == m.fill_stats


# ------------------------------------------------- 4. unfavorable (5 m data)

@pytest.mark.skipif(not _SITE5.is_file(), reason="Site01 5 m DEM not present")
def test_punched_holes_do_not_lower_horizon_on_average(tmp_path):
    with rasterio.open(_SITE5) as src:
        z = src.read(1).astype(np.float32)
        tr = src.transform
    x_m, y_m = polar_stereo_xy(SITE01.lat_deg, SITE01.lon_deg)
    r0, c0 = int((tr.f - y_m) / 5.0), int((x_m - tr.c) / 5.0)
    # Holes are punched on the pixels that DEFINE the horizon at 20 random azimuths
    # (random holes elsewhere do not change the horizon at all: measured diff 0).
    import math
    from moonpark.horizon.mask import R_M
    rng = np.random.default_rng(20261118)
    ex, ey = -x_m, -y_m
    nrm = math.hypot(ex, ey)
    ex, ey = ex / nrm, ey / nrm
    nx, ny = -ey, ex
    h0 = float(z[r0, c0]) + SITE01.observer_height_m
    punched = np.zeros(z.shape, bool)
    dd = np.arange(10.0, 4000.0, 5.0)
    for k in rng.choice(720, 20, replace=False):
        az = math.radians(k * 0.5)
        X = x_m + dd * (math.cos(az) * ex + math.sin(az) * nx)
        Y = y_m + dd * (math.cos(az) * ey + math.sin(az) * ny)
        rr = ((tr.f - Y) / 5.0).astype(int)
        cc = ((X - tr.c) / 5.0).astype(int)
        ok = (rr > 1) & (rr < z.shape[0] - 2) & (cc > 1) & (cc < z.shape[1] - 2)
        ang = np.where(ok, (z[rr.clip(0, z.shape[0] - 1), cc.clip(0, z.shape[1] - 1)] - h0 - dd**2 / (2 * R_M)) / dd, -9.0)
        j = int(ang.argmax())
        punched[rr[j] - 1 : rr[j] + 2, cc[j] - 1 : cc[j] + 2] = True
    zh = z.copy()
    zh[punched] = np.nan
    n_nan = int(punched.sum())
    p_h = _write_tif(tmp_path / "holes.tif", zh, x0=tr.c, y0=tr.f, res=5.0)
    p_o = _write_tif(tmp_path / "orig.tif", z, x0=tr.c, y0=tr.f, res=5.0)
    g_h, g_o = load_tif(p_h), load_tif(p_o)
    assert _n_filled(g_h) == n_nan
    m_h = mask(SITE01, schedule=[(5.0, 4000.0, g_h)])
    m_o = mask(SITE01, schedule=[(5.0, 4000.0, g_o)])
    diff = m_h.elevation_deg.astype(float) - m_o.elevation_deg.astype(float)
    print(f"holes-orig horizon diff: mean={diff.mean():.4f} min={diff.min():.4f} max={diff.max():.4f} deg")
    assert diff.mean() >= -0.05
    # measured with a reference max-of-neighbours fill: mean +0.025, min -0.28, max +0.46 deg
