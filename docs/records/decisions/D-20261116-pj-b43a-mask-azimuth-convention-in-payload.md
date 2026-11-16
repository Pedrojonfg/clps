---
id: D-20261116-pj-b43a
title: "Site payload states the mask azimuth convention and every view converts it"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: ai
status: accepted
mode: advise
domain: contracts
task: T-20261116-pj-9eee
concepts: [azimuth convention between modules]
supersedes: []
relates: [D-20261114-pj-f369, D-20261114-pj-9e53, D-20261114-pj-aa58]
ai: recommended
---
# Site payload states the mask azimuth convention and every view converts it
## Context

Found while rebuilding the planner view (2026-11-16). The horizon mask array is indexed by an azimuth measured from the direction of the pole, turning the other way from geographic azimuth: `mask_az = (180° − geographic_az) mod 360°` (`lunar_eval.visibility._mask_el_at_geo_az`). The scored series applies this correctly. The planner chart and the first-person view did not: they drew mask index `i` at geographic azimuth `i × 0.5°`. Checked on PGDA Site01 with real data over 49 hourly samples: with the conversion, "Sun centre above the mask" agrees with `sun_fraction > 0.5` in 49 of 49; drawn directly, 0 of 49. The mock payload hid this because it built its mask directly in geographic azimuth.

## Framing

The numbers were right and the pictures were wrong; the contract did not say which azimuth the array uses.

## Options considered

1. **Convert in each view, undocumented**: consequence: the next view repeats the mistake.
2. **State the convention in the payload (`mask.azimuth_zero_deg`, `mask.azimuth_sign`) and convert in one helper per front end; make the mock use the same convention**: consequence: a small additive contract change.
3. **Re-index the array to geographic azimuth in the API**: consequence: the payload would differ from stored masks and from what the series code reads.

## Decision

**2.**

## Rationale

Additive, keeps stored masks and the scoring path untouched, and makes the mock exercise the same conversion as real data so the bug cannot hide again.

## Checks raised

None beyond the test below.

## Values

| Name | Value | Notes |
|------|-------|-------|
| mask_azimuth_zero_deg | 180 | Geographic azimuth of mask index 0 |
| mask_azimuth_sign | -1 | geographic_az = zero + sign × index_az |

## Expected behavior and validation

A test asserts, on the mock payload, that the mask sampled through the stated convention at each Sun azimuth reproduces the payload's own `sun_fraction`.

## Consequences

- Planner panorama, first-person view and its 2D fallback all draw the mask through the conversion.
- Earlier screenshots of real sites showed a mirrored horizon.
