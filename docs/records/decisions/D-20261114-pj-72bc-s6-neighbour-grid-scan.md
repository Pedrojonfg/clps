---
id: D-20261114-pj-72bc
title: "Local neighbour scan: 5 km grid, always, rank by score or companion"
date: 2026-11-14T19:31:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-03a6
concepts: [local neighborhood search, infeasible-search signal]
supersedes: []
relates: [D-20261114-pj-5577, D-20261114-pj-9cc5, D-20261111-pj-60ab, D-20261114-pj-f369]
ai: options+critique
---
# Local neighbour scan: 5 km grid, always, rank by score or companion

## Context

S6 requires better neighbouring sites on the grid (`D-60ab`, plan S6 ±N km). Time search is the window slide in `D-9cc5`. Infeasible ranking uses the companion R×bonus (`D-5577`). The 1 km cap supplies regional candidates when present (`D-f369`). Stub `better_neighbours` took an arbitrary `radius_km`.

## Framing

Local space search should be exhaustive inside a small neighbourhood when precompute and temporal reuse make it affordable; shrink the range if compute fails that assumption. Deep search methods stay separate.

## Options considered

1. **A — Time only; drop neighbours from S6**.
2. **B — n points from the grid; rank by score or infeasible companion; scan even when the origin is feasible; local combos assumed cheap with precompute + temporal reuse; deep later may use ML/DL/RL**.
3. **C — Fixed radius with no n cap**.

## Decision

**B**, with neighbourhood **radius 5 km** on the 1 km grid (pj accepted the assisted default). Temporal overlapping reuse only; if the choice is falsified by cost, **reduce the spatiotemporal range**.

## Rationale

n points from the grid; better means better score (or “fake score”); look even if the site is already viable. With precomputed surfaces and the Sun not having to be run so many times because of overlapping, checking all combinations should not be a problem — overlapping meant temporal only. For deep research, more advanced ML/DL/RL techniques will be needed. Radius/n needed help because lunar distances were unclear; chose 5 km after the assisted options. If falsified, reduce the spatiotemporal range.

## Checks raised

- Site×window combinations can still explode → falsification is cost; mitigation is shrink radius and/or time slide.
- Sun geometry is per site; temporal reuse does not equal spatial reuse → recorded; pj limited overlapping claim to time.
- Deep ML/DL/RL is future intent, not a weekend method lock → out of S6 build scope.
- 5 km was AI-assisted → pj still owns the pick; value named below.

## Values

| Name | Value | Notes |
|------|-------|-------|
| local_space_search | grid_neighbours_always | Runs even when origin is feasible |
| local_neighbour_source | precomputed_1km_grid_when_available | Fallback for tests: synthetic candidates in-radius |
| local_neighbour_radius_km | 5 | Assisted default; ~tens of 1 km cells |
| local_neighbour_rank | score_else_infeasible_companion | Feasible score, else `D-5577` companion |
| local_space_time_product | enumerate_neighbours_times_time_slide | Same time slide as `D-9cc5` per neighbour as affordable |
| local_cost_fallback | shrink_spatiotemporal_range | If too expensive: smaller radius and/or shorter slide |
| deep_search_methods_intent | ml_dl_rl_later | Intention only; not S6; S7/P14 still open |

## Expected behavior and validation

Wrong if it is computationally too demanding. Then shrink the spatiotemporal range rather than silently dropping the neighbour scan's meaning.

## Consequences

- S6 space scan uses 5 km around the origin on the 1 km grid when the cap exists.
- Leaderboard includes neighbour rows (with dual zero/companion when needed).
- Cut order item “S6 neighbours → time only” remains available at a failed checkpoint; this record is the preferred full S6 shape.
