---
id: D-20261114-pj-7520
title: "Layer-1 score: product risk Π Φ(slack/σ) plus capped bonus"
date: 2026-11-14T18:29:22Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-8138
concepts: [needs-adapted score, visibility series]
supersedes: [D-20261114-pj-de42]
relates: [D-20261114-pj-de42, D-20261114-pj-7af3, D-20261114-pj-f369, D-20261114-pj-41fa, D-20261114-pj-4ffe, D-20261114-pj-9e53]
ai: options+critique
---
# Layer-1 score: product risk Π Φ(slack/σ) plus capped bonus

## Context

`D-de42` deferred `score_layer1_quantity` and `score_layer_combination`. Among feasible site×times, pj wants risk to dominate but to credit noticeably more Sun or Earth when accepting slightly more risk. `D-7af3` adds a layer-0 gate on `longest_lit_h`. The interim code used minimum normalized slack only. This record locks layer-1 for S4 v1 and the S3 aggregates the bonus needs.

## Framing

A defendable scalar score among feasible options: joint survival probability under hour-scale uncertainty, plus a small, bounded upside from surplus illumination.

## Options considered

1. **A — Min normalized slack only**: assumes slack is enough; consequence: ignores bonus for extra lit hours (rejected for v1).
2. **B — min_i Φ(slack_i/σ_i)**: assumes the weakest term dominates; consequence: no union-of-failure modes.
3. **C — Product Π_i Φ(slack_i/σ_i) with independent failure modes, plus weighted bonus**: assumes errors on distinct aggregates do not share the same draw (v1); consequence: needs σ table and a bonus cap so upside cannot swamp risk.
4. **D — Defer layer-1 until a full error model exists**: consequence: blocks the intended prob + bonus shape.

## Decision

**C.**

## Rationale

Option 3 from the brief (probabilistic + bonus). pj chose product aggregation over the minimum: combine Gaussian survival terms as a union under independence, not as a sum of failure probabilities. Bonus uses both interval excesses and scalar hour counts, with interval terms at about one tenth the weight of scalars because marginal utility of longest_* is near zero once minima are met. pj could not name falsification cases; proposes setting limits on the risk–bonus ratio so the bonus cannot eat total risk, and tuning via experiment.

## Checks raised

- Summing failure probabilities is unbounded → use product of survivals `R = ∏ p_i`.
- Interval and scalar metrics may correlate → pj: measured differently so v1 treats modes as independent; revisit if scores look optimistic.
- Bonus could dominate risk → cap enforced (Values); experiment to set `β` and ratio limit.
- No named falsification → record pj's honesty; safeguard is the cap plus future score distribution checks.

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_layer1_quantity | product_phi_slack_over_sigma | Settles `D-de42` deferral for v1 |
| score_layer1_risk_R | ∏_i Φ(slack_i / σ_i) | i over night, no_earth, lit (if min_continuous_lit_h > 0), and any future hour-slack minima |
| score_failure_independence_v1 | independent_modes_assumed | Correlation interval↔scalar not modeled in v1 |
| score_slack_night | max_night_h − longest_night_h | Same series as layer-0 |
| score_slack_no_earth | max_no_earth_h − longest_no_earth_h | |
| score_slack_lit | longest_lit_h − min_continuous_lit_h | Only when min_continuous_lit_h > 0 |
| score_sigma_night_h | 5 | `D-f369` / `D-41fa` mask aggregate tolerance |
| score_sigma_lit_h | 5 | Same schedule error budget on longest lit |
| score_sigma_no_earth_h | 1 | v1 provisional kernel timing on Earth visibility |
| score_sigma_hourly_count_h | 0.5 | v1 provisional on hourly above-threshold counts |
| score_bonus_interval_weight | 0.1 | Relative to scalar branch |
| score_bonus_scalar_weight | 1.0 | |
| score_bonus_scalar_fields | hours_sun_above_threshold; hours_earth_above_threshold | New S3 outputs; hourly, same thresholds as series |
| score_bonus_scalar_normalize | divide by window length in hours | Each in [0, 1] before weighting |
| score_bonus_interval_fields | normalized excess beyond minima on night, no_earth, lit slacks | Only when corresponding need is active |
| score_bonus_B | weighted mean of interval (×0.1) and scalar (×1.0) terms | Clip to [0, 1] before mixing |
| score_layer1_combine | R * (1 + β * B) | β small; bonus is multiplicative uplift on risk core |
| score_bonus_beta | 0.15 | v1 default until experiment; provenance names it |
| score_bonus_max_uplift | 0.10 | Enforce (score − R) / R ≤ 0.10 after combine; bonus cannot add more than 10% relative to R |
| score_layer_combination | risk_multiplicative_with_capped_bonus | Settles `D-de42` deferral for v1 |
| score_provenance_sigmas | list score_sigma_* used | Every scored payload cites σ sources by decision ID |
| score_layer1_tune | experiment_ratio_risk_bonus | pj: adjust β and caps if feasible sites cluster or bonus dominates in hand scenarios |

## Expected behavior and validation

pj could not specify what would prove this choice wrong without running cases. Wrong if independence is badly violated and R is systematically too high, or if the cap is left too loose so bonus masks a weak risk term; address by the ratio cap, hand scenarios under `D-41fa` Z, and an experiment that sweeps β/ratio on Site01 windows. σ values are rough v1 from `D-f369` and provisional ephemeris/hourly values; replacing σ is a record or value update, not a formula change.

## Consequences

- `lunar_eval/visibility.py` adds hourly counts for scalar bonus; `lunar_eval/score.py` implements R, B, cap, provenance.
- Supersedes the interim `min(slack/max)` implementation for feasible scores.
- Layer-2 hazard weights remain `D-de42` layer-2 / S5; `score_infeasible_signal` still for S6.