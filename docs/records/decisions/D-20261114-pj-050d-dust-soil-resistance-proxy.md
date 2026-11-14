---
id: D-20261114-pj-050d
title: "Dust term is Apollo-average soil resistance with PGDA slope; rock and roughness out"
date: 2026-11-14T15:39:06Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: data & sources
task: T-20261114-pj-d4ce
concepts: [hazard proxy, layer-B in the score, provenance]
supersedes: []
relates: [D-20261114-pj-de42, D-20261114-pj-b8d3, D-20261114-pj-41a2]
ai: options+critique
---
# Dust term is Apollo-average soil resistance with PGDA slope; rock and roughness out

## Context

Layer B requires a dust-related hazard (`D-20261114-pj-b8d3`). No public site×time dust lofting field exists (`docs/resources.md`). LDEX measures a near-equatorial exospheric ejecta cloud, not landing-plume scour at the south pole. Metzger (2024) gives a lunar plume erosion relation whose soil side uses mean grain size, cohesion, bulk density and gravity; a slope factor was set to flat (factor 1) for horizontal terrain. PGDA slope (`LDSM`) is site-specific. Diviner rock abundance maps exposed rocks ~1–2 m, not grain-scale cohesion. PGDA roughness is terrain at tens to hundreds of metres, not grain-scale roughness height in the erosion relation.

## Framing

The hazard number is the soil resistance term from that physics line (Apollo-average grain and cohesion, lunar gravity), with site slope from PGDA once the slope substitution in Metzger’s relation is found. It is soil erodibility resistance, not a lofting rate without a defined engine. Rock abundance and PGDA roughness stay out until a published conversion exists.

## Options considered

1. **A — No dust number**: assumes the score can omit it; consequence: a dust limit cannot zero or rank.
2. **B — Three separate static maps**: assumes the planner sets limits in each unit; consequence: no single “dust” scalar.
3. **C — Weighted index of rock, slope and roughness**: assumes an unvalidated blend is honest; consequence: the index is not physical dust.
4. **D — Metzger soil-resistance side with Apollo-average soil, PGDA slope in the slope factor when known, rock and roughness out**: assumes slope is the only site-varying input with a formula slot; consequence: sites differ mainly by slope; grain and cohesion are Moon-wide constants until mapped.
5. **E — Full plume erosion rate with a chosen engine**: assumes a lander nozzle is part of the product question; consequence: the number is mission-specific, not site-only.

## Decision

**D.** Apollo-average soil resistance in the Metzger line, PGDA slope in the slope factor once investigated. Diviner rock abundance and PGDA roughness out. Label: soil resistance proxy, not dust lofting rate without an engine.

## Rationale

It is the best approximation we can make with the information we have. We will use D with slope and investigate how slope substitutes into the formula. The other two inputs we leave out because we do not have a clear proxy or evidence that they are important.

## Checks raised

- Slope factor formula not yet written → kept D; `dust_metzger_slope_factor` deferred to investigation.
- Without nozzle gas properties the result is resistance, not erosion rate → kept D; `dust_quantity_label` set to soil_resistance_proxy.
- Apollo-average soil does not vary by polar site except via slope → kept D; noted in Values.
- “No evidence they matter” is absence of conversion, not proof they are irrelevant → kept D; rock and roughness remain out until a conversion is recorded.

## Values

| Name | Value | Notes |
|------|-------|-------|
| dust_quantity | soil_resistance_proxy_metzger | Metzger (2024) soil-side resistance; not volumetric erosion rate without engine inputs |
| dust_quantity_label | soil_erodibility_resistance_not_lofting_rate | UI and provenance must use this; `D-3c91` |
| dust_soil_constants | apollo_average_grain_cohesion_bulk_density | Moon-wide until a polar soil map is decided |
| dust_slope_input | pgda_ldsm_degrees | Site-varying; enters Metzger slope factor when defined |
| dust_metzger_slope_factor | deferred — investigate substitution from PGDA slope into Metzger relation | Blocks site-varying dust numbers until set |
| dust_engine_inputs | out — no default nozzle in the hazard term | Full erosion rate needs ρ, v, A at the nozzle |
| dust_rock_abundance | out | No published conversion to Metzger soil parameters |
| dust_pgda_roughness | out | Terrain roughness ≠ grain-scale height in the relation |
| dust_ldex | out | Exospheric ejecta, not plume scour at the site |

## Expected behavior and validation

The same as usual: the choice would be wrong if there were factors we had not identified. Even so, it is the best approximation we can make with the information we have.

## Consequences

- S5 returns this scalar with full provenance: Apollo soil constants, PGDA slope product, deferred slope formula, and the honesty label.
- The score’s “dust” planner field compares against this resistance proxy until renamed in the UI if needed.
- `score_surface_as_minima` for dust is still open in this task queue.