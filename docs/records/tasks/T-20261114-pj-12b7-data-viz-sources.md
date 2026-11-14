---
id: T-20261114-pj-12b7
title: "Choose data and visualization sources for the evaluator"
kind: decide
owner: pj
branch: docs/product-ledger-portfolio
created: 2026-11-14T11:17:52Z
stage: decide
relates: [T-20261114-pj-a1b2]
---
# Choose data and visualization sources for the evaluator

## Goal

Done means: the sources that feed the score, the horizon, the maps, the first-person view, and layer-B hazards are recorded as decisions (or explicitly deferred). Then the project documentation gets a clean resource catalogue that cites those decisions. Origin: pj asked which official challenge resources (QuickMap, Moon Trek, Horizons, CSA) and which other data/repos to use, and to document them once nothing is left to decide.

## Triage

- Own/advise parts: weekend frame vs portfolio scope (own, scope); geometry and horizon data path (own, data & sources / method); role of long-term average maps (own, data & sources); kernel/frame provenance (own, data & sources); first-person viewer and basemap libraries (advise, dependencies & ops / licences).
- Plumbing: resource catalogue doc, attribution text, citation list (after decisions).

## Pending checkpoint

Decisions 1–3 and hosting recorded (D-d7d9, D-4ffe, D-f369, D-5994). Horizon-decision history: evidence and pj's answers are in D-20261114-pj-f369 (Context, Checks raised); test scripts were run from /tmp and will be ported into the test suite. Now: redo the implementation plan with /shape-up on top of the recorded decisions (pj: "analiza el plan de implementación del repo y cámbialo con total libertad"), including `hack_submission_cut`. Remaining agenda (open, answered by the plan's spikes or later): (4) role of PGDA 69 averages (own); (5) kernel version / frame / library (own + advise); (6) first-person viewer (advise); (7) basemap (advise).

Agenda accepted by pj 2026-11-14 without changes. Warm-up answered ("ni idea"); graded shaky in U-20261114-pj-3839.

## Orientation

- Concepts: ephemeris (core), topographic horizon mask (core), DEM resolution (core), long-term average illumination (hazard), reference frame / kernel version (prerequisite), WMTS tiles (prerequisite), 3D Tiles streaming (prerequisite), licence terms (hazard), appetite (core).
- Facts gathered: `docs/research/briefs/research-brief-data-viz-sources.md` (written before decision-flow mode; its recommendations in own domains do not bind).
- Decisions surfaced: see agenda in chat; recorded below as they land.

## Decisions

- D-20261114-pj-d7d9 — Portfolio scope governs through 20 Nov; Space Apps submission on 15 Nov as a cut (supersedes D-20261114-pj-7e2a)
- D-20261114-pj-4ffe — Sun/Earth geometry computed locally from kernels; Horizons as test oracle
- D-20261114-pj-f369 — Horizon mask from LOLA DEMs with a distance-graded resolution schedule to 250 km
- D-20261114-pj-5994 — Precompute on pj's PC for the demo, then a Hetzner CX43 for the full cap and serving (advise)
- D-20261114-pj-a3b3 — Space Apps submission targets the full portfolio scope; fallback cut only at the Sunday freeze

## Auto decisions

| Choice | Reason |
|--------|--------|

## Fog

- Temperature and dust models (engine ledger per D-20261114-pj-9f04); source facts are in the brief.
- Candidate site list beyond PGDA 78 named sites.
- Search granularity and method (time step, site spacing, neighborhood rules): pj wants rules plus experiments to set them, in whichever scope it lands (engine ledger / recommender).

## Out of scope

- QuickMap or ACT software at runtime (proprietary viewer; used only by eye).
- CSA portal as a data source (outreach; no lunar DEM or ephemeris).
- Trajectory products (D-20261114-pj-b8d3).

## Build

`docs/resources.md` — resource catalogue citing the decisions; open items marked Pending decision.

## Audit

pending

## Detours

- `docs/plans/2026-11-14-hackathon-lite-plan.md` excluded DEM masks and SPICE; rejected by D-20261114-pj-d7d9 and replaced by the /shape-up replan.
