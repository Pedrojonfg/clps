---
id: D-20261114-pj-bf69
title: "PSR is an initial impossible-site check; other related maps stay out"
date: 2026-11-14T15:59:06Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-d4ce
concepts: [hazard proxy, minima and feasibility, related site hazards]
supersedes: []
relates: [D-20261114-pj-5cfa, D-20261114-pj-050d, D-20261114-pj-f369, D-20261114-pj-b8d3]
ai: options+critique
---
# PSR is an initial impossible-site check; other related maps stay out

## Context

Related surface hazards in scope (`D-20261114-pj-b8d3`, `D-20261114-pj-41fa`) include slope, roughness and PSR beside temperature and the soil-resistance dust slot. PGDA publishes `LPSR_80S_20MPP_ADJ`, slope, roughness and Diviner rock abundance. Slope is already in the dust resistance term (`D-050d`). Hour-specific Sun and Earth come from the horizon mask (`D-f369`). PSR marks topographic permanent shadow, not a chosen date and hour.

## Framing

PSR gates the user early with a plain impossible-site message. The engine still runs the rest of the hazard and score path for optimization. No extra score terms for roughness, rock abundance or PGDA 69 averages in v1.

## Options considered

1. **A — PSR as a score minimum (layer 0)**: assumes PSR is another fail-closed gate in the score; consequence: overlaps Sun minima at most hours.
2. **B — PSR as an initial check only, full pipeline anyway**: assumes the planner needs an immediate “cannot land here” and search still needs downstream numbers; consequence: PSR is not a separate score term.
3. **C — PSR plus roughness and rock as score terms**: assumes static maps need their own weights; consequence: more planner limits and provenance without conversions decided in P13.
4. **D — PGDA 69 averages in the score**: assumes long-term illumination substitutes for site×time geometry; consequence: contradicts instant visibility (`D-f369`).

## Decision

**B.** PSR initial check with an impossible-site message; compute temperature, resistance and the rest anyway for optimization. Rock abundance, PGDA roughness and PGDA 69 stay out of the model in v1.

## Rationale

I would simply use PSR as an initial check so that if someone wants to land there they are told right away that the site is impossible. I suppose we compute everything else anyway because it will be needed for the optimization process. Nothing more in the model.

## Checks raised

- PSR at 20 m may disagree with a sub-site mask at finer DEM → kept B; message cites PSR product, mask cites its schedule (`D-f369`).
- An “impossible” PSR site may already fail Sun minima → kept B; PSR check is an explicit early explanation, not a second score formula term.
- Full pipeline under PSR costs compute in search → kept B; pj requires it for optimization.
- Discarded maps might still matter → pj falsification: unlikely per the literature; kept out until a conversion is recorded.

## Values

| Name | Value | Notes |
|------|-------|-------|
| psr_role | initial_site_viability_check | Not a separate score term |
| psr_product | LPSR_80S_20MPP_ADJ | PGDA; cite in provenance |
| psr_on_psr_pixel | impossible_site_message | User told the site is not viable for landing |
| psr_compute_full_pipeline | true | Still run hazards and score for optimization |
| score_roughness_pgda | out_v1 | `D-050d` |
| score_rock_abundance | out_v1 | `D-050d` |
| score_pgda69_averages | out_v1 | Context only if shown elsewhere; not in hazard model |
| related_hazards_extra | none_v1 | Settles open “as modeled” items beyond temp + resistance |

## Expected behavior and validation

The choice would be wrong if the discarded factors were very relevant. That does not seem probable according to the scientific literature.

## Consequences

- UI or API returns early PSR rejection before or beside the score, with a clear label.
- Search and deep optimization may still evaluate non-PSR fields on PSR-labelled cells if the implementation needs a full vector; provenance states PSR status.
- No layer-0 limit for roughness or rock unless a later decision adds them.