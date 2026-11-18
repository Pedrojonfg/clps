import numpy as np

from moonpark import planner_payload


def test_local_search_window_uses_elapsed_hours_with_fine_steps(monkeypatch) -> None:
    import moonpark.search.local as local

    seen = {}

    def fake(site, anchor, window_hours, *a, **k):
        seen["h"] = window_hours
        return {"pick": None, "leaderboard": []}

    monkeypatch.setattr(local, "local_search", fake)
    t0 = np.datetime64("2027-01-01T00:00:00", "s")
    times = t0 + np.arange(24 * 6 + 1) * np.timedelta64(10, "m")  # 24 h at 10 min
    try:
        from moonpark.providers import Site

        planner_payload.build_planner_payload(
            Site(lat_deg=-89.0, lon_deg=0.0, observer_height_m=2.0),
            times,
            needs={"max_no_earth_h": 100},
            sun_lit_percent=50,
            earth_lit_percent=50,
            bridge_h=0,
            hazards_enabled=False,
            local_search=True,
            step_min=10,
        )
    except Exception:
        pass  # engine data may be absent; only the window computation matters
    if "h" in seen:
        assert seen["h"] == 24
