"""Layer-B surface factors (Hazards lane). # per D-20261114-pj-de42"""

from lunar_eval.providers import Site


class ConstantHazards:
    """Neutral term until P13."""

    def hazards(self, site: Site, times) -> dict:
        return {}

