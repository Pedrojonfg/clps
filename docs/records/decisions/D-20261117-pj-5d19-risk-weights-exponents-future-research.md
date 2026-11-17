---
id: D-20261117-pj-5d19
title: "Per-factor risk weights (exponents on the risk product): not in v1, research line"
date: 2026-11-17T20:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: method & validation
task: none
concepts: [risk product, severity weights, risk appetite]
supersedes: []
relates: [D-20261114-pj-7520, D-20261114-pj-de42, D-20261117-pj-7b2d]
ai: options+critique
---
# Per-factor risk weights (exponents on the risk product): not in v1, research line

## Context

Layer 1 risk is `R = ∏ Φ(slack_i / σ_i)` (`D-7520`): all factors weigh the same. pj asked whether companies accept
more risk in some factors than in others, and whether equal weighting is right.

## Framing

Two things look like weights but are not. **σ_i** is how well the metric is known (mask, model and timing error),
not how much it matters. **Risk appetite** already enters through the limits the user sets in the needs (a looser
`max_no_earth_h` is a tolerance). What the product does not express is **severity**: a flat battery ends the
mission, a gap without Earth loses data, dust degrades. Today every failure counts as mission-ending.

## Options considered

1. **A — Keep equal weights (v1)**: consequence: a tolerable failure still multiplies `R`; simple, no new inputs.
2. **B — Exponents** `R = ∏ p_i^{w_i}`, `w_i ∈ [0, 1]` (0 ignores the factor, 1 is today): consequence: one
   advanced input per factor, defaults 1, and nothing to set the values from yet.
3. **C — Severity classes** (terminal / degrading), fixed per factor: consequence: classification decided by us,
   not by the mission.

## Decision

**A for v1.** B and C are recorded as a research line, not implemented.

## Rationale

No data to set the weights, and the effect is easier to see after the pre-search tuning pass. Keeping σ (knowledge)
and `w` (importance) separate is the one thing to preserve if this is reopened.

## Criteria for change

Reopen if, in the tuning pass of `D-7520`/`D-6ce5`, a single factor dominates the ranking among feasible sites,
or if real mission requirements show that users set a factor's limit loosely only to avoid it zeroing the score
while still wanting it to weigh less in the ranking.

## Consequences

- None in v1. Option B would add per-factor weights to `needs` and an exponent in `_layer1_score`.
