---
id: D-20261115-pj-7c70
title: "Tune gate: accept in 2–40% risk-order inversion band; reopen outside"
date: 2026-11-15T07:41:54Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-d567
concepts: [needs-adapted score, risk-order inversion, reopen vs retune]
supersedes: []
relates: [D-20261114-pj-6ce5, D-20261114-pj-7520, D-20261114-pj-52bd]
ai: options+critique
---
# Tune gate: accept in 2–40% risk-order inversion band; reopen outside

## Context

`D-20261114-pj-6ce5` left `score_layer1_tune_done` false until pj accepts β / uplift after a risk–bonus experiment on Site01 windows and mission templates. S6 is not green until that gate is met (`D-20261114-pj-52bd`). The experiment needs a recorded accept / reopen rule before the sweep runs.

## Framing

Close the pre-S6 tune gate with a defendable band on how often the bonus overturns risk order, without treating a reopen as an automatic β change.

## Options considered

1. **A — Cap-usage only**: assumes ranking inversions need not be measured for the gate; consequence: `tune_done` without looking at R-vs-score order.
2. **B — 2–40% inversion band**: inside → accept now (deeper review only if time left); outside (<2% or >40%) → reopen / rethink (does not imply moving β); assumes pj's intuitive thresholds suffice for today's gate.
3. **C — Formal study before any `tune_done`**: assumes provisional values cannot be accepted without a fixed scientific pass; consequence: S6 green waits on that study.

## Decision

**B.**

## Rationale

pj (2026-11-15): The two numbers I gave are what feels intuitive to me. Between 2% and 40% we do not review, or we leave it for later if there is time; if it is below 2% or above 40%, we review.

## Checks raised

- Middle band skips a more scientific pass for now → accepted; if time is left, reopen anyway for a more careful look.
- 2% / 40% are not yet measurable until the comparison universe is fixed → left to the next decision on this task.
- Residual `score_bonus_max_uplift` 0.10 (`D-7520`) vs 0.30 (`D-6ce5`) → not settled here; code already follows `D-6ce5`.

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_layer1_tune_inversion_low_pct | 2 | Below this → reopen / rethink |
| score_layer1_tune_inversion_high_pct | 40 | Above this → reopen / rethink |
| score_layer1_tune_accept_band_pct | 2_to_40 | Inclusive interior: accept provisional β/cap for the gate |
| score_layer1_tune_mid_band_deep_review | deferred_if_time | Not required for `tune_done` |
| score_layer1_tune_reopen_implies_beta_change | false | Reopen means rethink; β may stay |

## Expected behavior and validation

pj (2026-11-15): That my thresholds were badly set because of Moon-specific behaviour I do not know. In any case, if time is left we will reopen this anyway and perhaps then we can do a somewhat more scientific investigation.

## Consequences

- The sweep must report a risk-order inversion rate comparable to these bands.
- Inside the band after a valid sweep: pj may set `score_layer1_tune_done` true (separate accept decision with numbers in hand).
- Outside the band: new decide pass; do not silently edit β.
- Comparison pair universe still required before the rate is defined.
