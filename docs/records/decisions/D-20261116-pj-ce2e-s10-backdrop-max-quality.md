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

## Checks raised

- Finest tiles cost network and GPU → tile cache raised; a "Loading terrain" hint shows while tiles refine.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_resolution | native_device_pixels (capped at 2×) | |
| s10_msaa_samples | 4 | Where WebGL2 is available |
| s10_tileset_max_screen_space_error | 1 | Finest practical level of detail |
| s10_backdrop_source | unchanged | `D-7d58` |

## Expected behavior and validation

Wrong if the view becomes unusably slow on the owner's machine; then relax the tile error first.

## Consequences

- A DEM-based own terrain mesh is the follow-up if more fidelity is wanted.
