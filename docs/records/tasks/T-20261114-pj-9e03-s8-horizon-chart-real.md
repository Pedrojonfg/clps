---
id: T-20261114-pj-9e03
title: "S8 horizon chart on real Site01 data"
kind: task
owner: pj
branch: scope/ops-skeleton
created: 2026-11-14T17:05:00Z
stage: done
relates: [T-20261114-pj-e01c, D-20261114-pj-da5f, D-20261114-pj-aa58]
---
# S8 horizon chart on real Site01 data

## Goal

Plan S8 done: `/site` and the horizon page show Site01 mask silhouette, Sun/Earth tracks, case strip, and score from local kernels and the D-f369 DEM schedule when data is present (`D-da5f`).

## Triage

- Own/advise: none new; `chart_site` = Site01 (`D-da5f`).
- Plumbing: wire `api/app.py` to `lunar_eval` pipeline; keep mock fallback when `data/dem` or kernels missing (CI).

## Pending checkpoint

Implementation checkpoint — S8 real `/site`: approved by pj ("venga, pues /decision-flow de S8") 2026-11-14.

Scope: add `lunar_eval/site01.py` (mask schedule, sky, series, score payload); switch `GET /site` to real path when files exist; update `web/index.html` labels and case-strip thresholds for fractional visibility; extend API test with optional real-data assertion. Out: query params, hazards in score, 1 km cap, basemap, layer-2 weights.

## Orientation

- Concepts: visibility series (prerequisite); horizon chart (core).
- Facts: mock API + chart UI already pass contract tests; E2E in `test_dem_site.py`.

## Decisions

- D-20261114-pj-8588 — S8 planner UI defaults (ten templates, percent lit, hazards toggle, error on failure)
- D-20261114-pj-aa58 — Interactive demo: live sky, cached mask, user date/needs and templates
- D-20261114-pj-da5f — Next build scope is the horizon chart on real data for one site
- D-20261114-pj-9e53 — API field shapes
- D-20261114-pj-f369 — mask schedule
- D-20261114-pj-4ffe — SpiceEphemeris
- D-20261114-pj-de42 — score

## Auto decisions

| Choice | Reason |
|--------|--------|
| `GET /site?mock=1` only for CI mock | per D-8588 |
| Mask cache files under `data/masks/{lat}_{lon}_oh2.0.npy` | per D-aa58 |

## Fog

## Out of scope

- Layer-B hazards on `/site` (neutral `{}` until wired).
- `score_layer2`, demo site refinement, ephemeris library record formalization.

## Build

2026-11-14a: first real `/site` slice. 2026-11-14b: planner API + UI per `D-aa58`/`D-8588` (`planner_templates.py`, `planner_payload.py`, `mask_store.py`, `dem_schedule.py`, form in `web/index.html`). pytest 62 passed, 1 skipped (~6.5s) 2026-11-14.

## Audit

2026-11-14b aligned with D-aa58 and D-8588. Layer-2 score weight still 0 in engine (`D-de42` deferred). Surface hazard score limits use defaults when hazards on (`max_temperature_k` 320) until template fields added.

## Detours

- 2026-11-14: pj product intent (coords, demo button, live sky, cached mask, templates) recorded in `D-20261114-pj-aa58` after S8 build.