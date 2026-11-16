---
id: D-20261116-pj-2325
title: "Region map: evaluated cells are always-visible markers, infeasibles are not black, picking snaps to evaluated cells"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261116-pj-9eee
concepts: [absolute score color scale, infeasible display zero, evaluated versus estimated]
supersedes: [D-20261115-pj-8acb]
relates: [D-20261115-pj-85bf, D-20261115-pj-834a, D-20261115-pj-7227, D-20261115-pj-4126, D-20261116-pj-1df2]
ai: recommended
---
# Region map: evaluated cells are always-visible markers, infeasibles are not black, picking snaps to evaluated cells
## Context

pj reviewed the region map on a whole-cap mock search (2026-11-16): with the default or the "Whole Moon" zoom the painted cells cannot be seen at all; zoomed in, only a few points show; black infeasible cells cannot be told from craters and shadows; and it is hard to click an evaluated cell in a sea of induced ones. pj: evaluated cells give the most insight, so the user must reach them most easily; an option to show only evaluated cells and have the cursor go to the nearest one would be fine; free to change the infeasible colour.

Cause of the "few points": each evaluated cell was painted at its true size (about 1 km) on a cap 600 km across, so at fit zoom a cell is under one pixel. Nothing was dropped by distance.

## Framing

First read of the map must be where the search evaluated and how good each place is, at any zoom.

## Options considered

1. **Only enlarge the default zoom**: consequence: a whole-cap search still cannot be seen whole.
2. **Draw every evaluated cell as a marker with a minimum on-screen size; infeasibles in a colour that is neither on the score ramp nor on the Moon; pointer snaps to the nearest evaluated cell within a screen radius; a toggle hides everything but evaluated cells; a ranked list of the best evaluated cells**: consequence: at low zoom a marker is larger than the cell it stands for.
3. **Aggregate into coarse bins at low zoom**: consequence: bins would show numbers no search produced.

## Decision

**2.** This supersedes the black fill of `D-8acb`; its relative-badness dot is kept, drawn inside the infeasible marker.

## Rationale

pj asked for more visible points, a default zoom at which they can be told apart, easier access to evaluated cells and a clearer infeasible mark. A minimum on-screen size makes every evaluated cell visible at every zoom, so the default fit already shows the whole search. Violet with a cross is unmistakably not terrain and not a score colour; "cannot land here" still reads apart from "poor but feasible" (the purpose of `D-8acb`). Snapping the pointer to evaluated cells within a generous radius makes them the easy target; the best-cells list reaches them without aiming at all.

## Checks raised

- Enlarged markers overstate the area a cell covers at low zoom → markers shrink to the true cell size as soon as that is larger than the minimum; the legend says markers mark evaluated cells, not areas.
- Ramp is red–yellow–green, weak for colour-vision deficiency → unchanged here (`D-7227` is pj's); the readout and the best-cells list give the number.

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_evaluated_marker_min_px | 4 to 9 px diameter | Scales with sample spacing on screen; true cell size once larger |
| region_map_infeasible_fill | violet_with_cross | Supersedes `region_map_infeasible_fill = black` |
| region_map_infeasible_marker | in_query_relative_dot | Kept from `D-8acb`, inside the marker |
| region_map_pick | nearest_evaluated_within_24_px | Estimate readout only when no evaluated cell is that close |
| region_map_evaluated_only_toggle | present | Hides the estimate layer |
| region_map_top_cells_list | best_8_feasible_evaluated | Click flies to and pins the cell |

## Expected behavior and validation

Wrong if, at the default zoom after a whole-cap search, a viewer cannot see where the evaluated cells are, or cannot tell infeasible markers from terrain.

## Consequences

- `sample_rgba` returns the violet for infeasibles; tests that pinned black change.
