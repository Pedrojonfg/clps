---
id: T-20261114-pj-03a6
title: "Specify and build S6 local search"
kind: task
owner: pj
branch: scope/ops-skeleton
created: 2026-11-14T18:43:47Z
stage: audit
relates: [T-20261114-pj-8138, D-20261114-pj-de42, D-20261114-pj-6ce5, D-20261111-pj-60ab]
---
# Specify and build S6 local search

## Goal

Done means: local search (nearest feasible time; better neighbours within a radius; honest "none") is specified with recorded values, then built and checked against those records. Origin: pj `/decision-flow de s6` after S3/S4 decisions; plan scope S6 depends on S4 green and on `score_layer1_tune_when` (`D-6ce5`).

## Triage

- Own/advise parts: search objective among infeasible points (`score_infeasible_signal`, deferred in `D-de42`); neighbourhood radius and candidate set; tie-breaks in time; what "better" means among feasible neighbours; validation bar for S6 (own, method & validation). Scope of S6 vs S7 cut (`D-a3b3`) if needed (own, scope). API/UI contract for returning local-search results (advise, contracts).
- Plumbing: existing `lunar_eval/search/local.py` and `tests/test_search.py` already stub nearest time and better neighbours with `score(..., {})`.

## Pending checkpoint

None.


## Orientation

- Concepts: needs-adapted score (prerequisite, `D-7520`/`D-7af3`); local neighborhood search (core, `D-60ab`); nearest feasible time (core); neighbour radius / candidate set (core); infeasible-search signal (hazard — silent walk among zeros); search vs deep search boundary (hazard — S6 absorbing S7).
- Facts: plan S6 = nearest feasible time; better neighbours ±N km; or honest none. Code stub ranks by |Δt| among feasible windows and by score among neighbours inside `radius_km`; hazards `{}`; no API. `score_infeasible_signal` deferred to lock with S6. `D-6ce5` tune before S6 green. S3/S4 decide done; engine edits still dirty.
- Decisions surfaced: infeasible signal; radius/candidates; time tie-break; “better” neighbour rule; S6 validation; API shape (advise).
- Approach: pj — after concept review, ready to decide (no detailed approach sketch).

## Decisions

- D-20261114-pj-5577 — Infeasible search ranks by R×bonus; UI shows zero plus impossible score
- D-20261114-pj-9cc5 — Local time search slides the window by ±h with a leaderboard
- D-20261114-pj-72bc — Local neighbour scan: 5 km grid, always, rank by score or companion
- D-20261114-pj-f57e — Local search uses request hazards; temp/dust gaps starred on the board
- D-20261114-pj-52bd — S6 validation: synthetic tests plus one Site01 search E2E
- D-20261114-pj-ecc9 — Local search results ride on GET /site as local_search block

## Auto decisions

| Choice | Reason |
|--------|--------|
| Keep `lunar_eval/search/local.py` + synthetic tests | agenda OK |
| Polar-stereo km distance | matches stub; agenda OK |
| `local_search` query default off unless UI requests it | keep `/site` light; `D-ecc9` flag |

## Fog

- Exact neighbour radius vs compute until candidate source is clear.
- Whether S4+bonus implementation and the `D-6ce5` tune experiment must finish before Build (records: before S6 *green*, not before Decide).

## Out of scope

- S7 deep search ranges and stopping rules (plan P14).
- 1 km cap precompute as a deliverable of this task (`D-da5f` following scope).
- Reopening layer-1 formula (`D-7520`) except as consumed by search ranking.
- Bonus tune experiment itself (`D-6ce5`) — gate before green, separate work.

## Build

2026-11-14: S6 implemented. score companion + hazard_gap_star; local_search slide±h + 5km; `/site?local_search=1`; UI board. pytest parent re-run: target suite green (1 skip without Site01 data); full suite green. Out: bonus tune (D-6ce5), 1km neighbour grid (time-only when absent).

## Audit

## Detours

- Open task `T-20261114-pj-12b7` remains on `docs/product-ledger-portfolio`; not resumed.
- Working tree still carries uncommitted S3/S4 decide records and engine edits from `T-8138`.
- 2026-11-14: pj paused approach question to review all concepts first (large project, forgets pieces).
