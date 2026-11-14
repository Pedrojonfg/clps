---
id: D-20261111-pj-ea51
title: "Audience and product positioning"
date: 2026-11-11T15:08:17Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: problem framing
task: T-20261111-pj-c84f
concepts: [framing, challenge brief]
supersedes: []
relates: [U-20261111-pj-9197]
ai: options+critique
---
# Audience and product positioning

## Context

Space Apps challenge statement names mission planners, educators, and the public. Task T-20261111-pj-c84f must fix who the v1 product is for before scope and UI depth. Official challenge text archived in `docs/sources/challenge-statements/clps-lunar-mission-browser.md`.

## Framing

Optimize for planner-grade technical depth in the backend while keeping a frontend that non-planners can use, with explanation of where each datum comes from and multiple visualizations.

## Options considered

1. **A — Planner-only depth**: assumes only planners matter; consequence: no UX cost for friendliness; weaker fit to the three audiences named in the statement.
2. **B — Dual: planner-depth backend + explainable UI**: assumes one product serves all via depth + clarity; consequence: more UX/explainability work; risk that friendliness slows planners (mitigated by a more technical UI fallback).
3. **C — Educator/public first**: assumes pedagogy first; consequence: less “real planner” depth.

## Decision

**B — Dual: planner-depth backend + explainable UI** (with technical UI fallback if friendliness interferes with planner workflow).

## Rationale

We will build a product with the technical depth a real planner needs. The point is to make a UI so intuitive, and with so much capacity to explain what sits behind each datum, that an educator or a general power user can use it. That is: a complex backend as for a planner, and a frontend friendly enough not to scare off everyone who is not a planner, with the ability to explain where the data come from and to include different visualizations (at first glance: 2D and projective 3D).

## Checks raised

- Friendly frontend might interfere with normal planner use → then switch to a more technical front any real planner could use, without giving up explainability (as an add-on, it would rarely be “surplus”).
- 48 h may not fit full depth + friendly UX + 2D/3D → resolve in scope decision (queue item 3).

## Values

| Name | Value | Notes |
|------|-------|-------|
| primary_user | mission_planner | Technical depth of calculations and metrics |
| secondary_users | educator, general_power_user | Same product; served by UI and explainability |
| ui_default_mode | friendly_explainable | Intuitive UI + provenance of data |
| ui_fallback_mode | technical_if_planner_friction | If friendly UI interferes with planner workflow |
| viz_modalities_intent | 2d_and_projective_3d | Intent only; final viz set deferred to scope/presentation |

## Expected behavior and validation

This choice would be wrong if the friendly frontend interfered with a planner’s normal use. In that case we would switch to a more technical front that a real planner could use, without dropping explainability (as an add-on, it would rarely be superfluous).

## Consequences

- Scope and success criteria must state how much of “friendly + explainable + 2D/3D” is in the 48 h cut.
- Product question / recommender decisions assume planner-grade metrics underneath.
- Claims must not imply educator-first pedagogy if the primary bar is planner depth.
