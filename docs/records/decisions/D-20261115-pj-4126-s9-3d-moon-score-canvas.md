---
id: D-20261115-pj-4126
title: "S9 canvas is an orbitable 3D Moon with scores painted on it"
date: 2026-11-15T10:50:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-33ca
concepts: [region score heatmap, first-person viewer]
supersedes: []
relates: [T-20261114-pj-12b7, D-20261115-pj-834a]
ai: options+critique
---
# S9 canvas is an orbitable 3D Moon with scores painted on it

## Context

Agenda item “basemap” meant a 2D underlay (relief/tiles) under a heatmap. pj rejected that framing: the product view should be a 3D Moon the user can drag and orbit, with scores painted on top. First-person site view remains plan S10 / open `T-12b7` viewer item, separate from this region map.

## Framing

Trade a simple 2D map ship for a defendable 3D region canvas that matches the portfolio story; keep S10 (eye-level at one site) out of this decision.

## Options considered

1. **A — 2D heatmap only (cells, optional flat basemap)**: assumes fastest S9; consequence: no orbitable Moon.
2. **B — Orbitable 3D Moon with score layer painted on it; S10 first-person stays separate**: pj's choice after the basemap clarification.
3. **C — Defer 3D; ship 2D now**: assumes calendar risk; consequence: mismatches pj's stated representation.

## Decision

**B.**

## Rationale

Not a 2D underlay — want a 3D Moon you can drag/orbit, with scores painted on it.

## Checks raised

- 3D Moon may perform badly in user feedback → accepted for now; not treated as a big problem yet.
- Library/engine choice (Three.js, Cesium, etc.) → deferred to Build as advise/dependencies unless licence or hosting blocks.

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_canvas | orbitable_3d_moon | Drag/orbit required |
| region_map_score_layer | painted_on_3d_moon | Per S9 color decisions |
| region_map_vs_s10 | s10_first_person_separate | Do not fold eye-level site view into S9 |
| region_map_3d_library | three_js_plus_real_moon_texture | pj 2026-11-15: real Moon imagery on the globe (not a blank sphere); low cost, high UI value |
| region_map_moon_asset | public_domain_or_nasa_derived_texture | Served from `web/` or documented CDN; no QuickMap runtime |

## Expected behavior and validation

Wrong if the 3D Moon performs badly in user feedback (accepted for now).

## Consequences

- Closes “basemap” for S9 in favour of a 3D canvas; 2D-only underlay is out for this scope.
- `T-12b7` basemap/viewer agenda should cite this for the region map and keep first-person open.
