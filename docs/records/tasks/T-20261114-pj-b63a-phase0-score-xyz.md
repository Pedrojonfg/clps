---
id: T-20261114-pj-b63a
title: "Lock the Phase 0 score formula and success X/Y/Z"
kind: decide
owner: pj
branch: scope/ops-skeleton
created: 2026-11-14T13:27:58Z
stage: done
relates: [T-20261114-pj-12b7, T-20261114-pj-a1b2]
---
# Lock the Phase 0 score formula and success X/Y/Z

## Goal

Done means: `score_formula` and `success_xyz` are recorded (or explicitly deferred with a working default pj defends). That unblocks S4. Origin: approved implementation plan Phase 0; pj asked what of Phase 0 still needs `/decision-flow` versus committing the Ops skeleton.

## Triage

- Own/advise parts: score formula and success X/Y/Z (own, method & validation / scope); how temperature and dust enter the score (own, deferred to the 17:00 P13 session unless pj wants it now); recording the plan-gate contracts P1–P3, P5–P7 (advise, contracts / architecture / dependencies).
- Plumbing: Ops skeleton already built on this branch (`pyproject.toml`, `lunar_eval/`, `api/`, `web/`, tests, CI, `data/` gitignored). Commit when asked.

## Pending checkpoint

None.

## Orientation

- Concepts: visibility series (prerequisite); needs-adapted score (core); minima and feasibility (core); success X/Y/Z (core); provenance (hazard); layer-B in the score (hazard, P13 later).
- Approach: engine (pandas over the visibility series) yields longest-night / longest-without-Earth / etc.; score is a separate question. Fail-closed zero when a minimum is missed. Do not compare to a global best case (harsh missions would look bad). First layer: slack toward going infeasible (pj framed it as probabilistic). Second layer: weights on remaining factors (temperature, dust, extra hours); a simple sum is enough. Goal is assured basics, not idle surplus.
- Decisions surfaced: score formula (two-layer); success X/Y/Z (Horizons, 5 h / 28 pts, fail-closed score); contracts P1–P3, P5–P7.
- Agenda accepted by pj 2026-11-14 without changes.

## Decisions

- D-20261114-pj-de42 — Two-layer score: fail-closed zero, then assurance, then weighted factors
- D-20261114-pj-41fa — Success X/Y/Z: Horizons, 5 h mask hours, fail-closed score; PGDA 69 later
- D-20261114-pj-9e53 — Phase 0 engine contracts: sky, mask, visibility, score signature, seams, stack, fixtures

## Auto decisions

| Choice | Reason |
|--------|--------|
| Package layout `lunar_eval/{ephemeris,horizon,hazards,search}`, `api/`, `web/`, `tests/` | engineering hygiene; matches plan §10 ownership |
| `data/dem|kernels|masks|precompute` gitignored; Horizons fixtures under `tests/fixtures/horizons/` | P7 as approved at the plan gate; DEMs never in git |
| CI: pytest on Python 3.12; `spiceypy` optional extra `[sky]` | hygiene; library lock is still deferred (`D-4ffe`) |
| Hardlink existing `/tmp` DEMs into `data/dem/`; fetch remaining PGDA files in background | execution of `D-f369` / `D-5994`, not a new choice |

## Fog

- Layer-B temperature and dust models (plan P13, Sat 17:00).
- Ephemeris library / frame / kernel version (T-12b7 agenda item 5; after Spike K, Sat 16:30).
- First-person viewer and basemap (T-12b7 agenda items 6–7; Sat 17:45).
- Demo site refinement (`D-f369`, ~20:00).

## Out of scope

- Remaining T-12b7 items that the plan parked after Phase 0's 15:00 session (PGDA 69 = P12 Sunday).
- Deep-search ranges and stopping rules (P14, Sat 23:00).
- Ordering the CX43 (already decided in `D-5994`; execution, not a new decision).
- Editing `project.md` (must be default branch / its own PR per `D-d7d9`).

## Build

Ops skeleton on `scope/ops-skeleton`; pytest 3 passed locally. Not committed.

## Audit

decide task: `lunar_eval/providers.py` cites `D-20261114-pj-9e53`. Score formula and X/Y/Z tests are not implemented in this task (S1/S2/S4).

## Detours

- T-20261114-pj-12b7 lives on merged branch `docs/product-ledger-portfolio`; remaining agenda items 4–7 are not continued by editing that task. They sit in Fog here and wait for their plan slots.
