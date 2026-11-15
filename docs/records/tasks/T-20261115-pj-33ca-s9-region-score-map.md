---
id: T-20261115-pj-33ca
title: "Specify and build S9 region score map"
kind: task
owner: pj
branch: scope/s9-region-map
created: 2026-11-15T10:34:39Z
stage: done
relates: [T-20261114-pj-9e03, T-20261114-pj-12b7, D-20261114-pj-de42, D-20261114-pj-f369, D-20261114-pj-da5f, D-20261114-pj-72bc, D-20261115-pj-48ee, D-20261115-pj-85bf, D-20261115-pj-8acb, D-20261115-pj-7227, D-20261115-pj-834a, D-20261115-pj-4126]
---
# Specify and build S9 region score map

## Goal

Plan S9 done: score map on an orbitable 3D Moon; paint local/deep evaluated points (induce if partial); click/lift → solid sample + horizon chart; deep-search best highlighted when present. Origin: pj `/decision-flow S9`.

## Triage

- Own/advise parts: paint set, color semantics, absolute scale, fill/lift, 3D canvas (recorded below).
- Plumbing: region API payload, wire to S8 `/site`, front-end map module.

## Pending checkpoint

None.

## Orientation

- Concepts: needs-adapted score (prerequisite); local-search candidate set (prerequisite); absolute score color scale (core); cell fill / nearest-sample paint (core); relative stretch of this query's scores (hazard); smooth fill inventing mid-scores between sparse points (hazard); map looks like illumination climatology (hazard).
- Facts: no prior `web/map.*` / `/region`; S8 = `web/index.html` + `GET /site`; layer-1 feasible scores ~0…1.4; S7 sibling may supply deep payloads.
- Approach (pj): recorded in D-85bf…D-4126.
- Pace note: UI/taste batched in one audio pass.

## Decisions

- D-20261115-pj-85bf — Paint evaluated points; induce only under partial search
- D-20261115-pj-8acb — Infeasible black + in-query dots; feasibles use UI score RYG
- D-20261115-pj-7227 — Absolute RYG gradient; clamp above ceiling to green
- D-20261115-pj-834a — Interpolate overview; solid color on lift
- D-20261115-pj-4126 — Orbitable 3D Moon canvas (S10 separate)

## Auto decisions

| Choice | Reason |
|--------|--------|
| Click cell → reuse S8 `/site` + chart with map needs/time and cell lat/lon | pj: pure plumbing; no product fork |
| Batch UI decide + English rationale confirm before save | pj pace; language rule |
| Serve `/map.html`, `/map.js`, `/assets/*` from FastAPI | plumbing so the page loads under uvicorn |
| Yellow mid-stop = 0.7; induce 4-neighbour ±1 km stereo; opacity 0.45 | approved Proposed additions |
| Moon texture: Solar System Scope 2k_moon.jpg vendored as `web/assets/moon.jpg` | pj wanted real Moon; fits `D-4126` |

## Fog

## Out of scope

- S10 first-person; PGDA climatology as score color; closing S7; trained ML model for the map.

## Build

2026-11-15: `lunar_eval/region_map.py` + `POST /region-map`; `web/map.html` + `map.js` + Moon texture; static routes; infeasible `marker_t` wired. Parent pytest: `tests/test_region_map.py` + `test_api_region_map.py` + `test_api_site.py` green (1 skipped). `test_hazards.py` raster failure pre-existing / unrelated.

## Audit

2026-11-15: matches D-85bf/8acb/7227/834a/4126. Fixed gap: infeasible relative dots (`marker_t`) were computed but not in payload/UI — wired. Fixed front RGB 0–255 vs Three/CSS. Citations to S7-only `D-54f0`/`D-c159` on this branch flagged by `check` (relates trimmed). No remaining own-domain unrecorded choices found in the S9 diff.

## Detours

- Branched from `scope/s6-layer1-tune` onto `scope/s9-region-map`.
- “Basemap” reinterpreted as 3D Moon canvas (`D-4126`); pj amended blank sphere → real Moon texture at implement time.
- `check` warns S7 decision cites exist only on `scope/s7-deep-search` — merge before relying on deep-search highlight end-to-end.
- 2026-11-15: pj opened S10/S11 (`T-2b7a`, `T-5200`) while this task still needs Close (`flow.py check` / stage done).
