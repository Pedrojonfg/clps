---
id: D-20261114-pj-f57e
title: "Local search uses request hazards; temp/dust gaps starred on the board"
date: 2026-11-14T19:34:14Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-03a6
concepts: [needs-adapted score, local neighborhood search]
supersedes: []
relates: [D-20261114-pj-8588, D-20261114-pj-5cfa, D-20261114-pj-8764, D-20261114-pj-bf69, D-20261114-pj-72bc]
ai: options+critique
---
# Local search uses request hazards; temp/dust gaps starred on the board

## Context

S6 ranks many site×windows with `score(series, hazards, needs)`. The demo toggle enables or disables layer-B hazards (`D-8588`). Surface limits fail-close when present (`D-5cfa`). PSR is a precheck (`D-bf69`). Hazard rasters may be missing on disk during portfolio builds.

## Framing

Keep search rankings consistent with the planner's hazard setting, and make incomplete temperature/dust inputs obvious without inventing silent defaults that look like full layer-B.

## Options considered

1. **A — Search always with empty hazards**.
2. **B — Search with the same hazards as the request; missing files marked clearly**.
3. **C — Hazards only on the origin site**.

## Decision

**B.** Rows with incomplete **temperature or dust** stay on the leaderboard marked with `*`; the board can hide those rows. Missing **PSR** does not get this treatment and should not change ranking behavior (PSR is an extra check that does not add new information in that gap case).

## Rationale

Search with hazards (not very demanding computationally versus sky/mask). If files were missing, mark those cases with an asterisk and show that very clearly in the UI. Confirmed B: stay on the leaderboard with `*`; the leaderboard has a hide option. If PSR is missing, nothing should change because it is an extra check that does not add new information; the asterisk rule should apply only to temperature and dust.

## Checks raised

- Inconsistent rows if some candidates lack rasters → `*` plus optional hide.
- PSR absence vs temp/dust absence → split policy as above (`D-bf69` PSR role unchanged when the map is present).
- Hazards-off toggle → search uses empty hazards, same as the chart path (`D-8588`).

## Values

| Name | Value | Notes |
|------|-------|-------|
| local_search_hazards | same_as_request | Respects demo hazards toggle |
| local_search_hazard_gap_mark | asterisk_on_leaderboard | User-visible `*` |
| local_search_hazard_gap_fields | temperature; dust_soil | Only these trigger `*` |
| local_search_hazard_gap_psr | no_mark_no_rank_change | Missing PSR map does not star or alter ranking for this rule |
| local_search_hazard_gap_rows | keep_on_board_hide_optional | Stay ranked; UI can hide starred rows |
| local_search_hazard_gap_ui | very_clear_star_and_copy | Provenance names what file/field was missing |

## Expected behavior and validation

Wrong if missing temperature/dust inputs are silent in the leaderboard, or if missing PSR is treated like those gaps. Compute cost of hazard reads is not the falsifier for v1 given raster sampling vs sky/mask.

## Consequences

- S6 `score(..., hazards, ...)` uses the request's hazard payload, not a hard-coded `{}`.
- Leaderboard schema includes a gap/star flag for temp/dust incompleteness and a hide control.
- PSR precheck behavior when the map **is** present stays `D-bf69`; this record only covers the **missing map** case for starring policy.
