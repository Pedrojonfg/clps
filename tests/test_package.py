from lunar_eval import __version__
from lunar_eval.providers import MOON, HorizonMask, Site


def test_version():
    assert __version__ == "0.1.0"


def test_moon_seam():
    assert MOON.name == "moon"
    assert MOON.radius_m == 1_737_400.0


def test_mask_bins_are_half_degree():
    site = Site(lat_deg=-89.5, lon_deg=0.0)
    assert site.observer_height_m == 2.0
    assert HorizonMask.__annotations__["elevation_deg"]
