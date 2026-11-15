"""Soil erodibility resistance proxy (D-050d / D-06cb). Not a lofting rate without engine inputs."""

from __future__ import annotations

import math

G_M = 1.62
# ponytail: Apollo-typical regolith until polar maps are wired
RHO_BULK_KG_M3 = 1500.0
MEAN_GRAIN_M = 70e-6
COHESION_PA = 500.0
# Engineering floor near-vertical cells (D-06cb); not a Metzger claim
BETA_FLOOR = 0.05


def soil_resistance(slope_deg: float) -> float:
    """Metzger soil-side denominator: ρ g D β + α with β = cos(θ) (D-06cb)."""
    beta = max(BETA_FLOOR, math.cos(math.radians(slope_deg)))
    return RHO_BULK_KG_M3 * G_M * MEAN_GRAIN_M * beta + COHESION_PA


def soil_provenance(slope_deg: float) -> dict:
    """Nested provenance for the dust / soil_resistance row (D-06cb, D-9ed6)."""
    beta = max(BETA_FLOOR, math.cos(math.radians(slope_deg)))
    return {
        "label": "soil_erodibility_resistance_not_lofting_rate",
        "formula": "rho_m * g * D * beta + alpha",
        "metzger_slope_factor": "cos_theta_on_grain_term_only",
        "beta": beta,
        "beta_floor": BETA_FLOOR,
        "slope_deg": slope_deg,
        "slope_product": "pgda_ldsm",
        "soil_constants": "apollo_average_grain_cohesion_bulk_density",
        "decision": "D-20261115-pj-06cb",
    }
