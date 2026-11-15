---
id: D-20261115-pj-7227
title: "Feasible map colors use absolute RYG gradient; clamp above ceiling to green"
date: 2026-11-15T10:50:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-33ca
concepts: [absolute score color scale]
supersedes: []
relates: [D-20261115-pj-8acb, D-20261115-pj-48ee]
ai: options+critique
---
# Feasible map colors use absolute RYG gradient; clamp above ceiling to green

## Context

Layer-1 feasible companion/UI scores live roughly in 0…~1.4 under β and uplift cap (`D-48ee`). pj rejected stretching each query’s min–max so a weak neighbourhood would look green.

## Framing

Absolute scale tied to how scores usually move; continuous gradient (not three bins); defensive clamp for out-of-range values.

## Options considered

1. **A — Stretch colors to this query’s min–max**: assumes local contrast matters most; consequence: all-bad searches look “good.”
2. **B — Absolute continuous RYG from ~0 (red) to ceiling (green); values above ceiling clamp to green**: pj's proposal.
3. **C — Discrete three-color bins only**: assumes fewer stops are clearer; consequence: pj rejected in favour of a moving gradient.

## Decision

**B.**

## Rationale

Green near the ceiling, red near zero; better → greener, worse → redder. Nothing more complicated. Code must clamp surprises (e.g. 2) to green so the app does not break.

## Checks raised

- Empirical probe for stops → optional; formula already bounds typical feasible scores. Exact mid-stop (yellow anchor) may be chosen in Build as engineering under this absolute rule; if a named threshold becomes a claim, record it.

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_feasible_scale | absolute_continuous_ryg | Not per-query min–max stretch |
| region_map_gradient_low | near_zero_feasible | Red end |
| region_map_gradient_high | score_ceiling | Green end; ~1.4 under current formula / uplift cap |
| region_map_above_ceiling | clamp_to_green | No crash, no NaN color |

## Expected behavior and validation

Wrong if out-of-range values crash or leave the scale; clamp to green handles that.

## Consequences

- Infeasible coloring stays under `D-8acb` (black), not this gradient.
- If the score formula’s ceiling changes, update the green anchor to match.
