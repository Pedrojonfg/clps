---
id: D-20261115-pj-60a3
title: "Deep search exposed on dedicated /deep-search endpoint"
date: 2026-11-15T10:27:05Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: contracts
task: T-20261115-pj-2cbd
concepts: [deep search over user ranges]
supersedes: []
relates: [D-20261114-pj-ecc9, D-20261115-pj-54f0, D-20261115-pj-c159, D-20261115-pj-0ee7]
ai: recommended
---
# Deep search exposed on dedicated /deep-search endpoint

## Context

S6 returns a `local_search` block on `GET /site` (`D-ecc9`). Deep search can run for minutes (`D-8a25` default 5 min) or much longer in `total_coverage` mode (`D-54f0`), so folding it into `/site` risks timeouts and mixes chart payload with batch search. Range v1 is a snapped rectangle plus hourly starts (`D-c159`).

## Framing

Give the demo a clear sync API for deep search without blocking the existing planner `/site` path.

## Options considered

1. **A — `deep_search` block on `GET /site`**.
2. **B — Dedicated `/deep-search` endpoint (sync v1)** with mode, rect, template, optional N; response includes best, short board, ETA/runtime, claim label.
3. **C — Library + script only; UI mocks**.
4. **D — Async jobs + poll**.

## Decision

**B.**

## Rationale

Accepted the recommendation: dedicated endpoint (pj: “endpoint propio”).

## Checks raised

None beyond the recommend trade-offs (another route; sync wait for demo).

## Values

| Name | Value | Notes |
|------|-------|-------|
| deep_search_api | dedicated_deep_search_endpoint | Sync for v1 demo |
| deep_search_api_path | /deep-search | |
| deep_search_api_http | POST_json | pj approved; avoids huge query strings |
| deep_search_api_inputs | mode; rect_snap_bounds; time_start_end; template_or_needs; optional_start_n | per `D-54f0` `D-c159` `D-e3cf` |
| deep_search_api_outputs | best; short_leaderboard; eta_or_runtime_s; claim | claim: grid_optimum vs best_seen |
| deep_search_api_leaderboard_n | 20 | pj approved short board |
| deep_search_api_csv_download | ui_button_or_export | pj: download CSV to filter offline; Build may expose export of board/full rows |
| deep_search_api_row_shape | align_with_local_search_rows_where_practical | per `D-ecc9` |

## Expected behavior and validation

Wrong if deep search is only reachable by overloading `/site` or if the response omits mode claim (optimum vs best seen).

## Consequences

- Implement `lunar_eval/search/deep.py` plus POST `/deep-search`; wire minimal demo + CSV download control for `D-0ee7` demo bar.
- Async jobs remain a later upgrade if coverage runs become hours-long in-product.

