---
id: T-20261118-pj-a670
title: "Respond to the external (OpenAI) audit: P0/P1 findings"
kind: task
owner: pj
branch: fix/audit-p0-code-bugs
created: 2026-11-18T14:53:47Z
stage: audit
relates: [D-20261114-pj-9cc5, D-20261114-pj-f57e, D-20261114-pj-5cfa, D-20261114-pj-41a2]
---
# Respond to the external audit: P0/P1 findings

## Goal

An outside model audited the repo (171 tests pass, 22 skipped) and listed 42 findings (P0 correctness, P1 validation/distribution/UX/release). Done = each finding is triaged, the ones in scope for v1 are decided and fixed with regression tests, and the rest are explicitly deferred or dropped from README claims.

## Triage

- Own/advise parts: which findings are real and in scope; semantics of window endpoints (item 3); what "not evaluable" means for a requirement (item 4); policy for substituted/missing data (item 5); LST method (item 1); what README may claim (items 10, 11, 41); cache/versioning policy (items 19-21).
- Plumbing: longitude filter bug in `sites_in_latlon_rect` (item 6, objective bug).

## Pending checkpoint

None.

## Detours

- Before `/decision-flow` was invoked this session, three code changes were already made without records, in `own`/`advise` territory: (a) local-search window duration from elapsed time (`planner_payload.py`), (b) hazard limits kept when data is missing + `hazard_gap_star` for min temperature (`planner_payload.py`, `score.py`), (c) longitude filter in `cap_index.py`. (a) and (c) are bug fixes against the existing intent of D-9cc5; (b) restores behavior already decided in D-f57e/D-5cfa (limit set + data missing => starred); the only addition is that a missing min temperature also stars. Item 4 is therefore already-decided, not a new decision. All three shipped in PR #34. Uncommitted, tests pass.

## Orientation

- Concepts: sample vs interval semantics (core), fail-closed vs not-evaluable requirements (core), local solar time (prerequisite, hazard: silent proxy), cache identity / immutability (core), evidence-backed claims (core)
- Decisions surfaced: item 4 and item 3 semantics, LST method, claims policy

## Decisions

- D-20261118-pj-9413 (window endpoints), D-20261118-pj-b3dc (missing data), D-20261118-pj-633d (local solar time), D-20261118-pj-75f1 (searches use user requirements), D-20261118-pj-70ec (template edits), D-20261118-pj-1bc9 (score is a ranking index), D-20261118-pj-62d3 (data store versioning), D-20261118-pj-23ab (first run), D-20261118-pj-d99f (offline), D-20261118-pj-6fea (3D relief cuts), D-20261118-pj-8625 (saved analysis), D-20261118-pj-cd33 (usage limits), D-20261118-pj-fc4d (platforms)

## Not yet built

Decisions also include D-20261118-pj-1454 (search stop and resume) and D-20261118-pj-d90c (terrain gaps). All decisions above are decided but not implemented, except the three code fixes in PR #34. Build comes next; do not build before the deferred values that block each step are settled (see `flow.py values`).

## Agenda (own/advise queue, one at a time)

1. Window endpoints: samples vs intervals (item 3, 14, 15) - concepts: sample vs interval
2. Substituted data: slope 0, missing PSR, season fallback (item 5, 9) - concepts: not evaluable vs favorable default
3. Local solar time method (item 1) - concepts: local solar time, climatology
4. Regional search requirements and template editing (items 7, 8)
5. Claims and evidence in README (items 10, 11, 12, 41)
6. Score is heuristic, not probability; provenance in results (items 16, 17)
7. Data versioning and cache identity (items 19, 20)
8. First run, offline, 3D relief (items 23, 24, 25)
9. v1 usage limits, saved analysis, platforms, release (items 29, 30, 33, 35, 42)

## Already decided

- Item 4 (missing data must not look viable): D-20261114-pj-f57e (now superseded by D-20261118-pj-b3dc), D-20261114-pj-5cfa
- Items 10, 11, 41 (claims without evidence): D-20261115-pj-de70. pj: the 28-point test was probably an uncommitted one-off; remove unbacked claims now, rewrite the README at release. Applied: README 28-point row removed, validation rows reworded; full README rewrite deferred to release.

## Auto

None.

## Fog / out of scope

- Item 39 dependency lock (tool choice, minor); items 31, 36, 37 (testing/usability passes)

## Build (2026-11-19, unattended run)

All decided items implemented on branch feat/audit-decisions-impl (uncommitted): suite 533 passed / 1 skipped, desktop build and cargo check green. Not done / not verifiable: 1 km masks recompute and republish (D-d90c), real publishing to R2 (D-62d3, D-6fea), app never run (CSP, Tauri commands, UI flows), Diviner noon convention only checked statistically, licence of elevation data unclear (docs/relief-licence.md). Findings: dev-machine own-DEM masks skip the 0-2 km near field (up to 17 deg lower than cap masks); data/dem/ldem_87s_5mpp.tif is truncated; PCP climatology bins incomplete locally (95/96 summer, 87/96 winter).
