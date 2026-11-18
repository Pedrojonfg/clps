---
id: T-20261118-pj-a670
title: "Respond to the external (OpenAI) audit: P0/P1 findings"
kind: task
owner: pj
branch: main
created: 2026-11-18T14:53:47Z
stage: understand
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

- Before `/decision-flow` was invoked this session, three code changes were already made without records, in `own`/`advise` territory: (a) local-search window duration from elapsed time (`planner_payload.py`), (b) hazard limits kept when data is missing + `hazard_gap_star` for min temperature (`planner_payload.py`, `score.py`), (c) longitude filter in `cap_index.py`. (a) and (c) are bug fixes against the existing intent of D-9cc5; (b) changes behavior governed by D-5cfa/D-f57e and needs the person's review. Uncommitted, tests pass.

## Orientation

- Concepts: sample vs interval semantics (core), fail-closed vs not-evaluable requirements (core), local solar time (prerequisite, hazard: silent proxy), cache identity / immutability (core), evidence-backed claims (core)
- Decisions surfaced: item 4 and item 3 semantics, LST method, claims policy

## Decisions

None yet.
