---
id: D-20261117-pj-3b71
title: "New analysis splits into Setup and Results views"
date: 2026-11-17T12:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261117-pj-c2d8
concepts: [progressive disclosure, design-system authority]
supersedes: []
relates: [D-20261116-pj-142f, D-20261116-pj-4902]
ai: options+critique
---
# New analysis splits into Setup and Results views
## Context

pj (2026-11-17): the desktop app does not fit the 1100×720 window and "New analysis" needs scrolling; the result block (score, longest night, longest no-Earth) looks off-style; the local-search leaderboard is hard to find; the modes (single window, local search, deep search) are not clear from the UI.

## Decision

**Two views.** Run moves to a Results view; `Edit inputs` returns. Results has sub-tabs Overview (score, needs, panorama, timeline) and Best starts (leaderboard, only when local search ran).

## Rationale

Chosen by pj among the options offered in the session (recommended option taken). Each view fits the 650 px under the nav bar; the leaderboard stops being the last block of a long page.

## Expected behavior and validation

Wrong if either view needs vertical scroll at 1100×720 in Overview or Setup, or if Best starts is not reachable after a local-search run.
