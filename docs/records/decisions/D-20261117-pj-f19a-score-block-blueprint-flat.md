---
id: D-20261117-pj-f19a
title: "Score and needs block follows Blueprint: flat, colour only on failure"
date: 2026-11-17T12:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261117-pj-c2d8
concepts: [progressive disclosure, design-system authority]
supersedes: []
relates: [D-20261115-pj-01b0]
ai: options+critique
---
# Score and needs block follows Blueprint: flat, colour only on failure
## Context

pj (2026-11-17): the desktop app does not fit the 1100×720 window and "New analysis" needs scrolling; the result block (score, longest night, longest no-Earth) looks off-style; the local-search leaderboard is hard to find; the modes (single window, local search, deep search) are not clear from the UI.

## Decision

**Flat.** Score as a tabular number plus a Feasible/Infeasible tag; needs as a compact table (need, actual, limit, status) with thin neutral bars; red only on failing needs. The red-yellow-green ramp stays on the region map.

## Rationale

Chosen by pj among the options offered in the session (recommended option taken). Honours `D-01b0` (Blueprint strict); colour carries state, not decoration.

## Expected behavior and validation

Wrong if any colour in the block other than the failure state or the feasibility tag is decorative.
