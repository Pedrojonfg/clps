---
id: D-20261115-pj-ac34
title: "S10 hybrid: third-party backdrop plus explicit our mask and sky"
date: 2026-11-15T11:20:05Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-2b7a
concepts: [topographic horizon mask, site×time sky geometry, photo-real look vs geometry-true placement, external tiles as if our score mask]
supersedes: []
relates: [D-20261115-pj-4126, D-20261115-pj-8c03, D-20261115-pj-4494, D-20261114-pj-aa58, T-20261114-pj-12b7]
ai: options+critique
---
# S10 hybrid: third-party backdrop plus explicit our mask and sky

## Context

S10 needs a first-person site view. S9 is already an orbitable Moon (`D-4126`). S8 can supply mask and Sun/Earth geometry. Options ranged from mask-only panorama to third-party globes. pj asked for the option brief before choosing.

## Framing

Trade visual impact (helps a final user grasp product complexity) against honesty about what is our model versus external basemap.

## Options considered

1. **A — Our geometry only** (mask + S8 sky; panorama / 2.5D): cleanest claim; least spectacle.
2. **B — Our DEM mesh + our sky**: our relief; more build time; no ion dependency.
3. **C — Third-party globe/tiles + our sky on top**: spectacle; licence/CORS; easy to misread as our terrain model.
4. **D — Hybrid**: third-party backdrop + explicit “our mask / our sky” layer: spectacle with labeled provenance.

## Decision

**D — Hybrid: impressive third-party backdrop, with our horizon mask and sky kept visibly separate and honest.**

## Rationale

C–D because an impressive UI helps the end user understand the complexity behind the product, but honesty must be kept. Confirmed D after checks: visible labeling of what is ours is required, not look alone.

## Checks raised

- Falsification was only aesthetic (“if it did not look good”) → honesty hazard remains: confusion between third-party relief and our model → mitigated by mandatory on-UI provenance for our mask/sky.
- Engine (Cesium vs Trek vs other) still open → advise viewer-stack decision.
- Demo may use mocked mask/sky under `D-4494` → UI/docs must not imply live cap serving.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_view_composition | hybrid_thirdparty_backdrop_plus_our_geometry | |
| s10_our_layers | horizon_mask; sun_earth_from_site_geometry | From S8 contract / mocks until real |
| s10_backdrop_role | visual_context_only | Not the score; not the mask |
| s10_provenance_ui | required_visible_labels | State what is ours vs backdrop |
| s10_backdrop_engine | cesiumjs_cesium_moon | Filled by `D-7d58` |
| s10_cut_fallback | mask_panorama_2d | Filled by `D-ac74` |

## Expected behavior and validation

Wrong if it did not look good enough to serve that understanding role.

## Consequences

- Build must ship labels/copy that separate backdrop from our geometry.
- Claims must not say the third-party terrain *is* the evaluator model.
- Viewer library choice and ion/Trek constraints come next.
