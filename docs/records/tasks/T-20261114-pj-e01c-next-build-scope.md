---
id: T-20261114-pj-e01c
title: "Choose the next build scope"
kind: decide
owner: pj
branch: scope/ops-skeleton
created: 2026-11-14T16:56:22Z
stage: done
relates: [T-20261114-pj-b63a, T-20261114-pj-d4ce, T-20261114-pj-12b7]
---
# Choose the next build scope

## Goal

Done means: one next build scope is recorded, inside the accepted plan and `D-a3b3`, given what the branch already runs. Origin: pj asked for the next scope and delegated the pick.

## Triage

- Own/advise parts: which accepted plan scope is next (own, scope & success criteria). pj delegated the pick.
- Plumbing: none. This task does not implement.

## Pending checkpoint

None.

## Orientation

- Concepts: scope (core); appetite (core); horizon chart (hazard — the Sunday do-not-cut view is still a mock).
- Facts: plan `docs/plans/2026-11-14-implementation-plan.md`. Branch `scope/ops-skeleton` at 0ec8d82. S1 sky, S3 series, S4 score (layer 2 forced to 0), S5 hazard code, and S6 local search have tests. S2 mask code runs on Site01 DEMs; `scripts/precompute.py` is absent and `data/masks/` is empty. `api/app.py` and `web/index.html` serve a mock. Kernels and the D-f369 DEM stack for Site01 are on disk.
- Approach: delegated. pj asked for the next scope from the plan and the code, without proposing one.
- Decisions surfaced: next build scope.

## Decisions

- D-20261114-pj-da5f — Next build scope is the horizon chart on real data for one site

## Auto decisions

| Choice | Reason |
|--------|--------|

## Fog

- `score_layer1_quantity` and `score_layer_combination` (`D-de42`): `lunar_eval/score.py` uses minimum normalized hour-slack and sets layer 2 to 0. Unrecorded code does not settle those values.
- `ephemeris_library` (`D-4ffe`): the code loads SpiceyPy and the DE440 kernel set. The record still defers the library.
- Demo-site refinement (`D-f369`), basemap, first-person viewer, deep-search ranges (plan P9–P11, P14).
- 1 km cap: the following scope, same night, after this chart runs.

## Out of scope

- Implementing the chart.
- Starting the 1 km precompute inside this decision.
- Editing `project.md` (default branch or its own PR, per `D-d7d9`).
- Resuming `T-20261114-pj-12b7` (other branch; its remaining agenda is not this pick).

## Build

Decide only. No code.

## Audit

decide task: no product code in this task.

## Detours

- Open task `T-20261114-pj-12b7` is on `docs/product-ledger-portfolio`, not on this branch. It was not resumed.
- `project.md` and `README.md` still describe the pre-code portfolio frame. `D-d7d9` already requires a `project.md` edit on the default branch.
