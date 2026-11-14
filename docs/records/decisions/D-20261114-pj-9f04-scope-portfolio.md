---
id: D-20261114-pj-9f04
title: "Portfolio scope and definition of done"
date: 2026-11-14T11:10:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261114-pj-a1b2
concepts: [scope, success criteria, portfolio]
supersedes: [D-20261111-pj-5cf6]
relates: [D-20261114-pj-7e2a, D-20261111-pj-60ab, D-20261114-pj-b8d3]
ai: options+critique
---
# Portfolio scope and definition of done

## Context

`D-20261111-pj-5cf6` cut must/stretch/decidable/out for a ~48 h hackathon Sunday. That taxonomy is obsolete under `D-7e2a`. Product question `D-60ab` (scored evaluation + constrained search + deep-search intent) remains the north star for what the product *is*.

## Framing

Definition of done is a **defendable portfolio demo**: useful score under planner constraints, honest provenance, working search at least locally, and surface layer-B factors in scope per `D-b8d3`. No Sunday bar.

## Options considered

1. **A — Keep 48 h must/stretch cut**: wrong calendar and wrong ambition.
2. **B — Portfolio MVP = score + one viz + explained thresholds only**: safe but under-sells `D-60ab`.
3. **C — Portfolio done = `D-60ab` loop + layer-B surface factors + body-agnostic seam; full trajectories out**: matches raised ambition without swallowing flight dynamics.

## Decision

**C** (supersedes `D-5cf6`).

## Rationale

Without a contest deadline, the previous “stretch” pieces (local search, deep mode, extra viz) become part of the real product, not optional Sunday luck. Layer-B **surface** physics (temperature, dust, and related site hazards) belongs in the same site×time score. Full Earth–Moon trajectory optimization does not (see `D-b8d3`). Native mobile remains out of v1.

## Values

| Name | Value | Notes |
|------|-------|-------|
| scope_core | needs_adapted_score; explained_thresholds_and_provenance; useful_viz_set; local_neighborhood_search | From `D-60ab` |
| scope_core_deep | deep_search_mode_over_time_space_ranges | Name TBD; required intent |
| scope_layer_b_surface | temperature; dust; related_site_hazards_as_modeled | In product; models deferred to engine ledger |
| scope_out_v1 | full_trajectory_optimization; native_mobile_app; mars_feature_parity | Trajectory *filter* allowed per `D-b8d3` |
| definition_of_done | defendable_portfolio_demo | Backend useful under explicit X,Y,Z (engine ledger) |
| success_xyz | deferred — metrics / validation decisions | Unchanged |

## Consequences

- Engine ledger must define score, X/Y/Z, and how temp/dust enter the score.
- Claims must not imply ops certification or full mission-design coverage.
- Multi-body extension is architectural only in v1 (`D-b8d3`).
