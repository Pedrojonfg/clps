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

- Observation that came out of the comparison, now resolved: the relief showed hard-edged flat patches of different brightness and did not respond to the light direction (same pixels for relief light at 10, 60, 90 degrees). Ruled out first: mesh density, seams between DEM tiers (heights agree within about 0.5 m), the far ring, the data itself. Cause, found by printing the normals and the light in the shader: Cesium's `czm_phong` lights diffuse only from fixed camera-relative directions (eye axis and eye up) and uses the scene light for specular only, and `MaterialAppearance` with `closed: false` flips every normal that has a negative eye-space z. Level ground seen toward the horizon has exactly that, so it was flipped to face down and lit by the camera headlamp, giving the patches. Fix in `web/firstperson.js`: `closed: true`, and Lambert from `czm_lightDirectionEC` computed in the material and written to `emission`; bump grain reduced (it was too strong once lit) and faded sooner. The relief now follows our Sun azimuth at the fixed relief angle (`D-7304`); the earlier "brightness follows our Sun-disc fraction" part was unaffected.

## Expected behavior and validation

Wrong if users ask for textured ground and ion is not an acceptable answer; revisit then with better imagery (for example illumination-controlled data) rather than this mosaic.

## Consequences

- No code change from the experiment; the throw-away patch and script are kept only under `docs/experiments/imagery-drape/`.
- `D-e5d2` stays as the record of the spike; this record closes the question.
- The imagery comparison above was rendered with the old, camera-lit shading; the verdict stands, since the photo's problem is scale and baked shadows, not lighting, but a re-run could look slightly different.
