---
id: D-20261118-pj-75f1
title: "Every search uses the user's requirements; a requirement a search cannot evaluate is warned"
date: 2026-11-18T17:31:33Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261118-pj-a670
concepts: [effective requirements]
supersedes: []
relates: [D-20261114-pj-9cc5, D-20261115-pj-54f0, D-20261118-pj-b3dc, D-20261118-pj-9413]
ai: options+critique
---
# Every search uses the user's requirements; a requirement a search cannot evaluate is warned

## Context

External audit item 7. Read from `moonpark/api/app.py`: the single-site analysis (`/site`) uses the limits the user types (night, no-Earth, lit time, battery, hazards), except that with a mission template the server takes the Sun/Earth thresholds and the gap allowance from the template. The regional search (`/deep-search`) takes only the template (or fixed fallbacks: 72 h night, 48 h no-Earth, 0 %/0 %/5 h), and never evaluates total lit time, battery or hazards (hazards are off by default and its evaluator returns empty hazards). A site can therefore win a search and then fail its own analysis.

## Framing

The search and the analysis must give the same verdict for the same site and window. Honesty with the user over computational cost.

## Options considered

1. **A, each search with its own subset, silently (current)**: assumes what is not evaluated does not matter; consequence: two different exams.
2. **B, a subset, but showing which requirements were evaluated**: assumes a simplified search is acceptable if declared; consequence: cheap, still two exams.
3. **C, every search uses all of the user's parameters**: assumes search and analysis must agree; consequence: more computation, one list of requirements.

## Decision

**C.** All searches, local search and regional/deep search, without exception, use the parameters, thresholds and limits the user entered, the same list as the single-site analysis. If a search cannot evaluate a given requirement, the program **warns and continues**. If a cell lacks the hazard data a search needs, that cell is **dropped and the user is told how many**. A missing PSR map is the exception: it does not block, drop or mark anything.

## Rationale

(Translated from pj's Spanish.) ALL searches, without any exception, should use the parameters, thresholds and the rest that the user entered, for obvious reasons: we would be lying to the user otherwise. If a search cannot evaluate something: warn and continue. If one cell lacks data: drop that cell and say how many were dropped. If what is missing is the PSR, it is not important and the search/optimization can continue, because the PSR gives no information that cannot be obtained in other ways (it only helps check faster). I accept the computational cost.

## Checks raised

- A search that cannot evaluate a requirement could ignore it silently → pj: warn and continue.
- A cell without hazard data in a search that uses hazards (e.g. outside the 80S raster) → pj: drop the cell and report the count.
- Cost of adding battery and hazards to the regional search → pj accepts it; size and time limits are audit items 29-30, not decided here.

## Values

| Name | Value | Notes |
|------|-------|-------|
| search_requirements_source | the user's effective requirements, identical to the single-site analysis | |
| unevaluable_requirement_in_search | warn and continue | pj's rule |
| unevaluated_requirement_row_marking | no per-row marking; one general warning that this could not be measured and the estimate was made as if it were not taken into account | pj; pj would like to see a real case where this happens |
| search_cell_missing_hazard_data | drop the cell, report how many were dropped | settles `search_cell_missing_data` of `D-20261118-pj-b3dc` |
| psr_missing_in_search | continue, no effect | same as `D-20261118-pj-b3dc` |
| search_cost_limit | set from the tests run at implementation (an overnight run) | pj; see `D-20261118-pj-cd33` |
| template_vs_manual_edits | settled in `D-20261118-pj-70ec` | |

## Later answers (pj, translated)

If a search cannot evaluate a requirement, I would like to see the case where that happens, but in any case a general warning: we could not measure this, so we made the estimate as if we did not take it into account.

## Expected behavior and validation

(pj, translated.) Nothing would make it a mistake; pj prefers to be honest and give a result even if it costs more to compute. Implied check, not stated by pj: for the same site and window, the regional search and the single-site analysis return the same verdict.

## Consequences

- Deep-search request gains the full set of user limits, battery and hazard switch; its evaluator evaluates hazards when enabled, like the local search path.
- Local search (`planner_payload.py`) must keep passing the same effective needs it uses for the analysis.
- Regression test: same site, window and requirements through both paths give the same verdict.
- Results must show which requirements were evaluated (audit item 16, provenance).
