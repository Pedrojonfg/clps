---
id: D-20261115-pj-8c03
title: "Product remote serves horizon masks only; evaluator runs on the client"
date: 2026-11-15T11:12:37Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261115-pj-2b7a
concepts: [client compute vs server compute, public HTTPS demo honesty]
supersedes: [D-20261114-pj-5994]
relates: [T-20261115-pj-5200, D-20261114-pj-f369, D-20261114-pj-3c91, D-20261114-pj-a3b3]
ai: none
---
# Product remote serves horizon masks only; evaluator runs on the client

## Context

S10/S11 need a product runtime shape. `D-20261114-pj-5994` chose pj's PC for the demo precompute and a Hetzner CX43 (CAX31 if out of stock) for the 100 m cap **and for serving the app**. pj separates *production process* (where masks are precomputed) from *product runtime* (what a user of the tool talks to). CX43 was out of stock on Hetzner at decision time; the 1 km cap is already on disk.

## Framing

Optimize for defending a tool whose heavy site×time work uses the end user's machine; keep any remote role minimal and honest for a portfolio demo.

## Options considered

1. **A — Remote masks only; evaluator on the client**: assumes the user can run the compute; consequence: S11 is not “app on a VPS”; public URL meaning changes; supersedes `D-5994` serving-the-app role.
2. **B — App + API + compute on pj's server**: assumes use is mostly over the network against pj's host; consequence: matches the old S11 plan; cost and performance capped by what pj pays.
3. **C — Fully local, no remote masks**: assumes the user brings or generates masks; consequence: no product host; the 1 km cap is distributed offline.

## Decision

**A — Remote serves horizon masks only; the evaluator runs on the client.**

## Rationale

For the product (not the production process), the server is only to obtain horizon masks. In production, a server (e.g. Hetzner) may be used to precompute, or the same work can run on pj's PC at night; that is process, not product runtime. For what the product is, the server only stores and serves masks (whether that is a dedicated VPS or another store is a later delivery choice).

## Checks raised

- Partial conflict with `D-5994` “serving” the app → this record supersedes `D-5994` and restates precompute hosting as process-only values.
- “Client” form (desktop / local Python / browser) not fixed here → deferred to mask-delivery / packaging decisions.
- `D-3c91` audience is portfolio-technical, not live enterprise traffic → accepted; hardware falsification is about product fitness, not today's users.

## Values

| Name | Value | Notes |
|------|-------|-------|
| product_compute_locus | client | Score, search, live sky on the user's machine |
| product_remote_role | horizon_masks_store_and_serve | Nothing else in product runtime |
| precompute_host_demo | pj's PC | Process; from former `D-5994` |
| precompute_host_full | Hetzner CX43; CAX31 if out of stock | Process when a paid month is used; stock may be zero |
| server_months_budget | 1, a second if the 100 m run is unfinished | Process budget; unchanged |
| server_benchmark | first hour on the server measures masks/s before committing to the full run | Process; when a host is used |
| public_https_role | static_demo_and_docs | Filled with `D-4494` / `D-2533`; must not imply evaluator on our VPS |
| client_packaging | browser_static_demo | Filled with `D-2533` for this tranche; richer packaging later |

## Expected behavior and validation

Wrong if end users lacked hardware good enough to run it (unlikely vs any VPS pj would pay for), or if client-side compute were so expensive or infeasible that there would be no product at all — in which case the failure is the product, not this split.

## Consequences

- Build and demo must not require pj's VPS to run the evaluator.
- S11 “public URL” cannot mean “full app on Hetzner” without a superseding decision.
- Mask delivery mechanism (VPS vs object store vs “DB on my web”) is a later advise/own item.
- Cesium/ion tokens and host credentials stay out of git (unchanged).
