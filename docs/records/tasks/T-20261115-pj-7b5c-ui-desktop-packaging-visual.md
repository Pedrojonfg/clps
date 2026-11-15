---
id: T-20261115-pj-7b5c
title: "Decide desktop product packaging and visual system"
kind: decide
owner: pj
branch: scope/s12-s14-s15-validation-claims
created: 2026-11-15T12:21:55Z
stage: done
relates: [D-20261115-pj-8c03, D-20261115-pj-2533, D-20261115-pj-4494, D-20261115-pj-8fd2, D-20261114-pj-9f04, D-20261114-pj-aa58]
---
# Decide desktop product packaging and visual system

## Goal

Close the product client form (desktop on user hardware; VPS/masks-only already in `D-8c03`) and the visual design authority (industrial / Blueprint-class constraints) so UI work stops being ad-hoc CSS on a static web stub. Decide-only: records, no build this task.

## Triage

- Own/advise parts: product packaging and role of the static demo (scope); visual non-negotiables and design authority (presentation / claims); desktop shell and Blueprint adoption path (architecture / dependencies & ops).
- Plumbing: none in this decide pass.

## Pending checkpoint

None.

## Orientation

- Concepts: client compute vs server compute (prerequisite, from `D-8c03`); product desktop shell vs portfolio static web (core); design-system authority vs ad-hoc styling (core); silent AI-slop drift from half-following a kit (hazard); embedding a data-dense toolkit inside a desktop shell (hazard).
- Approach (pj, prior chat): industrial / aerospace-ops look; no glass, gradients, serif, rounded corners; Palantir Blueprint as strict visual authority; product = desktop app on user hardware, VPS only for masks — not a web app.

## Decisions

- D-20261115-pj-cc6f — Product client is desktop-primary on user hardware
- D-20261115-pj-c973 — Static web/Pages are not the product; desktop is the priority
- D-20261115-pj-01b0 — UI look follows Blueprint strictly for now
- D-20261115-pj-bdaf — Desktop shell is Tauri
- D-20261115-pj-50a5 — Blueprint via React in the Tauri webview
- D-20261115-pj-b6fe — UI tokens: Blueprint dark theme and kit defaults

## Auto decisions

| Choice | Reason |
|--------|--------|
| Package/folder naming when a desktop shell exists | Hygiene only |
| Prefer Blueprint tokens over inventing parallel CSS variables once Blueprint is accepted | Matches design-authority queue |
| `ui_front_location` = `desktop/` (repo root) | Fills deferred from `D-50a5`; implementa hygiene |

## Fog

- Exact installer / update channel; mask API contract (`D-3832` deferred); Cesium/ion token handling inside a packaged desktop binary.

## Out of scope

- Native mobile (`D-9f04`); rewriting the evaluator into Dash; inventing a custom design system from scratch this pass.

## Decide agenda

OK 2026-11-15 (pj): queue 1–6 as proposed; item 3 kept own for portfolio defense; explain calmly before first Decision.

## Detours

- Task opened on `scope/s12-s14-s15-validation-claims` while S10/S11 records and `web/firstperson.*` sit uncommitted on the working tree; packaging/UI is a global choice — prefer landing these `D-` records toward `main` (or a dedicated docs branch) rather than burying them only in validation-claims history.
