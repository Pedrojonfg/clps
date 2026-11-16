---
id: T-20261115-pj-2b7a
title: "Specify and build S10 first-person view"
kind: task
owner: pj
branch: scope/s9-region-map
created: 2026-11-15T10:59:53Z
stage: build
relates: [T-20261114-pj-12b7, T-20261115-pj-33ca, D-20261115-pj-4126, D-20261114-pj-f369, D-20261114-pj-4ffe, D-20261114-pj-9f04, D-20261114-pj-aa58]
---
# Specify and build S10 first-person view

## Goal

Plan S10 done: eye-level view from a site with terrain and Sun/Earth placed from our geometry at the chosen hour (`web/firstperson.*`). Origin: pj `/decision-flow` for S10 and S11. Closes open `T-12b7` agenda item 6 (viewer).

## Triage

- Own/advise parts: what the view claims to show (scope/claims); viewer stack and licence (advise, dependencies & ops / presentation); how DEM/mask/sky feed the canvas (advise, architecture/contracts).
- Plumbing: page wiring from S8 site params; static assets layout.

## Pending checkpoint

None.

## Orientation

- Concepts: topographic horizon mask (prerequisite); site×time sky geometry (prerequisite); first-person viewer vs orbit globe (core); Cesium ion / non-commercial licence fit (hazard); photo-real look vs geometry-true placement (hazard); external tiles as if they were our score mask (hazard).
- Facts: no `web/firstperson.*`; S9 is orbit Moon (`D-4126`, separate); S8 `GET /site` already carries sky + mask series; P11 still open; plan cut fallback = static panorama from the mask; `docs/resources.md` lists Cesium Moon vs three.js+DEM pending.
- Approach (pj): asked plain-language concept refresh first; open product question how far this is a web app vs local app (ties to S11 where-compute). First-person still to be specified after that framing.
- Pace note: advise-heavy; one meaningful decision at a time (normal checkpoints).

## Decisions

- D-20261115-pj-8c03 — Product remote = masks only; evaluator on client (supersedes D-5994)
- D-20261115-pj-4494 — S11 this tranche: deploy + docs; mask API out (shared)
- D-20261115-pj-ac34 — S10 hybrid backdrop + our mask/sky with visible provenance
- D-20261115-pj-7d58 — CesiumJS + Cesium Moon backdrop (portfolio / non-commercial ion assumption)
- D-20261115-pj-f2d3 — S10 camera 2 m, S8 sync, limited look-around
- D-20261115-pj-2533 — GitHub Pages static deploy (revisit later)
- D-20261115-pj-671e — S10 fidelity / provenance UI (ours vs Cesium)
- D-20261115-pj-e062 — S10 entry coupled to S8 site/time
- D-20261115-pj-ac74 — S10 fallback 2D mask panorama

## Auto decisions

| Choice | Reason |
|--------|--------|
| Names `web/firstperson.*`; `deploy/` layout when needed; reuse `precompute.py` flags | Hygiene / plumbing only |

## Fog

- Exact packaging of a future local app; Hetzner SKU on order day; NAC/ShadowCam texture later.

## Out of scope

- S9 audit reopen; finishing 100 m this session; QuickMap at runtime; copying GPL crater-viewer source; native mobile app (`D-9f04`).

## Decide agenda (shared with T-5200; pj OK 2026-11-15, then expanded)

Global first: (1) product runtime / who computes — own. (2) S11 done this tranche — own.
Then S10: (3) terrain+sky source for the view — own/advise mix → listed as own claims + advise stack. (4) viewer stack+licence — advise. (5) fidelity bar (geometry vs photo-real; external tiles role) — own. (6) camera/observer + controls (height, time sync with S8, look-around) — advise unless claim-changing. (7) entry/wiring from S8/S9 — auto/advise. (8) cut fallback panorama — advise.
Reopened 2026-11-15: items wrongly skipped as “covered/out” return to the queue.
Already decided: (1) `D-8c03` (2) `D-4494` (3) `D-ac34` (4) `D-7d58` (6) `D-f2d3` (11 host) `D-2533`.
Queue complete: (5)`D-671e` (7)`D-e062` (8)`D-ac74` (9)`D-3832` (10)`D-a988` (11b)`D-c30e` (12)`D-573b`.
Auto: `web/firstperson.*` names; `deploy/` layout; `precompute.py` flags.

## Build

2026-11-15 `/implementa`: `web/firstperson.html` + `web/firstperson.js` (Cesium Moon or 2D fallback); routes `/firstperson` + `/firstperson.js`; S8 link with shared query. Tests: `test_firstperson_page_and_script` green with `test_api_site.py`.

## Audit

pending

## Detours

- Opened while `T-33ca` (S9) still at `stage: build` on this branch; warm-up on QuickMap/Moon Trek/Horizons skipped per pj (answered in a prior session).
- Task file currently on `scope/s9-region-map`; a dedicated `scope/s10-…` branch is desirable before merge (note for hand-off).
- 2026-11-15: jumped to implementation checkpoint too early; pj reopened Decide for items 5, 7–10, 11b, 12.
