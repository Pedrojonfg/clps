---
id: D-20261115-pj-f2d3
title: "S10 camera: 2 m observer, S8 site/time sync, limited look-around"
date: 2026-11-15T11:23:57Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: architecture
task: T-20261115-pj-2b7a
concepts: [site×time sky geometry, first-person viewer vs orbit globe]
supersedes: []
relates: [D-20261115-pj-ac34, D-20261115-pj-7d58, D-20261114-pj-f369, D-20261114-pj-aa58]
ai: recommended
---
# S10 camera: 2 m observer, S8 site/time sync, limited look-around

## Context

First-person view (`D-ac34`, `D-7d58`) needs observer height, whether time/site match S8, and whether the user can look around. Mask precompute and Site contracts use observer height 2 m.

## Framing

Keep v1 simple and consistent with stored masks; leave richer camera UX for later.

## Options considered

1. **A — 2 m + S8 sync + limited look-around** (recommended): coherent with masks; little “game”.
2. **B — Editable height in UI**: more pedagogy; more edge cases.
3. **C — Fixed demo time, decoupled from S8**: easier wiring; weaker product story.
4. **D — Free drone flight**: wow; not lander first-person.

## Decision

**A**, with editable height deferred.

## Rationale

Accepted the recommendation: for now 2 m; whether to expand later is open; choose simplicity. Confirmed proposed additions: site/time from S8; Cesium look-around with limited pitch; editable height deferred.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_observer_height_m | 2 | Same as mask / precompute default |
| s10_observer_height_ui | deferred — decide if/when expanding beyond 2 m | |
| s10_site_time_source | s8_shared_ui_or_query | Same site and hour as horizon chart |
| s10_look_around | cesium_yaw_pitch_ground_constrained | No free drone flight in v1 |

## Expected behavior and validation

Camera sits 2 m above the site, shows Sun/Earth for the S8-selected time, and allows looking around without flying. Wrong if height drifts from mask convention without a recorded change, or if sky time diverges from S8 silently.

## Consequences

- `web/firstperson.*` reads the same site/time parameters as S8.
- Changing observer height later is a new decision (and may need mask sets at that height).
