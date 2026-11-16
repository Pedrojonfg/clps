---
id: D-20261116-pj-ce2e
title: "First-person backdrop renders at the highest quality the Cesium Moon asset gives"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: ai
status: accepted
mode: advise
domain: dependencies & ops
task: T-20261116-pj-9eee
concepts: [third-party backdrop resolution limit]
supersedes: []
relates: [D-20261115-pj-7d58, D-20261115-pj-671e]
ai: delegated-by-pj
accepted-by: pj
accepted: 2026-11-16T22:26:00Z
---
# First-person backdrop renders at the highest quality the Cesium Moon asset gives
## Context

pj (2026-11-16): the first-person view should look better; "I do not know what the maximum quality we can get is, but that is what we should aim for." The view used default device resolution handling, no multisampling, a relaxed tile error and a strong albedo lift that flattened the ground to uniform grey.

## Framing

Push the renderer settings to the asset's limit; say plainly where the limit is.

## Options considered

1. **Renderer settings only (native device pixels, MSAA, finest tile level-of-detail, larger tile cache, gentler tone curve, star background)**: consequence: sharper and less flat, same source data.
2. **Swap the backdrop for our own DEM-based terrain mesh**: consequence: a new rendering path and a change to `D-7d58` / `D-ac34`; out of this pass.

## Decision

**1.** The backdrop remains Cesium Moon Terrain (`D-7d58`).

## Rationale

The ceiling is the asset: from a 2 m eye the ground is far coarser than our 5 m DEMs, so close ground stays soft whatever the renderer does. Within that, native-resolution rendering, multisampling and the finest tile selection remove the blur and stair-stepping that settings caused. Option 2 is the real path to a better picture and is recorded as the follow-up.

## Ownership and delegation

Added 2026-11-16T22:26:00Z, when pj accepted this record.

- **What pj decided.** The product, its concepts and all the mathematics behind this view are pj's own decisions: the score and its feasibility rules, the visible-disc series, the horizon mask and the absolute score scale are recorded in pj's own decision records. pj also decided that this part of the interface needed to change, and what it had to achieve.
- **What pj delegated.** The form of the interface. pj delegated it because interface design is outside pj's area of expertise and pj did not consider it necessary to take these decisions personally. The options, the choice and the values in this record were made by the AI.
- **Status of the acceptance.** pj accepts this record knowing that pj did not take these decisions. pj plans to review them and to change whatever pj sees fit later. Any such change must be a new decision record that references this one.

## Checks raised

- Finer tiles cost network and GPU → tile cache raised; a "Loading finer terrain" hint shows while tiles refine.
- Seen at build: the asset renders as plain shaded grey relief with no surface imagery near the eye, so sharper settings cannot add ground detail.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_resolution | native_device_pixels (capped at 2×) | |
| s10_msaa_samples | 4 | Where WebGL2 is available |
| s10_tileset_max_screen_space_error | 2 (was 6), no foveation or dynamic relaxation | 1 was tried at build and kept refining without settling in the test browser |
| s10_backdrop_source | unchanged | `D-7d58` |

## Expected behavior and validation

Wrong if the view becomes unusably slow on the owner's machine; then relax the tile error first.

## Consequences

- A DEM-based own terrain mesh is the follow-up if more fidelity is wanted.
