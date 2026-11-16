---
id: D-20261115-pj-7d58
title: "S10 backdrop engine is CesiumJS with Cesium Moon"
date: 2026-11-15T11:21:38Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: dependencies & ops
task: T-20261115-pj-2b7a
concepts: [Cesium ion / non-commercial licence fit, first-person viewer vs orbit globe]
supersedes: []
relates: [D-20261115-pj-ac34, D-20261115-pj-4126, D-20261114-pj-7e2a, D-20261115-pj-4494]
ai: options+critique
---
# S10 backdrop engine is CesiumJS with Cesium Moon

## Context

`D-ac34` requires a third-party visual backdrop plus labeled our mask/sky. Candidates: Three.js + baked NASA imagery, Cesium Moon via ion, Moon Trek WMTS, or mask panorama only. S9 already uses Three.js for the orbit map. `docs/resources.md` documents ion Community limits (personal non-commercial / unfunded education; not funded research or commercial).

## Framing

Pick a backdrop stack that can look impressive under `D-ac34` and still ship under static-demo deploy (`D-4494`), with licence honesty for a solo portfolio.

## Options considered

1. **A — Three.js + hosted/baked NASA imagery + our overlays** (AI recommended): reuse S9 stack; simple static deploy; less “globe product”.
2. **B — CesiumJS + Cesium Moon (ion) + our overlays**: max spectacle; ion token; Community plan constraints.
3. **C — Three.js + live Moon Trek WMTS**: no ion; browser CORS often needs a proxy (conflicts with mask API out).
4. **D — Mask panorama only**: fastest honest cut; little wow.

## Decision

**B — CesiumJS with Cesium Moon as the backdrop; our mask and Sun/Earth overlays per `D-ac34`.**

## Rationale

Accepted B over the AI recommendation: the project is portfolio-only and pj does not plan to charge for it, so the ion Community framing is acceptable.

## Checks raised

- If framing later becomes funded research or a paid product → ion plan may no longer fit; reopen this decision.
- Ion access token must stay out of git (`D-5994` / `D-8c03` secret rule).

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_backdrop_engine | cesiumjs_cesium_moon | Fills deferred from `D-ac34` |
| s10_cesium_ion_asset | 2684829 | Cesium Moon per resources catalogue |
| s10_ion_token_storage | environment_or_local_config_not_in_git | |
| s10_ion_plan_assumption | community_personal_non_commercial_portfolio | Reopen if monetized or funded-research framed |
| s10_attribution | required_cesium_and_nasa_usgs_as_applicable | On-page credit |

## Expected behavior and validation

Portfolio demo runs with Cesium Moon backdrop and labeled our geometry; no ion token in the repository. Wrong if the published framing needs a paid ion plan or if tokens leak into git.

## Consequences

- `web/firstperson.*` (or equivalent) loads CesiumJS; S9 may stay on Three.js.
- Build needs a documented way to inject the ion token for local/demo without committing it.
- Cut fallback panorama (`D-ac34`) remains if ion or Cesium integration fails before demo.
