---
id: D-20261114-pj-5577
title: "Infeasible search ranks by R×bonus; UI shows zero plus impossible score"
date: 2026-11-14T19:06:54Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-03a6
concepts: [infeasible-search signal, needs-adapted score]
supersedes: []
relates: [D-20261114-pj-de42, D-20261114-pj-7520, D-20261114-pj-6ce5, D-20261111-pj-60ab]
ai: options+critique
---
# Infeasible search ranks by R×bonus; UI shows zero plus impossible score

## Context

`D-de42` deferred `score_infeasible_signal`: the direction local search uses among site×times that all fail layer-0 (score zero). S6 needs that signal. Layer-1 among feasibles is `R × (1 + β·B)` with a cap (`D-7520`, `D-6ce5`). The product question requires nearest-feasible search when minima fail (`D-60ab`).

## Framing

Give search a continuous ordering under the fail-closed gate without pretending those points meet the planner's minima.

## Options considered

1. **A — No ordering among zeros**: search stops or returns none without a rank.
2. **B — Same probabilistic R (Φ of slacks, including negative) as the ranking key; clear infeasible marking**: continuous walk toward feasibility.
3. **C — Hour excesses past thresholds without Φ**.
4. **D — Cheap single-metric heuristic (e.g. longest night only)**.

## Decision

**B**, with ranking scalar **R×bonus** (same combine rules as layer-1). User-facing readout is dual: official **zero** when minima fail, plus a separate **“inside the impossible”** score from that scalar. UI must make the pair easy to understand.

## Rationale

Use the same probabilistic model as for cases that work; keep the candidate with the highest probability of working, marking very clearly that it may still fail the minima. Confirmed R×bonus. Show a zero and also a score “inside the impossible.” Exhaustive UI work will be needed so this is easy to understand; there is user value in that signal.

## Checks raised

- Cost may exceed the modest benefit of ranking zeros → accepted as falsification; prefer ranking over candidates already evaluated in that search, without an extra expensive sweep.
- Bonus among infeasibles could mis-order → kept R×bonus at pj's confirm; same β and uplift cap as feasible layer-1 (`D-6ce5`).
- Dual readout needs careful UI → accepted; pj wants the user value and expects thorough UI work.

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_infeasible_signal | layer1_R_times_bonus | Settles `D-de42` deferral; same Φ/σ, β, uplift cap as `D-7520` / `D-6ce5`, including negative slacks |
| score_on_minima_fail_display | zero | Restates fail-closed public score (`D-60ab`) |
| score_infeasible_companion | R_times_bonus_inside_impossible | Separate field for ranking and for the “inside the impossible” readout |
| score_infeasible_ui | dual_zero_plus_impossible_score | Feasible flag false; clear copy that minima are not met |
| score_infeasible_rank_scope | already_evaluated_candidates_only | Avoids an extra compute sweep; honors cost falsification |

## Expected behavior and validation

Wrong if it costs too much time/compute for a benefit that is not that large.

## Consequences

- S6 ranks infeasible candidates by the companion scalar, never treating them as feasible.
- `score()` / search payload expose both zero (or equivalent fail-closed score) and the companion when layer-0 fails.
- UI work for the dual readout is in scope for making S6 understandable; not a silent detail.
- Supersedes only the *deferral* of `score_infeasible_signal` in `D-de42`; does not reopen the feasible layer-1 formula.
