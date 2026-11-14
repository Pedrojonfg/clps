---
id: D-20261114-pj-8764
title: "SurfaceHazardProvider returns per-hour fields plus provenance"
date: 2026-11-14T16:47:29Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: contracts
task: T-20261114-pj-d4ce
concepts: [provenance, layer-B in the score]
supersedes: []
relates: [D-20261114-pj-9e53, D-20261114-pj-41a2, D-20261114-pj-050d, D-20261114-pj-bf69, D-20261114-pj-5cfa]
ai: recommended
---
# SurfaceHazardProvider returns per-hour fields plus provenance

## Context

`D-20261114-pj-9e53` defines `SurfaceHazardProvider.hazards(site, times) -> dict` without field names. P13 locked temperature (`D-20261114-pj-41a2`), soil resistance (`D-20261114-pj-050d`), layer-0 limits (`D-20261114-pj-5cfa`) and PSR precheck (`D-20261114-pj-bf69`). S5 must implement against a stable shape.

## Framing

One row per hour with typed scalars the score consumes, plus provenance for each quantity.

## Options considered

1. **A — Per hour: temperature_k, soil_resistance, slope_deg, psr flag and message, nested provenance**
2. **B — Only temperature_k and soil_resistance; other facts only in provenance text**
3. **C — Replace dict with a HazardSample dataclass**

## Decision

**A.**

## Rationale

Accepted the recommendation: per-hour dict with temperature, soil resistance, slope, PSR, and provenance blocks.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| hazard_provider_shape | per_hour_list_of_dicts | Same length as `times` |
| hazard_field_temperature_k | required | Climatology kelvin; `D-20261114-pj-41a2` |
| hazard_field_soil_resistance | required | Metzger resistance proxy; `D-20261114-pj-050d` |
| hazard_field_slope_deg | required | PGDA LDSM used in resistance term |
| hazard_field_psr | required | `{in_psr: bool, message: str | null}`; `D-20261114-pj-bf69` |
| hazard_field_provenance | required | Nested object per quantity: product ids, season, time bin, fill rule, labels |
| hazard_provider_psr_still_computes | true | Full series even when `in_psr` is true |

## Expected behavior and validation

S4 score tests can assert field presence and provenance keys without parsing free text.

## Consequences

- Implement `lunar_eval/hazards/` to return option A before S5 wires into score.
- `providers.py` may gain a typed dataclass later; the contract for callers is option A until superseded.