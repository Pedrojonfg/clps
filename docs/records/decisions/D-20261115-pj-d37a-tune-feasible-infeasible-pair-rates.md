---
id: D-20261115-pj-d37a
title: "Tune experiment: separate feasible and infeasible pair-inversion rates"
date: 2026-11-15T07:48:34Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-d567
concepts: [feasible pair set, mission templates, Site01 windows]
supersedes: []
relates: [D-20261115-pj-7c70, D-20261114-pj-6ce5, D-20261114-pj-5577]
ai: options+critique
---
# Tune experiment: separate feasible and infeasible pair-inversion rates

## Context

`D-20261115-pj-7c70` accepts the provisional β / uplift when the risk-order inversion rate sits in 2–40%, and reopens outside that band. That rate is undefined until the comparison universe is fixed. Local search ranks both feasible and infeasible candidates with the same R×bonus companion (`D-20261114-pj-5577`). Inputs named in `D-20261114-pj-6ce5` include Site01 windows and mission templates.

## Framing

Measure the tune gate on the regimes search actually ranks, without pooling them into one percentage that could hide a failure mode.

## Options considered

1. **A — Single pooled rate** over feasible and infeasible pairs.
2. **B — Two rates, same procedure, measured separately** (feasible pairs vs infeasible pairs) on what is already computable; if volume is too thin for a serious test, report that and decide whether to compute more.
3. **C — Feasible pairs only** for the tune gate.

## Decision

**B.**

## Rationale

pj (2026-11-15): We should run two tests that work the same way but are measured separately — one for feasibles and one for non-feasibles — using what we already have computed as the base. At the end of the day both use a very similar model, if not the same, and because the cases are so different the results may differ a lot, not just by chance; for example among non-feasibles the probabilities are lower. I think that with the beta cap it should work well in all cases, but just in case I would separate them in the test and look at both results.

## Checks raised

- Site01 × templates × week windows can fill many temporal pairs; spatial pairs need a cap sample → noted; sufficiency is checked when the sweep is assembled.
- Cap 1 km is on disk (~290k masks) but not yet a scored battery → expanding compute is a follow-up only if N is reported thin.

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_layer1_tune_rate_split | feasible_and_infeasible_separate | Two percentages vs `D-7c70` bands |
| score_layer1_tune_pair_procedure | same_for_both_splits | Same inversion definition; different pools |
| score_layer1_tune_base_inputs | site01_windows; mission_templates; aggregate_golden_if_present; expand_if_N_thin | Cite `D-6ce5`; expansion only after an insufficiency report |
| score_layer1_tune_insufficiency_reporter | session_ai_with_repo_access | pj: “tell me” means the AI in the decision-flow session (file access), not a solo note to himself |

## Expected behavior and validation

pj (2026-11-15): That we did not have enough computed material for a serious test; in that case the AI in this decision-flow session (which has access to the files) must say so, and on that basis we decide whether to compute more or not. (pj clarified: “tell me” is addressed to the AI, not spoken as if alone.)

## Consequences

- The sweep reports two inversion rates (feasible pool, infeasible pool), each compared to `D-7c70`.
- Reopen if either rate is outside the band (unless a later decision says otherwise).
- Before trusting the numbers, the builder/AI reports pair counts per pool; thin N → stop and ask whether to sample the 1 km cap or add windows.
