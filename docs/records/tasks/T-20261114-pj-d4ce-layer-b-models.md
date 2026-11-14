---
id: T-20261114-pj-d4ce
title: "Lock layer-B temperature and dust models"
kind: decide
owner: pj
branch: scope/ops-skeleton
created: 2026-11-14T14:43:11Z
stage: decide
relates: [T-20261114-pj-b63a, T-20261114-pj-12b7]
---
# Lock layer-B temperature and dust models

## Goal

Done means: temperature and dust each have a recorded quantity (or an explicit "not modelled" that pj defends), planner limits on those quantities are layer-0 minima or layer-2 factors, and every value S5 must return is decided or deferred with how and when. No implementation in this task. Origin: pj chose P13 as the next decide-only scope after Phase 0 (`D-de42` parks `score_surface_as_minima` here).

## Triage

- Own/advise parts: which temperature and dust quantities exist (own, data & sources / method & validation); whether planner limits fail-close or only rank (own, method & validation); what a hazard number is allowed to claim (own, claims & interpretation); `SurfaceHazardProvider` fields once the quantities exist (advise, contracts).
- Plumbing: none in this pass. Updating `docs/resources.md` waits until the decisions exist and should not be edited from this branch unless asked.

## Pending checkpoint

Decision `own`: qué número es la temperatura — awaiting falsification. Heard: day bin if day, night bin if night; if the exact point is missing, distance-weighted mean of the two nearest. Sun-angle question held until after this answer. No options shown.

## Orientation

- Concepts: layer-B in the score (hazard); minima and feasibility (core); climatology (core); hazard proxy (core); provenance (hazard).
- Facts: `docs/resources.md` and the source brief. No public series predicts temperature at an arbitrary future hour. No public site×time dust lofting field. The brief's "honest use" column does not bind (`T-12b7`).
- Decisions surfaced: temperature quantity; dust quantity; role of planner limits; related slope/roughness/PSR terms; provider fields.

## Decisions

## Auto decisions

| Choice | Reason |
|--------|--------|

## Fog

- Numeric weights and how layer 1 and layer 2 combine (`score_layer_combination`, `score_layer1_quantity`): S4, `D-de42`.
- Signal among all-zero scores: S6, `D-de42`.
- Exact PDS product id, and what happens when a pixel is missing: inside the model decision if a grid is chosen, otherwise deferred to the precompute.
- Demo site, ephemeris library, first-person viewer, basemap.

## Out of scope

- Implementing S5.
- Trajectories.
- Mars dust.
- Role of PGDA 69 averages.
- Viewer and basemap.

## Build

Decide only. No code.

## Audit

pending

## Detours

- `T-12b7` on `docs/product-ledger-portfolio` still lists temperature and dust under Fog. It is not deciding them. This task owns P13; that task cites the records after they exist.
- P13 is a global choice. Records are written on `scope/ops-skeleton` and need to reach the default branch before another branch cites them.
