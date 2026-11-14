---
id: D-20261114-pj-52bd
title: "S6 validation: synthetic tests plus one Site01 search E2E"
date: 2026-11-14T19:38:54Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-03a6
concepts: [local neighborhood search, nearest feasible time]
supersedes: []
relates: [D-20261114-pj-6ce5, D-20261114-pj-beb5, D-20261114-pj-aa58, D-20261114-pj-41fa]
ai: options+critique
---
# S6 validation: synthetic tests plus one Site01 search E2E

## Context

S6 needs a recorded “done / green” bar before trusting local search in the demo. Bonus tuning remains a separate gate (`D-6ce5`). Site01 and the 2027-01-01–07 window already exist for engine tests (`D-aa58`, `D-beb5`).

## Framing

Prefer automated checks pj trusts, without adding verification layers that do not buy confidence.

## Options considered

1. **A — Synthetic tests only**.
2. **B — Synthetics plus one Site01 search E2E**.
3. **C — Synthetics plus mandatory manual leaderboard review as a gate**.

## Decision

**B.**

## Rationale

Synthetic tests at first; not necessary another verification layer, with enough confidence in synthetics — except that inefficient tests would make the choice wrong. On confirm, add one Site01 E2E; setup is not that much.

## Checks raised

- Synthetics can miss real mask/sky wiring → Site01 E2E added.
- `D-6ce5` tune-before-green stays a separate gate, not a third validation layer of search logic.
- Manual leaderboard gate declined.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s6_validation_primary | synthetic_unit_tests | Slide, radius, always-scan, dual score, hazard gaps, ranking |
| s6_validation_e2e | one_site01_local_search | Real kernels/mask when data present; skip or soft-fail in CI without data |
| s6_validation_manual_gate | not_required | Leaderboard may be smoked in UI tests later; not a green gate |
| s6_green_also_requires | score_layer1_tune_when_met | Cite `D-6ce5`; not redefined here |

## Expected behavior and validation

Wrong if the tests are not efficient for checking the behavior. A second heavy verification layer is not required beyond synthetics + one Site01 E2E; confidence rests there plus the existing bonus-tune gate.

## Consequences

- Extend `tests/test_search.py` (and/or a dem-gated E2E) to cover `D-9cc5`, `D-72bc`, `D-5577`, `D-f57e`.
- Site01 E2E asserts local search returns a leaderboard-shaped result on the production test window when data exists.
- S6 is not “green” until `D-6ce5` tune milestone is met, even if these tests pass.
