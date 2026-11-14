---
id: D-20261114-pj-6ce5
title: "Provisional bonus cap: uplift at most 30% of R; tune before S6"
date: 2026-11-14T18:38:12Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-8138
concepts: [needs-adapted score]
supersedes: []
relates: [D-20261114-pj-7520, D-20261114-pj-de42, D-20261114-pj-41fa]
ai: options+critique
---
# Provisional bonus cap: uplift at most 30% of R; tune before S6

## Context

`D-7520` set `score_bonus_max_uplift` to 0.10 and `score_bonus_beta` to 0.15 as v1 defaults, with `score_layer1_tune` named but no milestone. pj wants the bonus to matter more than a 10% cap allows, without masking risk, and to run an experiment later to adjust `β` and possibly the cap.

## Framing

Lock the risk–bonus balance for implementation while leaving room to tune before search consumes the score.

## Options considered

1. **A — Keep 10% cap**: assumes bonus is cosmetic only; consequence: pj rejects; weak differentiation among feasible sites.
2. **B — 30% max uplift on R, β stays 0.15 provisional until experiment**: assumes bonus can shift rankings but cap prevents dominating weak R; consequence: needs a scheduled tune pass.
3. **C — Fix β now with no cap**: assumes pj can pick final β without data; consequence: contradicts pj’s experiment intent.
4. **When to tune:** (i) immediately after S4 lands on Site01 week, (ii) before local search (S6) is green, (iii) only at Sunday freeze, (iv) only after aggregate golden fails.

## Decision

**B** for the cap and provisional β. **Tune milestone (ii):** run the risk–bonus experiment and record updated `β` / cap if needed **before S6 local search is green**, because search ranks on the same scalar.

## Rationale

pj (2026-11-14): cap bonus impact at 30% of R so the bonus has real weight but still cannot fully disguise bad risk. Provisional until an experiment; pj asked when — implementation plan makes S6 the first consumer that cares about score spread among feasible sites, so tune after S4+bonus code exists and before trusting S6.

## Checks raised

- 30% may still let a weak R look “middling” → accepted with experiment on Site01 windows and hand Z cases; tighten cap in a follow-up value if needed.
- β=0.15 unchanged → provisional; experiment may lower or raise β within the 30% uplift bound.

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_bonus_max_uplift | 0.30 | Enforce (score − R) / R ≤ 0.30 after `R * (1 + β * B)` |
| score_bonus_beta | 0.15 | Provisional until `score_layer1_tune_done` |
| score_layer1_tune_status | provisional | |
| score_layer1_tune_when | before_s6_local_search_green | Experiment + optional record update |
| score_layer1_tune_done | false | Set true when pj accepts post-experiment β/cap |
| score_layer1_tune_inputs | site01_windows; mission_templates; aggregate_golden if present | Sweep scores; check uplift histogram and ranking sanity |

## Expected behavior and validation

Wrong if feasible sites with R≈0.35 routinely score above sites with R≈0.7 because B is always high; the experiment before S6 should show that ordering. Wrong if the cap is never applied (score exceeds R×1.30).

## Consequences

- Overrides `score_bonus_max_uplift` in `D-7520` for cap value; both records cited; `D-7520` still owns the formula.
- README or provenance may say “layer-1 β provisional until pre-S6 tune.”