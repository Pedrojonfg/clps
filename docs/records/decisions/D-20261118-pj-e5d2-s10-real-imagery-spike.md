---
id: D-20261118-pj-e5d2
title: "S10 real surface imagery: one-hour spike before committing"
date: 2026-11-18T11:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-2b7a
concepts: [photo-real look vs geometry-true placement]
supersedes: []
relates: [D-20261118-pj-c3a9, D-20261118-pj-b17e, D-20261115-pj-ce2e]
ai: options+critique
---
# S10 real surface imagery: one-hour spike before committing

## Context

pj: real imagery would improve the experience a lot, and matters for recording video to share with coworkers. Candidate: LROC WAC south-polar mosaic at 100 m/px (public domain, about 1.3 GB as the global south tile, 10 to 25 MB once cropped to 80°S–90°S). Cost estimate: negligible compute (colour sampled per mesh vertex on the server, about 170 KB extra), about a day of work, mostly tuning. Main risk: polar images carry baked shadows from grazing light, which contradict our simulated Sun.

## Options considered

1. **Commit to imagery now**: consequence: a day spent that may end in a dark, blotchy result.
2. **One-hour spike, then decide** (chosen): consequence: cheap evidence first.
3. **Stay procedural**: consequence: no cost, less appealing for video.
4. **Use ion for recordings**: consequence: best quality now, token needed only on the recording machine.

## Decision

**2.** Download the WAC south mosaic (prefer the summer ROI product), crop to 80°S–90°S, look at it, and drape it on our mesh in a test render. Go if tone is usable without baked-shadow artefacts; otherwise stop and keep `D-c3a9`.

## Checks raised

- 100 m/px is blocky inside about 300 m of the observer: blend with the procedural grain there.
- Attribution NASA/GSFC/Arizona State University; file distribution via the data store, optional.

## Expected behavior and validation

Go criteria: no obvious baked shadows at the site, brightness controllable by `D-7304`. Wrong to adopt if the imagery makes the lit/dark state contradict our Sun series.

## Consequences

- If go: per-vertex albedo in `/terrain`, an imagery file in the store, provenance and credit updated.
- If no-go: this record closes the question until better imagery is available.

## Outcome of the spike (2026-11-18)

Downloaded `WAC_ROI_SOUTH_SUMMER_100M.TIF` (829 MB, 8-bit, 28786 px square, 100 m/px, polar stereographic in the same planar metres as our DEMs). It lines up with our DEM (the large crater and the small craters coincide in a Site01 window), and sampling it needs no reprojection.

**No-go for draping it directly near the pole.** Even this mosaic, chosen by LROC to minimise shadows, is mostly photographed shadow at our sites:

| Window | Pixels below 20 / 255 | Median |
|---|---|---|
| Site01, 3 km | 58 % | 5 |
| Site01, 15 km | 47 % | 36 |
| (-89.52, 205), 3 km | 98 % | 2 |
| (-89.48, 248), 3 km | 94 % | 1 |
| 85°S and 82°S, 3 km | 11 % | 72 to 87 |

Draped as colour, the photo's own shadows would sit on the mesh and contradict our Sun-disc series (`D-7304`); near the pole most of the ground would be black with no information to recover. It is usable at about 82°S to 85°S, which is not where the sites are.

Kept: procedural surface (`D-c3a9`). Options left open, none started: (a) use the photo only where lit and blend to procedural elsewhere (patchwork tied to the photo's Sun); (b) invert the photo's illumination against our DEM to recover albedo (research-grade, shadow pixels still empty); (c) ion for recordings. The file stays in `data/imagery/` (gitignored) for any later test.
