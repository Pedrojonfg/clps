---
id: T-20261115-pj-2cbd
title: "Specify and build S7 deep search"
kind: task
owner: pj
branch: scope/ops-skeleton
created: 2026-11-15T08:24:53Z
stage: build
relates: [T-20261115-pj-d567, T-20261114-pj-03a6, D-20261111-pj-60ab, D-20261114-pj-9f04, D-20261114-pj-9cc5, D-20261114-pj-72bc, D-20261115-pj-48ee, D-20261115-pj-54f0, D-20261115-pj-e3cf, D-20261115-pj-cb6b, D-20261115-pj-8a25, D-20261115-pj-1ebf, D-20261115-pj-c159, D-20261115-pj-0ee7]
---
# Specify and build S7 deep search

## Goal

Done means: plan P14 (deep-search ranges and stopping rules) is recorded; `lunar_eval/search/deep.py` finds a best site×time over user ranges under that stopping rule and reports runtime; validation matches the recorded bar. Origin: pj `/decision-flow de S7` after S6 tune green (`D-48ee`).

## Triage

- Own/advise parts: what space and time ranges the user specifies (own, method & validation / scope); stopping rule and cost/runtime budget (own, method & validation); how “best” is defined across feasible vs infeasible over large ranges (own, method — cite or reopen `D-5577`); validation bar for S7 (own, method); API/UI contract for deep-search results (advise, contracts).
- Plumbing: module layout under `lunar_eval/search/deep.py`; wiring evaluate/score already used by local search; tests against synthetic grids and one Site01/cap sample if required by the validation decision.

## Pending checkpoint

None.


## Orientation

- Concepts: needs-adapted score / local search ranking (prerequisite, `D-7520`/`D-5577`/`D-48ee`); deep search over user ranges (core, `D-60ab`/`D-9f04`); space×time range specification (core, P14); stopping rule / budget (core, P14); local vs deep boundary (hazard — S6 absorbing S7 or deep becoming local±N); silent incomplete search (hazard — reporting a “best” without saying the search stopped early).
- Facts: S6 green on tune side (`D-48ee`); `lunar_eval/search/local.py` = slide ±h × 5 km neighbours; no `deep.py` yet; `deep_search_methods_intent=ml_dl_rl_later` is intention only (`D-72bc`); cap 1 km on disk; plan cut item 2 if S7 uphill = fixed demo-region brute grid.
- Decisions surfaced: P14 ranges + stopping; validation bar; API contract (advise).
- Approach: pj — user picks full time and space ranges in the UI (UI later); wants a simple explainable optimizer (gradient descent / Ridge / Lasso–style), not a heavy model; notes that user constraints shape the landscape and that with “few variables” they want guidance on how to optimize.

## Decisions

- D-20261115-pj-54f0 — Deep search: total_coverage plus default multi-start hill climb
- D-20261115-pj-e3cf — Optimized deep search starts: regular space-filling grid; user-set N; default TBD
- D-20261115-pj-cb6b — Start default follows wall-clock budget on the execution host
- D-20261115-pj-8a25 — Optimized deep-search default wall-clock budget: 5 minutes
- D-20261115-pj-1ebf — Hill climb neighbours: ±1 precomputed cell and ±1 h; stop at local peak
- D-20261115-pj-c159 — Deep-search range v1: map rectangle snapped to cap cells; hourly starts
- D-20261115-pj-0ee7 — S7 validation: demo bar now; medium megatest tonight
- D-20261115-pj-60a3 — Deep search exposed on dedicated /deep-search endpoint

## Auto decisions

| Choice | Reason |
|--------|--------|
| Cost probe script one-shot in session (not a repo deliverable) | facts for P14; engineering hygiene |

## Fog

- Exact UI widgets for drawing the range box (later / contracts).
- Where deep search executes long-term: server-heavy web vs masks hosted + compute on agency machines (`D-cb6b` deferred `deep_search_execution_host`).
- Polygon ranges after v1 rect (`D-c159`).

## Out of scope

- Pixel-perfect range picker UI.
- Obligatory heavy ML/DL/RL for v1 unless a later decision pulls it in.


## Build

2026-11-15: S7 deep search landed via `/implementa`.
- `lunar_eval/search/deep.py` — `total_coverage` + `optimized` multi-start hill climb (`D-54f0` `D-1ebf` `D-e3cf` `D-8a25`)
- `lunar_eval/horizon/cap_index.py` — rect snap + tile mask load (`D-c159`)
- `POST /deep-search` + CSV format (`D-60a3`); web panel + Download CSV
- `tests/test_deep_search.py` green (parent re-run); API smoke 200 on Site01 rect
- `scripts/megatest_deep_search.py` harness for tonight medium run (`D-0ee7`) — **not executed** this step

## Audit

## Detours

- Closed sibling `T-d567` (tune) as `stage: done` so S7 is not blocked by a stale pending checkpoint.
- pj paused saving family-only ADR (`D-9ead` id reserved unused); asked to check compute assumptions and lock a concrete model in one ADR.

