"""Layer-B surface factors. # D-20261114-pj-de42 D-8764"""

from moonpark.hazards.lst import HazardDataUnavailable
from moonpark.hazards.moon import MoonHazards, aggregate_hazards, default_moon_hazards
from moonpark.providers import Site


class ConstantHazards:
    """Neutral term when P13 grids are absent."""

    def hazards(self, site: Site, times) -> dict:
        return {"hours": [], "aggregate": {}}


__all__ = ["ConstantHazards", "HazardDataUnavailable", "MoonHazards", "aggregate_hazards", "default_moon_hazards"]
