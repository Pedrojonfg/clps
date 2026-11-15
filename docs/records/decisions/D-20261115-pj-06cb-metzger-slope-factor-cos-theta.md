---
id: D-20261115-pj-06cb
title: "Metzger slope factor β = cos(θ) on the grain term only"
date: 2026-11-15T11:58:15Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-98c4
concepts: [hazard proxy, Metzger slope factor]
supersedes: [D-20261114-pj-050d]
relates: [D-20261114-pj-8764, D-20261114-pj-5cfa]
ai: opinion-requested
---
# Metzger slope factor β = cos(θ) on the grain term only

## Context

`D-20261114-pj-050d` left `dust_metzger_slope_factor` deferred. Code in `lunar_eval/hazards/soil.py` used a provisional `base / cos(slope)` with a hardcoded `0.5` on the grain term (Metzger’s crater-experiment β≈½, not flat Moon). Metzger (2024) soil-side resistance is ρ_m g D β + α with β = cos(θ); on a flat lunar surface β = 1. This task (S12/S14/S15 pack) must close the deferred value so provenance and claims can name the factor.

## Framing

Prefer the published substitution over inventing a new slope curve; keep the hazard a soil-resistance proxy, not a full plume rate.

## Options considered

1. **A — β = 1 always**: ignore site slope.
2. **B — Metzger as written**: β = cos(θ) on the grain term only; α unchanged; θ from PGDA LDSM.
3. **C — Keep code placeholder** `base / cos(θ)` with embedded 0.5.
4. **D — Leave deferred**.

## Decision

**B.** Soil resistance = ρ_m g D · cos(θ) + α, with θ = site slope from PGDA LDSM (degrees → radians for cos). Apollo-average ρ_m, D, α unchanged. Label remains soil erodibility resistance, not lofting rate (`D-050d`).

## Rationale

Metzger as written — do not reinvent; a simple cos-style factor is enough and matching the paper keeps it from getting out of hand.

## Checks raised

- Current code is not Metzger-exact (÷cos on whole base; fixed 0.5) → kept B; implementation must replace that form.
- Near-vertical slopes make cos(θ) → 0 → kept B; a small positive floor on β is an implementation guard, not a second physical model (see Values).
- Falsification vague (“outside normal”) / little numerical stress testing → kept B; pj accepted moving on; bulk/surface scaling still deferred in `D-5cfa`.

## Values

| Name | Value | Notes |
|------|-------|-------|
| dust_quantity | soil_resistance_proxy_metzger | Restated from `D-050d` |
| dust_quantity_label | soil_erodibility_resistance_not_lofting_rate | Restated from `D-050d` |
| dust_soil_constants | apollo_average_grain_cohesion_bulk_density | Restated from `D-050d` |
| dust_slope_input | pgda_ldsm_degrees | Restated from `D-050d` |
| dust_metzger_slope_factor | cos_theta_on_grain_term_only | Closes deferred in `D-050d`; β multiplies ρ_m g D only |
| dust_metzger_beta | cos(theta_rad) | θ from `dust_slope_input` |
| dust_metzger_flat_beta | 1 | Do not hardcode 0.5 (crater ~60° in experiments) |
| dust_resistance_formula | rho_m * g * D * beta + alpha | Metzger soil-side denominator |
| dust_beta_floor | max(beta, 0.05) | Engineering floor near vertical |
| dust_engine_inputs | out — no default nozzle in the hazard term | Restated from `D-050d` |
| dust_rock_abundance | out | Restated from `D-050d` |
| dust_pgda_roughness | out | Restated from `D-050d` |
| dust_ldex | out | Restated from `D-050d` |

## Expected behavior and validation

Would be wrong if applying the formula produced values outside what can be considered normal. Unclear whether a dedicated test is needed; mathematically it does not look like it will go very strange — proceed.

## Consequences

- `soil.py` must implement ρgD·cos(θ)+α (not base/cos); provenance sets `metzger_slope_factor` to this rule, not `deferred`.
- Planner limit still compares against this resistance scalar (`D-5cfa`); `dust_planner_limit_units` remains deferred until the input form locks units/UX.
- S14 dust row must name β = cos(θ), product LDSM, Apollo constants, and non-lofting label.
