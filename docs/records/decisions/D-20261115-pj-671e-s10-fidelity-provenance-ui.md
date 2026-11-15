---
id: D-20261115-pj-671e
title: "S10 fidelity: Cesium backdrop not our model; expandable provenance UI"
date: 2026-11-15T11:32:59Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-2b7a
concepts: [photo-real look vs geometry-true placement, external tiles as if our score mask]
supersedes: []
relates: [D-20261115-pj-ac34, D-20261115-pj-7d58, D-20261115-pj-f2d3]
ai: options+critique
---
# S10 fidelity: Cesium backdrop not our model; expandable provenance UI

## Context

`D-ac34` / `D-7d58` already split hybrid composition (Cesium Moon backdrop vs our mask and sky). Item 5 needed an explicit fidelity/claims bar and a UI pattern that stays honest without crowding the screen. pj asked the AI to derive ours/not-ours from recorded work and use a conventional compact UI; then accepted that draft (“OK”).

## Framing

Make “what is ours” scannable; keep detail one click away.

## Options considered

1. **Draft package (accepted):** ours = horizon mask + site×time Sun/Earth (and score/search elsewhere); not ours = Cesium Moon terrain/imagery; UI = always-on short line + expandable details.
2. **Full always-visible legal block:** honest but eats the viewport.
3. **No on-UI provenance (docs only):** fails the hybrid honesty check.

## Decision

**Accepted draft:** short always-visible backdrop disclaimer plus expandable details; ours/not-ours as in Values.

## Rationale

pj: did not want to invent the UI pattern; accepted the conventional footnote / expandable notice draft so it stays clear that the backdrop is not ours without cluttering the screen.

## Checks raised

None raised beyond accepting the draft.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_ours | horizon_mask; sun_earth_site_time_geometry | Score/search claimed elsewhere, not as Cesium terrain |
| s10_not_ours | cesium_moon_terrain_imagery | NASA/USGS via ion; visual context only |
| s10_provenance_ui_pattern | persistent_one_line_plus_expandable_details | e.g. footnote / `*` / “Details” |
| s10_provenance_one_liner | Backdrop: Cesium Moon — not our model | Exact copy may be lightly edited for fit; meaning fixed |

## Expected behavior and validation

Wrong if a careful viewer still thinks the Cesium relief *is* the project’s terrain/score model despite the UI.

## Consequences

- Build must ship the one-liner and an expandable details panel on the first-person page.
- Docs can repeat the same split; UI remains the primary honesty surface for S10.
