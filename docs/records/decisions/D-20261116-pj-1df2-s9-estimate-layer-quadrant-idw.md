---
id: D-20261116-pj-1df2
title: "Region map: fill between evaluated cells with a distance-faded estimate (proposed, awaiting pj)"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: ai
status: proposed
mode: own
domain: method & validation
task: T-20261116-pj-9eee
concepts: [smooth fill inventing mid-scores between sparse points, silent incomplete search, evaluated versus estimated]
supersedes: []
relates: [D-20261115-pj-85bf, D-20261115-pj-834a, D-20261114-pj-affb, D-20261116-pj-2325]
ai: delegated-by-pj
---
# Region map: fill between evaluated cells with a distance-faded estimate (proposed, awaiting pj)
## Context

pj (2026-11-16): many points on the map have no value at all, neither evaluated nor induced; the original idea was that every point be interpolated from the nearest ones; ideally every point is painted one colour or another and the user can see the interpolation at any point. pj gave the AI freedom to decide, to be justified and reviewed the next day, and allowed the answer "this view would be too misleading". **This record is that proposal; it is not accepted until pj says so.** Method and validation is an own domain.

What the map did before: under a partial search each evaluated cell got four "induced" copies of itself 1 km away (`D-85bf`), and the overview blended colours only within about two cells of a sample (`D-834a`). So between samples that are 10–30 km apart nothing was painted. No record defines an interpolation formula for scores; the only recorded interpolation rule is the four-quadrant inverse-distance fill for temperature gaps (`D-affb`).

## Framing

Painting everything makes the map legible; painting everything equally would hide that most of it was never scored. The fill has to show its own uncertainty.

## Options considered

1. **Leave gaps empty (status quo)**: honest, but the map reads as scattered dots and pj finds it unusable.
2. **Paint the whole searched region at full strength by interpolation**: consequence: an invented value 30 km from any sample looks as solid as a scored cell.
3. **Estimate layer: four-quadrant inverse-distance interpolation of evaluated cells (the `D-affb` rule), drawn translucent and fading to nothing with distance from the nearest evaluated cell; unpainted beyond a reach; never clickable as a score**: consequence: most of a searched region is painted, far gaps stay visibly empty.
4. **Paint only under total coverage**: consequence: the default optimized search stays dots.

## Decision

**3, proposed.** The estimate layer replaces the display of the four-neighbour induced copies; evaluated cells stay as solid markers on top (`D-20261116-pj-2325`).

## Rationale

The view is misleading only if an estimate can be mistaken for a score. Three things prevent that: the layer is translucent and visibly weaker the farther it is from data; it stops at a reach of three times the typical spacing between evaluated cells, so real holes in coverage stay holes; and hovering it says "estimate, not scored", with the distance to the nearest evaluated cell and how many cells it was built from. Scores here come from terrain horizons, which can change sharply over a kilometre at a crater rim, so an interpolated value far from data is weak evidence; fading by distance says exactly that. Four-quadrant inverse distance is used because it is the project's one recorded interpolation rule and it does not let a dense cluster on one side outvote a lone sample on the other. Feasibility is interpolated with the same weights; where infeasible weight dominates, the estimate is drawn in the infeasible colour.

Under total coverage every cell is evaluated, so the layer only fills the gaps between markers at low zoom and adds no claim.

## Checks raised

- A reader may still quote an estimate as a result → readout wording, "estimate" in the legend, and the estimate cannot be pinned as a scored cell (it can be opened in the planner to be evaluated for real).
- Hill-climb searches sample along paths, so spacing is uneven → reach uses the median nearest-neighbour spacing of evaluated cells, with a floor and a cap.
- Not validated: no check yet of estimate error against a total-coverage run of the same region. That comparison is the test that would justify, tune or kill this layer.

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_estimate_method | four_quadrant_inverse_distance | Nearest evaluated cell per quadrant, weights 1/d² |
| region_map_estimate_reach | 3 × median evaluated spacing | Floor 3 km, cap 60 km; unpainted beyond |
| region_map_estimate_opacity | 0.6 at an evaluated cell, falling to 0 at reach | |
| region_map_estimate_feasibility | same weights; infeasible colour where infeasible weight > 0.5 | |
| region_map_induced_copies_display | replaced_by_estimate_layer | API still returns them; the map no longer draws them |

## Expected behavior and validation

Wrong if, on a region with both an optimized and a total-coverage run, estimates near the reach disagree with the evaluated truth so often that the faded colour is still too confident; or if users report reading estimates as scores.

## Consequences

- If pj accepts: remove four-neighbour induction from the API (`induce_neighbours`) in a follow-up and mark the induction style of `D-85bf` superseded.
- If pj rejects: the "Evaluated only" toggle becomes the default and the layer is removed; markers and snapping (`D-20261116-pj-2325`) do not depend on it.
