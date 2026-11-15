---
id: D-20261115-pj-8a25
title: "Optimized deep-search default wall-clock budget: 5 minutes"
date: 2026-11-15T10:13:34Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-2cbd
concepts: [deep_search_start_default, stopping rule / budget]
supersedes: []
relates: [D-20261115-pj-cb6b, D-20261115-pj-e3cf, D-20261115-pj-54f0]
ai: options+critique
---
# Optimized deep-search default wall-clock budget: 5 minutes

## Context

`D-cb6b` set the start-mesh default to a wall-clock budget on the execution host but left `T_max` unset. Cost order of magnitude on this branch: ~0.5 s per site sky; ~5 min ⇒ on the order of ~600 site evals if that cost holds.

## Framing

Pick an arbitrary but explicit default wait for optimized deep search when the user does not raise effort.

## Options considered

1. **A — ~30–60 s** interactive.
2. **B — 5 minutes**.
3. **C — ~15–30 min** light batch.
4. **D — ≥1 h** near coverage tolerance.

## Decision

**B.**

## Rationale

pj (2026-11-15): 5 min?

## Checks raised

- Arbitrary / not very falsifiable → accepted; real check is whether ~5–10 min on typical final-user hardware looks very bad vs total coverage in a test — post-demo.

## Values

| Name | Value | Notes |
|------|-------|-------|
| deep_search_start_default_T_max | 5_minutes | Wall-clock on execution host; densify/sparsify regular start mesh to fit |
| deep_search_start_default_vs_coverage_check | deferred_post_demo | Compare optimized-at-default vs total_coverage |

## Expected behavior and validation

pj (2026-11-15): It is arbitrary, not very falsifiable; only that the results obtained in 10 minutes with the average end-user hardware were very bad in the test vs total coverage. In any case, post-demo…

## Consequences

- ETA for default optimized mode targets ≤ 5 minutes on the execution host (calibration probe per `D-cb6b`).
- User may still raise N/density above the default.
- Parity test vs `total_coverage` stays post-demo alongside `D-54f0` validation deferral.
