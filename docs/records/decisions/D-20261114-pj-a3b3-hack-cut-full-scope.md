---
id: D-20261114-pj-a3b3
title: "Space Apps submission targets the full portfolio scope; fallback cut only at the Sunday freeze"
date: 2026-11-14T13:18:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261114-pj-12b7
concepts: [appetite, scope]
supersedes: []
relates: [D-20261114-pj-d7d9, D-20261114-pj-9f04, D-20261111-pj-60ab, D-20261114-pj-f369]
ai: options+critique
---
# Space Apps submission targets the full portfolio scope; fallback cut only at the Sunday freeze

## Context

`D-20261114-pj-d7d9` left `hack_submission_cut` deferred to the `/shape-up` replan. The first replan proposed a Sunday cut (sky, masks, timeline, score, local search, two views, submission pack) and moved deep search, layer B, server and validation to Mon 16 – Thu 20 Nov.

## Options considered

1. **A — Sunday cut as proposed, rest in the following days**: lower Sunday load; the submission lacks deep search and layer B.
2. **B — Full portfolio scope (`D-9f04`) targeted for Sunday, with the proposed cut order applied only if checkpoints fail**: everything is attempted; the cut becomes a fallback.

## Decision

**B.** The whole `D-20261114-pj-9f04` scope is targeted for the Sunday submission. The plan's cut order applies only at failed checkpoints and at the Sunday 18:00 freeze; what is cut then is finished Mon 16 – Thu 20 Nov.

## Rationale

"No, no — let's try to fit everything in for Sunday; trust me."

## Checks raised

- Planned lane work (~60 h) exceeds pj's review capacity before Sunday (~17 h of attention) → pj keeps the full target; the checkpoints and cut order stay as the circuit breaker.
- The 100 m precompute takes ~26–52 days on a CX43 and cannot finish by Sunday → it is a running job, not a Sunday deliverable; the submission uses the 1 km cap and the refined demo site.

## Values

| Name | Value | Notes |
|------|-------|-------|
| hack_submission_cut | full_portfolio_scope | Submission cut left open by `D-20261114-pj-d7d9` |
| hack_fallback_cut | plan cut order at failed checkpoints and the Sun 18:00 freeze | `docs/plans/2026-11-14-implementation-plan.md` §12 |

## Expected behavior and validation

As in `D-20261114-pj-d7d9`: "That I don't have time to finish it by tomorrow." Then the fallback cut is submitted and the rest is finished by 20 Nov.

## Consequences

- Layer-B model decisions and the first-person viewer decision move to Saturday.
- Mon 16 – Thu 20 Nov becomes the window for whatever the freeze cuts, plus the long precompute.
