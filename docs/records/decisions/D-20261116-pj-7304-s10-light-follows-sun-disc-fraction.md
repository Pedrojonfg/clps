---
id: D-20261116-pj-7304
title: "First-person backdrop brightness follows our visible Sun-disc fraction"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261116-pj-9eee
concepts: [photo-real look vs geometry-true placement, visible disc fraction]
supersedes: []
relates: [D-20261115-pj-671e, D-20261115-pj-ac34, D-20261114-pj-9e53]
ai: recommended
---
# First-person backdrop brightness follows our visible Sun-disc fraction
## Context

The backdrop was lit from our Sun azimuth at a fixed angle and fixed intensity, whether or not the Sun cleared our mask. pj (2026-11-16): the illumination must change with the fraction of solar disc visible; that is what makes this view didactic.

## Framing

The scene's brightness should be driven by the quantity the score uses, so that "night" in the planner looks like night here.

## Options considered

1. **Keep fixed lighting**: consequence: the scene is equally bright at 0 % and 100 % disc.
2. **Scale backdrop brightness by our `sun_fraction` (the series the planner scores), keep our Sun azimuth for light direction, keep a small night floor so terrain stays legible**: consequence: brightness is ours, relief shading is still cosmetic.
3. **Physically based shadows cast by the Cesium terrain**: consequence: shadows would come from terrain that is not our mask (`D-671e`), and could disagree with our series.

## Decision

**2.**

## Rationale

pj asked for brightness tied to the visible disc. Option 2 makes the backdrop respond to our own visibility result without claiming a photometric or shadow model: at fraction 0 the ground drops to a dim floor, at 1 it is fully lit, and partial discs sit in between. Option 3 was rejected because it would let third-party terrain decide light and dark.

## Checks raised

- Viewers may read the dimming as rendered shadows → the provenance details say brightness follows our visible-disc fraction and that no shadows are cast; the Sun label shows the percentage.
- Light elevation stays lifted above the true grazing angle so relief reads → stated in the provenance details as before.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_backdrop_brightness | night_floor + (1 − night_floor) × sun_fraction | `sun_fraction` from the planner series, interpolated during playback |
| s10_night_floor | 0.07 | Dim, slightly cool; terrain still legible |
| s10_light_azimuth | our_sun_azimuth | |
| s10_light_elevation | fixed_relief_angle | Not the true elevation; cosmetic |
| s10_cast_shadows | none | Would be third-party terrain deciding light |

## Expected behavior and validation

Wrong if the scene is bright at a time the planner counts as night, or dark while the full disc is above our mask.

## Consequences

- Provenance details text changes; the one-liner of `D-671e` stays.
- The 2D fallback tints its sky by the same fraction.
