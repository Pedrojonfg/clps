---
id: D-20261114-pj-affb
title: "Missing temperature pixels use four-quadrant inverse distance"
date: 2026-11-14T15:18:06Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-d4ce
concepts: [nodata fill, climatology, provenance]
supersedes: []
relates: [D-20261114-pj-41a2, D-20261114-pj-de42]
ai: options+critique
---
# Missing temperature pixels use four-quadrant inverse distance

## Context

`D-20261114-pj-41a2` reads the polar seasonal local-time climatology and left empty pixels undecided. The Diviner GDR text leaves cells with no observation empty, unlike LOLA, which interpolates. `gdal_fillnodata` fills a hole with inverse-distance weights on the nearest valid pixel in each of up to four quadrants. Its default search is 100 pixels and it does no smoothing pass. If it finds no valid pixel, the cell stays empty.

## Framing

When the chosen bin has no value at the site, emit a filled kelvin. Keep GDAL's default search, smoothing and empty fallback.

## Options considered

1. **A — Leave the cell empty**: assumes no invented kelvin; consequence: that site and hour have no temperature.
2. **B — Copy the nearest valid pixel**: assumes one neighbor is enough; consequence: a copied kelvin, no mean.
3. **C — Inverse distance from the nearest valid pixel in each quadrant, GDAL defaults**: assumes a short mix of nearby valid pixels; consequence: a blended kelvin, search 100 pixels, no smoothing, still empty if none are found.
4. **D — Bilinear, cubic or Lanczos while resampling**: assumes the job is a grid change; consequence: not a hole fill.
5. **E — Gaussian weights on every neighbor**: assumes every surrounding valid pixel enters; consequence: a kernel mean, not the GDAL hole-fill default.

## Decision

**C.** With GDAL's defaults: search 100 pixels, smoothing iterations 0, leave empty if no valid pixel is found.

## Rationale

C in the GDAL style, because it is the same simple and intuitive idea as before, and it is also proven in the real world, in the sense that it is something conventional. (The conventional clause is from the brief.)

## Checks raised

- A huge crater at the point and not at the neighbors could make the mean lie; pj said no fill removes that, and the score would probably be 0 because of the relief → kept C. Relief does not zero the score today (`D-de42`); pj kept C after that check.
- Leaving the cell empty does not emit the false kelvin → kept C.
- A 100-pixel search is 24 km at 240 m and can mix a sunlit ridge with a shadowed floor → kept the GDAL default.

## Values

| Name | Value | Notes |
|------|-------|-------|
| temperature_missing_pixel | four_quadrant_inverse_distance | Nearest valid pixel in each quadrant, inverse-distance weights. Settles the deferral in `D-20261114-pj-41a2`. |
| temperature_fill_max_distance_px | 100 | GDAL default. At 240 m this is 24 km. |
| temperature_fill_smoothing_iterations | 0 | GDAL default. |
| temperature_fill_if_none | leave_empty | No valid pixel inside the search. |

## Expected behavior and validation

The same as before: that we were missing something, but that does not seem to be the case; our approach seems the best. The only thing that could happen is a very specific case, a huge crater right at that point and not at the neighbors, that would make the mean lie. In that case, (1) there would also be no approach that removes that problem, and (2) the score will probably be 0 anyway because of the relief.

## Consequences

- A filled kelvin is labeled as filled, with the search radius, in provenance (`D-20261114-pj-de42`).
- This record does not make relief or a crater a minimum that zeros the score.
