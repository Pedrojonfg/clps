"""Production test window per D-aa58 / D-8588."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app
from lunar_eval.site01 import real_data_available

client = TestClient(app)


@pytest.mark.skipif(not real_data_available(), reason="Site01 DEM or kernels not present")
def test_first_week_january_2027_produces_hourly_series() -> None:
    r = client.get(
        "/site",
        params={
            "start": "2027-01-01T00:00:00Z",
            "end": "2027-01-07T23:00:00Z",
            "step_h": 1,
            "template_id": "clps_average",
            "hazards_enabled": "false",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data_source"] == "real"
    assert len(body["sky"]) == 7 * 24
    assert len(body["series"]["sun_fraction"]) == len(body["sky"])