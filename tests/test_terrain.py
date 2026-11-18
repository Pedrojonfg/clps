"""Ring-mesh relief for the first-person view. DEM-backed checks skip where the DEMs are absent (CI)."""

from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from moonpark.api.app import app
from moonpark.terrain import NAZ, TerrainUnavailable, build_rings, ring_radii

_DEM = Path(__file__).resolve().parents[1] / "data" / "dem"
_SITE5 = _DEM / "Site01_final_adj_5mpp_surf.tif"
needs_dem = pytest.mark.skipif(not _SITE5.is_file(), reason="Site01 5 m DEM not present")
SITE01 = (-89.46316, 222.51045)


def test_ring_radii_grow_geometrically_to_the_limit() -> None:
    r = ring_radii()
    assert r[0] == pytest.approx(4.0)
    assert r[-1] == pytest.approx(30_000.0)
    assert np.all(np.diff(r) > 0)


def test_northern_sites_have_no_relief() -> None:
    with pytest.raises(TerrainUnavailable):
        build_rings(10.0, 0.0)


def test_endpoint_reports_missing_relief_as_503() -> None:
    res = TestClient(app).get("/terrain", params={"lat": 10, "lon": 0})
    assert res.status_code == 503
    assert res.json()["detail"]["error"] == "terrain_unavailable"


@needs_dem
def test_rings_shape_and_horizon_agree_with_the_mask() -> None:
    from moonpark.horizon import mask
    from moonpark.horizon.dem_schedule import mask_schedule_for_site
    from moonpark.providers import Site

    d = build_rings(*SITE01)
    h = np.frombuffer(base64.b64decode(d["heights_f32_b64"]), dtype="<f4").reshape(len(d["radii_m"]), d["naz"])
    assert d["naz"] == NAZ and np.isfinite(h).all()

    r = np.array(d["radii_m"])
    horizon = np.degrees(np.arctan((h - 2.0) / r[:, None])).max(axis=0)  # geographic azimuth, 2 m eye
    site = Site(lat_deg=SITE01[0], lon_deg=SITE01[1], observer_height_m=2.0)
    sched = mask_schedule_for_site(site, _SITE5)
    if sched is None:
        pytest.skip("mask DEM stack not present")
    m = mask(site, schedule=sched).elevation_deg.reshape(360, 2).max(axis=1)
    # Same convention the planner payload documents: index = -(az - 180) mod 360 (D-b43a).
    ours = m[(-(np.arange(360) - 180)) % 360]
    assert np.corrcoef(ours, horizon)[0, 1] > 0.9
