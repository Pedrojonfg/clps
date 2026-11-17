---
id: D-20261117-pj-a3f1
title: "Region map: evaluated-cell markers at 85 % opacity so the relief shows through"
date: 2026-11-17T10:00:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261116-pj-9eee
concepts: [evaluated versus estimated, absolute score color scale]
supersedes: []
relates: [D-20261116-pj-2325, D-20261116-pj-1df2]
ai: recommended
---
# Region map: evaluated-cell markers at 85 % opacity so the relief shows through
## Context

pj (2026-11-17), looking at a whole-cap mock search: the markers cover the Moon completely where they are dense, so the relief underneath (craters, shadows) cannot be seen. pj asked to lower the opacity by about 15 %.

## Framing

Markers must stay readable as score colours, yet the terrain gives the context for where a cell lies.

## Options considered

1. **Keep fully opaque markers**: consequence: dense areas hide the terrain.
2. **Marker alpha 0.85**: consequence: colours blend slightly with the relief; dense overlaps let a little more through.
3. **Much lower alpha (0.5 or less)**: consequence: score colours get contaminated by terrain brightness and stop matching the legend.

## Decision

**2.** pj's value, about 15 % transparency, is used.

## Rationale

The legend ramp is absolute (`D-2325`); at 0.85 the hue stays recognisable while the relief remains visible. Only the marker alpha changes; size, ring, infeasible mark and picking are untouched.

## Checks raised

- Score colours read slightly muted over bright terrain → if reviewers cannot match marker to legend, raise alpha toward 0.9.

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_marker_alpha | 0.85 | Was 1.0; applies to the whole marker including ring |

## Expected behavior and validation

Wrong if terrain is still not visible through dense markers, or a marker colour can no longer be matched to the legend.
