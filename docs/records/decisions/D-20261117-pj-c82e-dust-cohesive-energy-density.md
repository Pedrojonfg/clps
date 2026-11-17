---
id: D-20261117-pj-c82e
title: "Dust proxy uses cohesive energy density (J/m³) for α and Metzger's ⟨D⟩, not Mohr-Coulomb cohesion"
date: 2026-11-17T21:45:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: method & validation
task: none
concepts: [hazard proxy, Metzger erosion, cohesive energy density]
supersedes: [D-20261115-pj-06cb]
relates: [D-20261114-pj-050d, D-20261117-pj-e3a7, D-20261114-pj-5cfa]
ai: options+critique
---
# Dust proxy uses cohesive energy density (J/m³) for α and Metzger's ⟨D⟩, not Mohr-Coulomb cohesion

## Context

A literature check for the dust σ (`D-e3a7`) read Metzger (2024), "Erosion rate of lunar soil under a landing
rocket", Part 1 (arXiv:2403.18583) and Part 2 (arXiv:2403.18584). The soil side of the relation is
`ρ_m g β ⟨D⟩ + α` in J/m³ with **α = cohesive energy density** (order 0.1–2 J/m³), which the paper says must not be
confused with the larger Mohr-Coulomb cohesion. `lunar_eval/hazards/soil.py` used `COHESION_PA = 500` (a
Mohr-Coulomb-type 0.1–1 kPa value), `MEAN_GRAIN_M = 70e-6` and ρ = 1500 kg/m³. That made α ~3 orders of magnitude
too large, so it swamped the grain term (0.17) and made the slope factor invisible. `D-06cb` kept the formula but
left these constants as "Apollo average". This record replaces only those constants; the β rule of `D-06cb`
(β = cos θ on the grain term, floor 0.05, θ from PGDA LDSM) stays.

## Decision

pj: change the value; it is a correction of a quantity, not a new design choice. Constants taken from the paper's
own lunar baseline, provisional:

## Values

| Name | Value | Notes |
|------|-------|-------|
| dust_alpha | 0.289 J/m³ | Cohesive energy density, Part 2 baseline at ρ = 1000 kg/m³. Replaces `COHESION_PA = 500`. |
| dust_rho_bulk | 1300 kg/m³ | Part 2 surface bulk density (soil model 1); verified range across its soil models 1100–1920. Replaces 1500. |
| dust_mean_D | 267 µm | ⟨D⟩ = 1.5 · D84, D84 = 2.3 · D50, D50 = 77.5 µm (Part 1 p. 11, read from the PDF). Replaces `MEAN_GRAIN_M = 70e-6`. |
| dust_mean_D_range | 1.1–2.0 · D84 (196–356 µm) | First to third quartile in Part 1. |
| dust_alpha_range | 0.11–1.72 J/m³ | Simulant analogs (JSC-Mars-1A / JSC-1A); lunar α rises exponentially with density, constant k only known within a factor of 3 (Part 2). |
| dust_flat_resistance | ≈ 0.85 J/m³ | `1300·1.62·267e-6 + 0.289`; the check value for tests. |
| dust_alpha_label | cohesive_energy_density_not_mohr_coulomb | Goes in provenance. |

## Inconsistency kept on purpose

α is taken at ρ = 1000 kg/m³ while the grain term uses ρ = 1300 kg/m³. α grows with density, so this slightly
understates α at 1300. Accepted for v1 (same baseline as the paper); revisit when the α(ρ) law is settled.

## Criteria for change

- Reopen when polar-specific soil properties or a calibrated α(ρ) law are published.
- Wrong if the slope term still has no visible effect after the change (the grain term is now ~0.56 of ~0.85 J/m³,
  so it should); a test asserts that 45° slope lowers the resistance by a clear margin.
- Planner limit units (`D-5cfa`, deferred) are now J/m³; the UI must say so.

## Consequences

- `soil.py` constants and `soil_provenance` (`soil_constants`, label) change; `tests/test_hazards.py` gets the
  flat value ≈ 0.85 and the slope assertion.
- `D-e3a7` computes the dust σ by propagating the verified ranges above, not the Apollo kPa ranges.
- Research brief with the evidence and the unverified items: kept in the session scratchpad, not in the repo.
