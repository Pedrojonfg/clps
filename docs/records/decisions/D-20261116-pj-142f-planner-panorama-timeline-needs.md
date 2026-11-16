---
id: D-20261116-pj-142f
title: "Planner result view: horizon panorama, visibility timeline and needs-versus-actual"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: ai
status: accepted
mode: advise
domain: presentation
task: T-20261116-pj-9eee
concepts: [sky chart form, need versus actual]
supersedes: []
relates: [D-20261114-pj-aa58, D-20261115-pj-b6fe, D-20261116-pj-b43a]
ai: delegated-by-pj
---
# Planner result view: horizon panorama, visibility timeline and needs-versus-actual
## Context

The planner's result block was a polar sky chart (elevation as radius, 0–8°) with a four-colour strip under it. pj (2026-11-16): "the main-screen visualization is very ugly and cannot be understood; fix it, you are free to choose the visualization." At polar sites everything of interest happens within a few degrees of the horizon, so a polar plot crushes the horizon mask into a blob at the centre and the Sun and Earth tracks spiral around it; the strip had no time axis and no link to the score.

## Framing

The view has to answer three questions in order: is this site×time feasible and how good is it; when are the Sun and the Earth visible; and why (which piece of terrain hides them).

## Options considered

1. **Keep the polar chart, restyle it**: assumes the form is right and only the styling is off; consequence: the low-elevation crowding stays.
2. **Unrolled horizon panorama (azimuth × elevation) plus a visibility timeline plus needs-versus-actual bars**: assumes readers think of a horizon as a line they look along; consequence: three small coordinated views instead of one chart.
3. **Timeline only**: assumes the "why" is not needed on this screen; consequence: the horizon mask, which is the product's own model, disappears from the main screen.

## Decision

**2.** Delegated by pj; chosen by the AI.

## Rationale

The panorama is the view an observer has when turning around, and it is the same picture the first-person screen falls back to (`D-ac74`), so the two screens teach the same reading. The timeline puts visible Sun-disc fraction and Earth visibility on a real time axis, where the longest night and the longest no-Earth gap can be marked directly. The needs-versus-actual bars show each mission need against the value achieved, which is what the score's feasibility is made of.

## Checks raised

- Three views can scatter attention → hovering a time in the timeline highlights the same instant in the panorama; one shared time cursor.
- The elevation axis is stretched relative to azimuth → stated on the axis; it is a chart, not a photograph.

## Values

| Name | Value | Notes |
|------|-------|-------|
| planner_sky_chart_form | horizon_panorama_az_el | Replaces the polar chart on the planner screen |
| planner_timeline_rows | sun_disc_fraction_area; earth_visibility_band | Need thresholds drawn as lines; longest night / no-Earth runs marked |
| planner_needs_view | bar_per_need_with_limit_marker | Longest night vs max, longest no-Earth vs max, continuous lit vs min |
| planner_score_scale | absolute_0_to_1.4 | Same absolute scale as the region map (`D-7227`) |

## Expected behavior and validation

Wrong if a first-time viewer cannot say, from this block alone, whether the site is feasible and during which hours the Sun is up.

## Consequences

- `PolarChart.tsx` is removed from the planner screen.
- The panorama must use the mask's azimuth convention correctly (`D-20261116-pj-b43a`).
