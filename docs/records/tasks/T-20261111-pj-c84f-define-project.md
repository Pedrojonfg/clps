---
id: T-20261111-pj-c84f
title: "Understand the CLPS challenge and its data, then decide what the project consists of"
kind: task
owner: pj
branch: main
created: 2026-11-11T11:33:27Z
stage: done
relates: [U-20261111-pj-9197]
---
# Understand the CLPS challenge and its data, then decide what the project consists of

## Goal

Done means: the owner understands the problem and the available data well enough to explain and defend the foundational decisions (question, scope, method, data, claims), those decisions are recorded, and a team can be recruited around them. Nothing is built in this task.

## Triage

- Own/advise parts: problem framing, scope and success criteria, method and validation, data and sources, claims, team and roles (own); rules and eligibility, presentation (advise).
- Plumbing: repo layout, record files.

## Pending checkpoint

None. Product ledger closed 2026-11-11 (owner): claims/team deferred; engine → future ledger.

## Decisions

Product ledger closed. Accepted: D-20261111-pj-ea51, D-20261111-pj-60ab, D-20261111-pj-5cf6. Deferred to later: claims, team; engine ledger (metrics, recommender, data/horizon, technical validation).

## Orientation

- Concepts (dependency order; sources in chat):
  - `prerequisite` — Space Apps 2026 format, judging pressure, 48h scope (`project.md` milestones; judging guide not yet in repo)
  - `prerequisite` — CLPS program and south-pole mission constraints (NASA CLPS landing sites page; challenge mirrors)
  - `prerequisite` — Official challenge brief archived: compare sites/dates; Sun & Earth vs local horizon; power & DTE (`docs/sources/challenge-statements/`)
  - `core` — Horizon-relative geometry (elevation, azimut as projection, line-of-sight)
  - `core` — Four visibility cases; DTE vs relay
  - `core` — Ephemerides path (Horizons / SPICE / precomputed maps)
  - `hazard` — Spherical horizon only vs LOLA terrain
  - `hazard` — Confusing trajectory/launch geometry with site local sky
- Decisions surfaced (not recorded yet):
  - Primary user: mission planner first
  - Product lean: recommender + flexibility + multi-viz; de-emphasize educator/public accessibility in v1
  - Four-case time budget as core metric framing

## Auto decisions

| Choice | Reason |
|--------|--------|

## Fog

- Official Resources tab empty (2026-11-11); concrete dataset URLs may appear later.
- Hands-on Horizons query not yet done (debt on `U-20261111-pj-9197`).
- 2026 judging/eligibility guides not read in repo.
- Engine ledger (not this task): score/X,Y,Z, recommender internals, data/horizon path, technical validation.
- Product optional still: claims, team & roles.

## Out of scope

- Building the app in this task.
- Full EDL / dust / temperature (layer B) unless a later decision expands scope.

## Build

Not started.

## Audit

pending

## Detours

- 2026-11-11: the repo was empty, so `project.md` and `people/pj.md` were committed directly to `main` in their own commit, before this task file (no PR).
- 2026-11-11: advanced to Decide after orientation; owner correctly blocked — product queue premature without domain facts. Back-edge to Understand; research brief + full statement + TikZ guide.
- 2026-11-11: orientation closed after geometry Q&A; return to Decide. Deferred numeric Horizons walkthrough into data decision / debt.
