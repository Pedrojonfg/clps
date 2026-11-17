---
id: D-20261117-pj-8e04
title: "Setup shows essentials; mission needs fold away"
date: 2026-11-17T12:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261117-pj-c2d8
concepts: [progressive disclosure, design-system authority]
supersedes: []
relates: [D-20261114-pj-8588]
ai: options+critique
---
# Setup shows essentials; mission needs fold away
## Context

pj (2026-11-17): the desktop app does not fit the 1100×720 window and "New analysis" needs scrolling; the result block (score, longest night, longest no-Earth) looks off-style; the local-search leaderboard is hard to find; the modes (single window, local search, deep search) are not clear from the UI.

## Decision

**Essentials visible** (lat/lon, start/end, template, mode); **Mission needs folded**, with a one-line summary (template, night, no-Earth limits). Step, thresholds, bridge, hazards and require-both live in the fold.

## Rationale

Chosen by pj among the options offered in the session (recommended option taken). Defaults come from the template, so most runs never open the fold.

## Expected behavior and validation

Wrong if a changed need is not reflected in the summary line.
