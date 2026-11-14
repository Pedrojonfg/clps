---
id: T-20261114-pj-8138
title: "Specify S3 visibility series and S4 score for real-data build"
kind: decide
owner: pj
branch: scope/ops-skeleton
created: 2026-11-14T17:42:21Z
stage: done
relates: [T-20261114-pj-b63a, T-20261114-pj-9e03, D-20261114-pj-de42]
---
# Specify S3 visibility series and S4 score for real-data build

## Goal

Done means: every value S3 and S4 still need for search, `/site`, and success X/Y/Z (`D-41fa`) is recorded or explicitly deferred with a working default pj defends. No implementation in this task unless pj asks later. Origin: pj `/decision-flow para s3 y s4` after S8 scope.

## Triage

- Own/advise parts: visibility metrics and validation (own, method & validation); score layer-0 minima and layer-1 quantity (own, method & validation); API series payload extras (advise, contracts).
- Plumbing: existing `lunar_eval/visibility.py` and `score.py`; tests in `tests/test_visibility.py`, `tests/test_score.py`, `tests/test_dem_site.py`.

## Pending checkpoint

None.

## Orientation

- Concepts: visibility series (prerequisite, `D-f369` `D-9e53`); disc fraction above mask (core); shadow bridging (core); four visibility cases (core, `D-60ab`); needs-adapted score (core, `D-de42`); minima and feasibility (core); layer-1 assurance quantity (hazard — probabilistic wording vs code); success X/Y/Z (hazard, `D-41fa`).
- Facts: `visibility.series()` returns fractions + longest night / no-earth / lit / `any_both`; UI derives four cases from thresholds. `score()` gates on night, no_earth, require_both, surface layer-0; feasible scores use `min(slack/threshold)` with layer2=0. `D-de42` defers `score_layer1_quantity`, `score_layer_combination`, `score_infeasible_signal`. E2E on 8 hours Site01 exists; no golden week series test yet.
- pj retrieval: smooth positive el can still be dark because terrain along the ray is higher than the smooth horizon (south pole regime).
- pj approach (2026-11-14): layer-1 should go beyond min slack — risk primary but allow small extra risk for much more Sun/Earth; uncertainty/variability of estimates belongs in a ledger pass (non-linear). `longest_lit_h` must be a score minimum. No golden week oracle v1; wants rationale on validation choice.
- Decisions surfaced: longest_lit layer-0; score_layer1 defer vs spec; validation scope without golden series

## Decisions

- D-20261114-pj-7af3 — Layer-0 minimum on longest continuous lit period (min_continuous_lit_h)
- D-20261114-pj-7520 — Layer-1 score: product risk Π Φ(slack/σ) plus capped bonus
- D-20261114-pj-1a46 — S3/S4 validation without a committed golden week series (superseded on aggregates by D-beb5)
- D-20261114-pj-6ce5 — Provisional bonus cap: uplift at most 30% of R; tune before S6
- D-20261114-pj-beb5 — Golden aggregate fixture for Site01 week 2027-01-01–07

## Auto decisions

| Choice | Reason |
|--------|--------|
| failing breakdown tag `lit` | hygiene; matches night / no_earth / both |
| score_bonus_beta | 0.15 v1 default; pj asked experiment to tune |
| score_bonus_max_uplift | superseded: D-6ce5 sets 0.30 |

## Fog

## Out of scope

- Hourly four-case flags in API JSON.
- Layer-2 hazard weights in the scalar score (S5).

## Build

Decide only.

## Audit

## Detours

- 2026-11-14: pj asked to lock bonus/risk ratio (β, cap), when to tune, ELI10 approval, and reopen golden set (`D-1a46`).