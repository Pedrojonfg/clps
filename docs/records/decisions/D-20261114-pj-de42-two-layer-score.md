---
id: D-20261114-pj-de42
title: "Two-layer score: fail-closed zero, then assurance, then weighted factors"
date: 2026-11-14T14:07:03Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-b63a
concepts: [needs-adapted score, minima and feasibility]
supersedes: [D-20261111-pj-60ab]
relates: [D-20261114-pj-9f04, D-20261114-pj-f369, D-20261114-pj-b8d3]
ai: options+critique
---
# Two-layer score: fail-closed zero, then assurance, then weighted factors

## Context

The product question (`D-20261111-pj-60ab`) requires a needs-adapted score that is zero when minima fail, then search toward the nearest feasible site×time. `score_formula` was deferred there. This record supersedes `D-60ab` only to settle that value; the product question itself is restated unchanged. Visibility series (longest night, longest gap without Earth, bridged lit periods, user light fraction and shadow bridge) are defined in `D-20261114-pj-f369`. Layer B (temperature, dust) is in the product (`D-20261114-pj-b8d3`) but models are still open (plan P13). Phase 0 of the implementation plan locks this formula so S4, local search and the region map share one rule.

## Framing

Rank site×time under the planner's own thresholds. Do not rank against a global best case. Prefer giving infeasible news over hiding it.

## Options considered

1. **A — Binary feasible / infeasible**: assumes only the crossing of minima matters; consequence: no ranking among feasible sites; search has no slope.
2. **B — Normalize against the best site×time in range**: assumes the best in-range case is the reference; consequence: a good site in a poor region looks excellent; a harsh mission never reaches 1.
3. **C — Margin to each threshold only**: assumes slack (hours, kelvin, …) is the whole score; consequence: ranking exists; remaining factors enter only if they are already thresholds.
4. **D — P(remain feasible) with an explicit error model**: assumes a distribution over mask/kernel error; consequence: needs that density. The records have a 5 h output tolerance (`D-f369`), not a density.
5. **E — Two-layer: zero if a minimum fails; among feasible, rank first by not approaching infeasibility; then a simple weighted combination of remaining factors**: assumes assurance of basics outranks idle surplus and extra comfort; consequence: matches `D-60ab` fail-closed zero; combination rule and infeasible-search signal still to set.

## Decision

**E.** Two-layer score: zero if a minimum fails; among feasible sites, the first layer ranks by not approaching a return to infeasible; the second layer weights remaining factors (temperature, dust, extra hours, and similar) with a simple rule such as a sum.

## Rationale

Assuming the engine exists — that is another scope. It gives the maxima (hours without Sun, without Earth) easily; pandas just filters what is met. The question is how we define the score. Comparing it with the best possible scenario is cheating, because a mission may have very tough requirements, for example needing many hours with everything active. If any of the things is not met, the score is zero. The first layer is probabilistic: we do not care that the situation is perfect, but that there is a very low probability that something goes wrong. It looks, in the things that are not deterministic, at the probability that something shifted a bit and you go to zero. The second layer is how we weight each concrete factor (temperature, dust, extra hours); a sum or similar is enough. What matters most is that the thing does not go wrong, not that everything is perfect. You do not need a lot of idle capacity; you need your basic needs to be assured.

## Checks raised

- `D-60ab` nearest-feasible search among all-zero scores needs a direction → kept E; signal among infeasible points deferred (see Values).
- First layer called both probabilistic and slack; no error density is recorded (`D-f369` has a 5 h tolerance) → kept E; layer-1 quantity deferred.
- Second layer can wash out the first unless the combination rule protects it → kept E; combination deferred.
- Planner temperature/dust limits may be minima (fail-closed) or second-layer preferences → kept E; deferred to P13.
- Provenance: each breakdown term must name its series or hazard → kept E; required by `D-3c91`, restated in Consequences.

## Values

| Name | Value | Notes |
|------|-------|-------|
| product_question | scored_evaluation_under_constraints | Restated from `D-60ab`; unchanged |
| score_on_minima_fail | zero_then_search_nearest_feasible | Restated from `D-60ab`; layer 0 is the zero; search is the follow-up |
| local_neighborhood_scan | required | Restated from `D-60ab` |
| deep_search_mode | required_intent | Restated from `D-60ab` |
| visualization_set | deferred — scope / presentation | Restated from `D-60ab` |
| score_formula | two_layer_zero_then_assurance_then_weights | Settles the deferred formula in `D-60ab` |
| score_reference | not_global_best | Do not normalize against the best site×time |
| score_objective | assure_basic_needs | Idle surplus is not the objective |
| score_layer1 | assurance_against_returning_to_infeasible | pj: low chance that a small shift drops the case to zero |
| score_layer1_quantity | deferred — hours of slack vs P(remain feasible); lock when S4 is specified, once it is decided whether an error distribution is adopted | |
| score_layer2 | weighted_remaining_factors | Temperature, dust, extra hours; simple combination (e.g. a sum) |
| score_layer_combination | deferred — how layer 1 and 2 combine so layer 2 cannot wash out assurance; lock when S4 is specified | |
| score_infeasible_signal | deferred — signal the search uses among all-zero scores to walk toward feasible (`D-60ab`); lock with S6 | |
| score_surface_as_minima | temperature_and_dust_fail_close_layer_0 | Settled by `D-20261114-pj-5cfa` |

## Expected behavior and validation

The problem would be cases where all the scores are so low they would not let you see the differences. In that sense it is better to be realistic. If a mission is extremely tough because you need very specific conditions, there is no site that can guarantee them. Being something professional, it is better that it gives you the bad news than that it hides bad things. If all the results moved in a range so high or so low that they would not allow being scaled, we can fix that with scaling.

## Consequences

- S4 implements this shape with a neutral hazard term until P13. The UI shows the rule and a breakdown; every term names its series or hazard (`D-3c91`).
- Supersedes `D-20261111-pj-60ab` so `score_formula` is not both deferred and set. The product question and the fail-closed-then-search behaviour are restated, not replaced.
- Layer-1 quantity, layer combination, infeasible-search signal, and surface-limits-as-minima are explicit deferred values, not silent defaults.
