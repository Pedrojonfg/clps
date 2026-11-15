---
id: T-20261115-pj-98c4
title: "Specify and decide S12 validation, S14 claims/README, S15 portfolio pack"
kind: task
owner: pj
branch: scope/s5-hazards-wire
created: 2026-11-15T11:46:30Z
stage: done
relates: [D-20261114-pj-41fa, D-20261114-pj-f369, D-20261114-pj-050d, D-20261114-pj-7e2a, D-20261115-pj-a988, D-20261115-pj-671e]
---
# Specify and decide S12 validation, S14 claims/README, S15 portfolio pack

## Goal

Lock every product/method/claims choice needed so S12 (validation + PGDA 69 role / short-night re-check), S14 (claims, provenance, README) and S15 (portfolio deliverable pack; not Space Apps Sunday submission) can be built without silent defaults. Done means: agenda worked, values recorded or deferred, `flow.py check` clean; build may follow in later sessions if scope is large.

Origin: pj asked `/decision-flow` for S12, S14, S15 together and required a full decision set (grouping must not shrink the agenda).

## Triage

- Own/advise parts:
  - S12: what counts as validation evidence (short-night re-check; PGDA 69 comparison; whether PGDA 69 enters X/Y/Z or claims) — own (method & validation, claims & interpretation, data & sources).
  - S14: what every number may claim; provenance footer contents; README story vs technical honesty — own (claims & interpretation, scope & success criteria); presentation layout advise.
  - S15: what the portfolio pack is (slides / video / docs), SI and branding honesty, what “submitted” means under solo portfolio — own (scope & success criteria, claims); format/presentation advise.
- Plumbing: file paths under `docs/validation.md`, `README.md`, `docs/submission/` or portfolio equivalent; test harness wiring once values exist (auto/advise).

## Pending checkpoint

None.

## Orientation

- Concepts: success X/Y/Z (prerequisite); topographic horizon mask / short-night regime (core, S12); PGDA 69 long-term averages (core, S12/P12); provenance (hazard, S14); claims honesty / demo vs computed (hazard, S14); portfolio pack vs contest submission (core, S15); hazard proxy (warm-up debt, S14 dust row); Metzger slope factor (core, deferred from `D-050d`).
- Approach (pj): skip further orientation; open Decide now; include slope factor; keep full agenda despite grouping scopes.
- Pace (pj 2026-11-15): time-box — item 1 alone, then batches of 3–4; questions only (no options / no AI pick); audio answers OK; falsify/lookup/change only when needed.
- Warm-up: hazard proxy graded `shaky`; taught from `D-050d`.
- Agenda OK 2026-11-15.

## Decisions

- D-20261115-pj-06cb — Metzger slope factor β = cos(θ) on grain term only
- D-20261115-pj-39f3 — S12 short-night re-check S1 (report; reopen Y if >5 h)
- D-20261115-pj-9ab3 — S12 PGDA 69 protocol P1 (~18.6 y; report only)
- D-20261115-pj-fe17 — PGDA 69 role: report + README; not product logic
- D-20261115-pj-1a9e — S12 done: scripts/tests exist; overnight run
- D-20261115-pj-de70 — S14 claims evidence-gated (test/ADR)
- D-20261115-pj-358b — S14 forbidden/provisional from ADRs
- D-20261115-pj-9ed6 — S14 provenance: full payload; one-line + expandable UI
- D-20261115-pj-cacb — README portfolio what/how/try-today/future
- D-20261115-pj-1264 — S15 Remotion after UI; pitch deck pj-owned
- D-20261115-pj-3c4a — S15 docs clear install; pitch length pj
- D-20261115-pj-6663 — S15 no NASA affiliation; hackathon heritage only
- D-20261115-pj-8fd2 — Portfolio done when UI finished (+ pack follow-through)

## Auto decisions

| Choice | Reason |
|--------|--------|
| Paths `docs/validation.md`, pack folder names, test file names once protocols exist | Hygiene; no claim change |
| Wire pytest once thresholds/protocols recorded | Plumbing |

## Fog

- Continuous polar grain/cohesion raster (unavailable; Apollo-average stands unless reopened)
- Full Metzger erosion-with-engine (out v1 per `D-050d`)
- Fine README typography

## Out of scope

- Reopen rock/roughness in score unless asked
- Space Apps eligibility / 23:00 submit (`D-7e2a`)
- Implementation during Decide
- S13 far-field experiment

## Decide agenda (pj OK 2026-11-15; batched pace)

1. Metzger slope factor (alone first)
2–5 S12: short-night re-check; PGDA 69 protocol; PGDA 69 product role; S12 done bar
6–9 S14: allowed claims; forbidden/provisional; provenance inventory; README honesty structure
10–13 S15: pack medium; content/length; SI+branding; published/done
Auto / fog / out as above.

## Build

2026-11-15 `/implementa`: `soil.py` Metzger β=cosθ (`D-06cb`); S12 harness scripts + `docs/validation.md` + smoke tests (`D-1a9e`); README portfolio rewrite; compact provenance UI on `web/index.html` (`D-9ed6`). Remotion still gated on UI (`D-1264`). Overnight short-night/PGDA69 numbers not filled.

## Audit

pending (parent re-check after PR)

## Detours

- Task opened on `scope/s5-hazards-wire` because that was the current branch; S12/S14/S15 are not S5. Prefer a dedicated branch before build/merge if this branch stays hazards-focused.
- `project.md` / `D-7e2a`: delivery is solo portfolio; plan text for S15 still says Space Apps submission by 23:00 — that frame is superseded for claims; S15 must be re-specified as portfolio pack.
