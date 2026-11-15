---
id: D-20261115-pj-1ebf
title: "Hill climb neighbours: ±1 precomputed cell and ±1 h; stop at local peak"
date: 2026-11-15T10:17:59Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-2cbd
concepts: [stopping rule / budget, multi-start placement, silent incomplete search]
supersedes: []
relates: [D-20261115-pj-54f0, D-20261115-pj-e3cf, D-20261115-pj-8a25, D-20261114-pj-f369]
ai: options+critique
---
# Hill climb neighbours: ±1 precomputed cell and ±1 h; stop at local peak

## Context

`D-54f0` / `D-e3cf` require a discrete neighbourhood for multi-start hill climb on the user range. The product grid spacing is the precomputed cap (`D-f369`: 1 km for the demo cap; 100 m later). Time ticks are hourly elsewhere in search.

## Framing

Keep the climb’s “step” aligned with data that already exists, and put step-size quality into the post-demo megatest vs total coverage.

## Options considered

1. **A — Large jumps** (±k cells / large Δt).
2. **B — ±1 precomputed spatial cell and ±1 h; stop when no neighbour improves; include step sizes in megatest vs coverage**.
3. **C — Adaptive coarse-then-fine neighbourhood**.
4. **D — Time-only or space-only neighbours**.

## Decision

**B.**

## Rationale

pj (2026-11-15): I suppose all of that is also very testable vs coverage, but I think by default 1 h and whatever precision is precomputed.

## Checks raised

- Same as usual: not entering on time / not doing it well enough → accepted; therefore step sizes will be added to the megatest vs coverage.

## Values

| Name | Value | Notes |
|------|-------|-------|
| deep_search_hillclimb_neighbour_space | plus_minus_1_precomputed_cell | Follows cap spacing (1 km now; 100 m if that grid is what is precomputed) |
| deep_search_hillclimb_neighbour_time | plus_minus_1_hour | |
| deep_search_hillclimb_stop | no_improving_neighbour | Local peak on that neighbourhood |
| deep_search_hillclimb_step_megatest | include_step_sizes_vs_coverage | Post-demo; with `D-54f0` / `D-8a25` checks |

## Expected behavior and validation

pj (2026-11-15): The same as always — not entering on time, not doing it well enough… that is why we will add step sizes to the megatest vs coverage.

## Consequences

- Climb evaluates the origin’s grid neighbours at ±1 cell and window starts at ±1 h (within the user range).
- When precompute spacing changes, the spatial neighbour size changes with it.
- Megatest must vary step sizes, not only default N / T_max.
