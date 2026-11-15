---
id: D-20261115-pj-c159
title: "Deep-search range v1: map rectangle snapped to cap cells; hourly starts"
date: 2026-11-15T10:23:02Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-2cbd
concepts: [deep search over user ranges]
supersedes: []
relates: [D-20261115-pj-54f0, D-20261111-pj-60ab, D-20261114-pj-f369]
ai: options+critique
---
# Deep-search range v1: map rectangle snapped to cap cells; hourly starts

## Context

Deep search needs a user-specified space×time domain (`D-60ab`). On disk the space domain is the precomputed 1 km polar-stereographic cap (~290 k cells, lat ≤ −80°). Time is computed hourly with SPICE; `/site` already uses `start`/`end` with a 1 h tick. `D-54f0` searches inside that domain (`total_coverage` enumerates; `optimized` does not visit every cell).

## Framing

Pick the v1 range shape that matches existing data, with a near-term path to richer geometry.

## Options considered

1. **A — Single site + radius** (S6-like).
2. **B — Map rectangle snapped to cap cells; time = hourly window-start interval; user zone is the search domain**.
3. **C — Free polygon / multi-region now**.
4. **D — Named site lists only**.

## Decision

**B for v1**, with polygons intended in the near future.

## Rationale

pj (2026-11-15): Whatever fits best — if I understood correctly that is rectangle-snap, right? In time it seems clear the tick is 1 h. The whole zone defined by the user should be checked. Yes for v1, but with a view to getting polygons in the near future.

## Checks raised

- No clearly better decision → accepted as fitting the data rather than a deep falsifier.
- “Check the whole zone” means the domain is the full rectangle; optimized mode still need not evaluate every cell (`D-54f0`).

## Values

| Name | Value | Notes |
|------|-------|-------|
| deep_search_range_space_v1 | axis_aligned_rect_snap_to_cap_cells | Cap spacing (`D-f369`) |
| deep_search_range_time_v1 | hourly_window_start_interval | Mission length `h` from template/needs |
| deep_search_range_domain_meaning | full_user_zone_is_domain | Coverage mode enumerates it; optimized searches inside it |
| deep_search_range_polygon | deferred — near future after v1 rect | Explicit follow-up |

## Expected behavior and validation

pj (2026-11-15): Here I think there is no better decision.

## Consequences

- API/UI v1: rectangle (or equivalent lat/lon/stereo bounds) + `[t_start, t_end]` for window starts.
- Snap bounds to existing mask cells; sites outside the cap are out of range.
- Polygon/multi-region is a planned upgrade, not v1 scope.
