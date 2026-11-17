---
id: D-20261117-pj-52c6
title: "Modes are chosen with a described selector and cross-linked"
date: 2026-11-17T12:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261117-pj-c2d8
concepts: [progressive disclosure, design-system authority]
supersedes: []
relates: [D-20261114-pj-9cc5, D-20261115-pj-60a3]
ai: options+critique
---
# Modes are chosen with a described selector and cross-linked
## Context

pj (2026-11-17): the desktop app does not fit the 1100×720 window and "New analysis" needs scrolling; the result block (score, longest night, longest no-Earth) looks off-style; the local-search leaderboard is hard to find; the modes (single window, local search, deep search) are not clear from the UI.

## Decision

**Selector** in Setup: *Single window* (score this exact window) vs *Best nearby start* (also tries shifted starts and ranks them); a note links to Region map for whole-region deep search. Region map explains each search mode and its cost.

## Rationale

Chosen by pj among the options offered in the session (recommended option taken). The same word 'search' covered three different things.

## Expected behavior and validation

Wrong if a first-time user cannot tell from Setup which mode gives a leaderboard and where deep search lives.
