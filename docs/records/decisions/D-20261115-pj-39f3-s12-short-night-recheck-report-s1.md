---
id: D-20261115-pj-39f3
title: "S12 short-night re-check: separate report; reopen Y if >5 h"
date: 2026-11-15T12:05:58Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: method & validation
task: T-20261115-pj-98c4
concepts: [short-night regime, success X/Y/Z]
supersedes: []
relates: [D-20261114-pj-f369, D-20261114-pj-41fa, D-20261115-pj-1a9e]
ai: recommended
---
# S12 short-night re-check: separate report; reopen Y if >5 h

## Context

`D-f369` / `D-41fa`: the 28-point Y gate used sites with longest night ≥ 392 h; error in a VIPER-like ~50 h regime is unmeasured. S12 must define the re-check. pj asked for advise on parameter choices.

## Framing

Measure schedule error where nights are short without silently rewriting `success_y` until a follow-up decision.

## Options considered

1. **S1 — Separate report; reopen Y if error > 5 h** (recommended).
2. **S2 — Same as S1 but failing CI on short-night error > 5 h.**
3. **S3 — Site01 only, no short-night band search.**
4. **S4 — Fold short-night into Y immediately.**

## Decision

**S1.** Short-night re-check is a **separate report** (does not automatically change `success_y`). Light/bridge/tolerance defaults match the Y 28-point test (same disc-fraction definition as that suite; shadow bridge 5 h; **5 h** tolerance schedule vs fine reference). Sites: **Site01** plus PGDA-78 / 5 m points whose longest night in the fixed test year falls in **~40–80 h** when available; if none, Site01 plus the shortest available night among those points, documented. Results in `docs/validation.md` plus script/test. If absolute error **> 5 h** on that set, record it and **reopen Y** via a new decision (do not silence).

## Rationale

Accepted the recommendation: S1 is the most coherent with what is already decided.

## Checks raised

- Overnight / CI may fail before final product → accepted; fix before final product (`D-1a9e`).
- Band 40–80 h may be empty → kept S1; fallback to shortest available documented.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s12_short_night_mode | separate_report_reopen_y_if_over_tol | Not part of success_y until reopened |
| s12_short_night_tolerance_h | 5 | Same as Y / `D-f369` default |
| s12_short_night_bridge_h | 5 | Match Y suite defaults |
| s12_short_night_light_def | same_as_y_28pt_suite | No second silent definition |
| s12_short_night_sites | site01_plus_pgda78_in_40_80h_else_shortest | Document actual set in validation.md |
| s12_short_night_year | deferred — pin when script is written (prefer one fixed year, e.g. 2027) | |
| s12_short_night_on_fail | reopen_success_y_decision | Not silent pass |

## Expected behavior and validation

Wrong if short-night error stays unmeasured while claims imply Y covers VIPER-like nights, or if >5 h errors are ignored. Tests may fail overnight; that is fixed before the final product.

## Consequences

- Scripts under S12 produce the report; Y stays the 28-point long-night gate until a superseding decision.
- Feeds `docs/validation.md` and honest README wording (`D-fe17`, `D-1a9e`).
