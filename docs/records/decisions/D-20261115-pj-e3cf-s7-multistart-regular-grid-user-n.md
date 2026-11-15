---
id: D-20261115-pj-e3cf
title: "Optimized deep search starts: regular space-filling grid; user-set N; default TBD"
date: 2026-11-15T09:57:53Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-2cbd
concepts: [multi-start placement, stopping rule / budget, deep search over user ranges]
supersedes: []
relates: [D-20261115-pj-54f0, D-20261114-pj-bf69]
ai: options+critique
---
# Optimized deep search starts: regular space-filling grid; user-set N; default TBD

## Context

`D-54f0` set default deep search to multi-start hill climb on the user range grid, with start placement deferred. Literature and session notes favour space-filling designs over clustered random starts; LHS vs regular grid usually matter less than count and spacing when both fill space. There is no product “landable zone” partition; PSR is only an early impossible-site check (`D-bf69`).

## Framing

Make optimized-mode starts reproducible and explainable on the map, while letting operators raise or lower effort.

## Options considered

1. **A — Fixed regular mesh** (e.g. every 10 km / 24 h), N not user-set.
2. **B — LHS / random space-filling with fixed N**.
3. **C — Regular space-filling mesh; user chooses N or density; default depends on range size** (default formula next).
4. **D — Starts only on predefined landable zones**.

## Decision

**C.**

## Rationale

pj (2026-11-15): Space-filling, regular grid; we do not need a test vs LHS. As for the number of starts, I do not know — perhaps the user can decide it and we put a reasonable default according to the time and space to cover.

## Checks raised

- Criterion is hard to falsify; what matters is whether the reasonable default is good → accepted; default formula is the next decision.
- No LHS A/B test → accepted; claim is regular grid, not “best sampler”.

## Values

| Name | Value | Notes |
|------|-------|-------|
| deep_search_start_design | regular_space_filling_grid | Inside the user range |
| deep_search_start_n_control | user_settable | Density or count in the UI/API |
| deep_search_start_default | wall_clock_then_T_max | Basis `D-cb6b`; T_max `D-8a25` |
| deep_search_start_vs_lhs_test | not_required_for_v1 | Explicitly skipped |

## Expected behavior and validation

pj (2026-11-15): I think this criterion is hard to falsify; the real issue will be whether the reasonable default is good or not.

## Consequences

- Build must expose a user control for start count/density and apply a recorded default when unset.
- Do not invent landable-zone partitions for start placement in v1.
- Next decision locks the default rule (and may set caps/floors).
