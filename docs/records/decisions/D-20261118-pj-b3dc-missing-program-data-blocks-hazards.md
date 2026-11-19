---
id: D-20261118-pj-b3dc
title: "Missing program data blocks the hazard analysis; no silent substitutes"
date: 2026-11-18T17:06:47Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261118-pj-a670
concepts: [not evaluable vs favorable default]
supersedes: [D-20261114-pj-f57e]
relates: [D-20261114-pj-5cfa, D-20261114-pj-bf69, D-20261114-pj-8588, D-20261118-pj-9413]
ai: options+critique
---
# Missing program data blocks the hazard analysis; no silent substitutes

## Context

External audit item 5. The code replaces missing program data with favorable values and still reports a complete result: slope missing (file absent, site outside the 80S raster, NaN pixel) becomes 0 deg and soil resistance is computed as flat terrain; if the season computation fails it falls back to "summer" and caches it for the day; a missing season temperature bin falls back to the other season's bin while the output keeps the original season label (`moonpark/hazards/moon.py`, `pcp.py`). All of these are program data (rasters, tables), not user input; they go missing mainly on first use offline or with an interrupted download, or when a site is outside raster coverage. `D-20261114-pj-f57e` instead kept such rows on the board with a `*`.

## Framing

Precision over availability: a result must not look complete when it is not (see `D-20261118-pj-9413`, false negative preferred to false positive). Data used only by the hazards (temperature, dust/soil resistance) must not block analyses that do not use hazards.

## Options considered

1. **A, fill and continue (current)**: assumes a default beats stopping; consequence: complete-looking result that may accept bad sites.
2. **B, fill and mark the gap (`D-f57e`)**: assumes a flagged number is acceptable; consequence: the number shown is still a substitute.
3. **C, block the analysis that needs the datum; allow retrying the download and viewing earlier analyses**: assumes no result is better than a doubtful one; consequence: new hazard analyses are impossible until the data is available.
4. **D, block by default, offer an explicit "continue without this check"**: assumes the user should choose to accept the gap; consequence: more states to explain.

## Decision

**C, limited to what the missing data affects.**

- If a datum needed by the hazards (temperature climatology for the season and local-time bin, slope for soil resistance, the season computation) is missing, the program warns and does **not** run an analysis with hazards. No substitute value is used: no 0 deg slope, no "summer" fallback, no other-season bin.
- Analyses without hazards (hazards switched off, `D-20261114-pj-8588`) still run, because they do not use that data.
- The user can retry the download and can view earlier analyses.
- Missing PSR is unchanged: it is skipped, does not affect the analysis in any way, and does not mark or change the ranking (the PSR handling of `D-f57e` and `D-20261114-pj-bf69` stands).
- This supersedes `D-f57e` for hazard-data gaps (no more starred rows for missing temperature or dust).

## Rationale

(Translated from pj's Spanish.) If the data is not there, no new analysis should be allowed; retrying the download and viewing earlier analyses is fine, but we will not sacrifice our precision. I replace the previous decision. If the user is not using hazards (temperature, dust), and the missing data is used only and exclusively for those hazards, the analysis is allowed. That is, if only the temperature datum is missing, the user is warned and cannot run an analysis with hazards, but everything else can be used. If PSR is missing we skip PSR; it does not affect the analysis in any way, at worst it makes it slightly longer; this is what was decided before and does not need to change.

## Checks raised

- Conflicts with `D-f57e` (stars, rows kept, PSR no mark) → pj: replace it, except the PSR rule.
- A site outside the 80S raster coverage cannot be fixed by retrying → pending: pj has not yet confirmed whether this counts as missing data (see Values).
- Hazards switch off → pj: the analysis is allowed when the missing data is used only by the hazards.
- Multi-cell searches where one cell lacks data → pj (in `D-20261118-pj-75f1`): drop the cell and report how many.

## Values

| Name | Value | Notes |
|------|-------|-------|
| missing_hazard_datum_policy | block hazard analysis, warn, no substitute | |
| non_hazard_analysis_when_hazard_data_missing | allowed | |
| earlier_analyses_when_data_missing | viewable | |
| retry_download | offered | |
| psr_missing | skip silently, no effect on analysis or ranking | same as `D-f57e`/`D-bf69`; unchanged |
| site_outside_raster_coverage | counts as missing data and follows this decision's rule | pj: "keep my previous decision". Fact for the record: the +-304 km rasters are slope and PSR; the temperature maps cover 80-90 S. pj first understood the map to concern only PSR |
| search_cell_missing_data | drop that cell and report how many were dropped | settled in `D-20261118-pj-75f1` |
| payload_label_for_unavailable_hazard | "not evaluated", with a hover explanation in two or three words | pj |
| local_search_hazards | same_as_request | restated from `D-f57e`; hazards switch applies to search |

## Later answers (pj, translated)

Outside the map: the map only means there is no PSR, I thought; if what is missing is temperature or dust then an analysis without hazards still runs, and one with hazards marks that it could not be measured, or removes it. I decided this before, so keep my earlier decision. What the result shows in place of a missing value: "not evaluated" is fine, and on hover a short explanation, two or three words.

## Expected behavior and validation

(pj, translated.) It would be a mistake if this happened very often and ruined the user's experience. Implied check, not stated by pj: first-run download state and failure messages (audit item 23) must make the blocked state short-lived and explain how to resolve it.

## Consequences

- Remove the 0 deg slope fallback, the "summer" fallback on any exception (and its per-day cache) and the other-season bin fallback; stop labelling results with a season that was not used.
- `hazard_gap_star` and the board `*` for missing temperature or dust lose their purpose except for the search-cell case still open.
- The user interface needs a "data not available, retry" state and must keep earlier analyses viewable (audit items 23, 33).
- Not decided here: the exact warning wording, and PSR payload value when the map is absent (currently reported as not in PSR).
- Values of `D-20261114-pj-f57e` dropped explicitly: `local_search_hazard_gap_mark`, `local_search_hazard_gap_fields`, `local_search_hazard_gap_rows`, `local_search_hazard_gap_ui` (the starred-row mechanism is replaced by blocking). `local_search_hazard_gap_psr` is restated as `psr_missing`.
