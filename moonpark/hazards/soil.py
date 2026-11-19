"""Soil erodibility resistance proxy (D-050d / D-06cb). Not a lofting rate without engine inputs."""

from __future__ import annotations

import math

G_M = 1.62
# D-20261117-pj-c82e: Metzger (2024) lunar baseline, provisional. alpha is the cohesive ENERGY density (J/m^3),
# not Mohr-Coulomb cohesion (Pa). Result is in J/m^3.
RHO_BULK_KG_M3 = 1300.0
MEAN_D_M = 1.5 * 2.3 * 77.5e-6  # <D> = 1.5 * D84, D84 = 2.3 * D50, D50 = 77.5 um
ALPHA_J_M3 = 0.289
# Engineering floor near-vertical cells (D-06cb); not a Metzger claim
BETA_FLOOR = 0.05


def soil_resistance(slope_deg: float | None) -> float | None:
    """Metzger soil-side denominator: ρ g D β + α with β = cos(θ) (D-06cb).

    None when the slope is not available: no flat-terrain substitute (D-20261118-pj-b3dc)."""
    if slope_deg is None:
        return None
    beta = max(BETA_FLOOR, math.cos(math.radians(slope_deg)))
    return RHO_BULK_KG_M3 * G_M * MEAN_D_M * beta + ALPHA_J_M3


def soil_provenance(slope_deg: float | None) -> dict:
    """Nested provenance for the dust / soil_resistance row (D-06cb, D-9ed6). beta is None without slope."""
    beta = None if slope_deg is None else max(BETA_FLOOR, math.cos(math.radians(slope_deg)))
    return {
        "label": "soil_erodibility_resistance_not_lofting_rate",
        "formula": "rho_m * g * D * beta + alpha",
        "metzger_slope_factor": "cos_theta_on_grain_term_only",
        "beta": beta,
        "beta_floor": BETA_FLOOR,
        "slope_deg": slope_deg,
        "slope_product": "pgda_ldsm",
        "soil_constants": "metzger_2024_lunar_baseline",
        "alpha_label": "cohesive_energy_density_not_mohr_coulomb",
        "units": "J/m3",
        "decision": "D-20261117-pj-c82e",
    }
