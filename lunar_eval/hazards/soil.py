"""Soil erodibility resistance proxy (D-050d). Not a lofting rate without engine inputs."""

from __future__ import annotations

import math

G_M = 1.62
# ponytail: Apollo-typical regolith until polar maps are wired
RHO_BULK_KG_M3 = 1500.0
MEAN_GRAIN_M = 70e-6
BETA_FLAT = 0.5
COHESION_PA = 500.0


def soil_resistance(slope_deg: float) -> float:
    """Metzger-style soil-side denominator; slope factor pending D-050d formula."""
    base = RHO_BULK_KG_M3 * G_M * MEAN_GRAIN_M * BETA_FLAT + COHESION_PA
    # ponytail: cos(slope) until Metzger slope substitution is recorded
    factor = max(0.1, math.cos(math.radians(slope_deg)))
    return base / factor