---
id: D-20261118-pj-f6b3
title: "S10 keeps the procedural surface: no imagery on the relief"
date: 2026-11-18T12:30:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-2b7a
concepts: [photo-real look vs geometry-true placement]
supersedes: []
relates: [D-20261118-pj-e5d2, D-20261118-pj-c3a9, D-20261118-pj-b17e, D-20261116-pj-7304]
ai: options+critique
---
# S10 keeps the procedural surface: no imagery on the relief

## Context

`D-e5d2` ran the one-hour spike and found the LROC WAC south summer mosaic (100 m/px) is 47 to 98 % photographed shadow around our sites, which would contradict our simulated Sun (`D-7304`). pj then asked to see the three ways forward side by side before deciding. A mini experiment rendered them on the same site, hour and views (files in `docs/experiments/imagery-drape/`).

## Options considered

1. **Procedural surface, no imagery** (chosen): consequence: no new data or files; no real surface features.
2. **(a) Photo where lit, procedural elsewhere**: consequence: in the render it is almost indistinguishable from the procedural surface; adds mid-scale tone patches tied to the photo's Sun, not ours.
3. **(b) Shadows filled and illumination removed**: consequence: smoother and flatter than (a); an approximation (the mosaic mixes many Sun azimuths, so a proper inversion is not possible); less appealing than today.
4. **(c) Cesium ion for recordings**: consequence: more fine detail than any of the above, but it could not be rendered in the experiment because no token was available; stays available as the opt-in of `D-b17e`.

## Decision

**1.** Keep the procedural surface (`D-c3a9`). Do not ship the imagery path, the texture files or a texture store entry.

## Rationale

From a 2 m eye almost everything seen is within a few hundred metres, where one 100 m texel covers the scene, and the far ground is near-horizontal. The photo only adds large-scale tone, which a normal viewer does not perceive as an improvement: the work and the extra files (829 MB source, 10 to 25 MB cropped) buy nothing visible. Users who want textured ground can use ion (`D-b17e`).

## Checks raised

- Open observation, not yet understood: the relief shows hard-edged flat patches of different brightness (see the comparison images with grain off). Ruled out by test: mesh density (3x denser mesh, same patches), seams between DEM tiers (5, 10 and 20 m heights agree within about 0.5 m), the far ring, the data itself (hillshades of the DEMs and of the ring grid are smooth, median slope 5.6 degrees). The pattern also did not change when the relief light elevation went from 20 to 60 degrees, which suggests the relief is not being lit by our light direction as intended. Needs its own diagnosis before any fix is promised.

## Expected behavior and validation

Wrong if users ask for textured ground and ion is not an acceptable answer; revisit then with better imagery (for example illumination-controlled data) rather than this mosaic.

## Consequences

- No code change from the experiment; the throw-away patch and script are kept only under `docs/experiments/imagery-drape/`.
- `D-e5d2` stays as the record of the spike; this record closes the question.
- Follow-up candidate: diagnose why the relief shading does not follow our light direction.
