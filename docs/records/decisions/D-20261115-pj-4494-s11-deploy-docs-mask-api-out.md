---
id: D-20261115-pj-4494
title: "S11 this tranche: deploy plus docs; mask API out for now"
date: 2026-11-15T11:15:14Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261115-pj-5200
concepts: [demo 1 km vs full 100 m spacing, calling the job done after start, public HTTPS demo honesty]
supersedes: []
relates: [D-20261115-pj-8c03, D-20261114-pj-a3b3, D-20261114-pj-f369, T-20261115-pj-2b7a]
ai: none
---
# S11 this tranche: deploy plus docs; mask API out for now

## Context

Plan S11 asked for a CX43 one-hour benchmark, HTTPS app with the 1 km dataset, and a started 100 m run. `D-20261115-pj-8c03` made product remote masks-only and client-side compute. Today's goal is a portfolio demo (NASA send optional). The 1 km cap already exists on disk; a live mask API does not.

## Framing

Define a defendable “S11 done for this tranche” that matches the demo, not the multi-week precompute.

## Options considered

1. **A — Deploy + docs; mask API out (mocks ok)**: assumes today's demo does not need to serve the real 1 km cap over the network; consequence: S11 here is hosting the static demo and writing clear docs; API and 100 m stay out (API only if spare time, not as done).
2. **B — Deploy + docs + 1 km mask API**: assumes the demo must read real masks over the network; consequence: design and ship store/API now.
3. **C — Old plan S11 (HTTPS app + benchmark + 100 m started)**: assumes the plan done-line still holds after `D-8c03`; consequence: conflicts with masks-only remote and with time/stock.

## Decision

**A — Deploy and good documentation; mask API out of this tranche's done (mocked data acceptable; API only if spare time tonight, not required).**

## Rationale

For what we want today — make the demo and possibly send the project to NASA — it is enough to have a deploy and solid docs that explain how everything works. An API is not needed for now: mocked data can be used and an API can be created later. If time is left tonight it may be built too, but for now it stays out.

## Checks raised

- “Deploy” under `D-8c03` means static demo + docs, not evaluator on a VPS → recorded in Values.
- Docs must not imply a live mask service while the cap sits only on disk → honesty check in Expected behavior.
- Spare-time API is not part of done → `s11_mask_api: out_for_this_tranche`.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s11_this_tranche_done | static_deploy_plus_docs | Host the demo pages; document architecture and how masks/precompute work |
| s11_mask_api | out_for_this_tranche | Mocks ok in the demo; optional later, not required for done |
| s11_100m_start | out_for_this_tranche | Not a today deliverable; still allowed as later process under `D-8c03` precompute values |
| s11_server_benchmark_hour | out_for_this_tranche | No CX43 in stock / not needed for this done |
| public_https_role | static_demo_and_docs | Fills deferred role from `D-8c03`; not “evaluator hosted on our VPS” |
| deploy_target | github_pages | Filled by `D-2533`; revisit later per that record |

## Expected behavior and validation

Wrong if the mask API were crucial for the demo — pj states it is not.

## Consequences

- Agenda items 9–10 and 12 are out or deferred for this tranche (no mask API; no public mask set contract; no 100 m start as done).
- Item 11 shrinks to “how we host the static demo + docs”.
- Cap 1 km on disk remains a documented artifact, not a networked product surface yet.
