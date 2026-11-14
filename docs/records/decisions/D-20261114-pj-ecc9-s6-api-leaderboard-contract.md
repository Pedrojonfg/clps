---
id: D-20261114-pj-ecc9
title: "Local search results ride on GET /site as local_search block"
date: 2026-11-14T19:40:49Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: contracts
task: T-20261114-pj-03a6
concepts: [local neighborhood search]
supersedes: []
relates: [D-20261114-pj-9e53, D-20261114-pj-aa58, D-20261114-pj-8588, D-20261114-pj-5577, D-20261114-pj-9cc5, D-20261114-pj-72bc, D-20261114-pj-f57e]
ai: recommended
---
# Local search results ride on GET /site as local_search block

## Context

S6 needs a transport for the leaderboard into the planner UI. `GET /site` already carries live sky, series, and score for the interactive demo (`D-aa58`, `D-8588`). Phase-0 contracts did not define a search payload (`D-9e53`).

## Framing

Prefer one planner request over a second parallel API for the weekend demo.

## Options considered

1. **A — New `/search` endpoint**.
2. **B — `local_search` block on `/site`**.
3. **C — Engine only; UI mocks the board**.

## Decision

**B.**

## Rationale

Accepted the recommendation: keep a single planner request; return a `local_search` block with the leaderboard on `/site`.

## Checks raised

- Larger responses → allow a query flag (e.g. `local_search=1`) so CI/mock paths stay light; default may follow Build auto choice if unset.
- Must expose dual zero / impossible companion and hazard `*` flags (`D-5577`, `D-f57e`).

## Values

| Name | Value | Notes |
|------|-------|-------|
| local_search_api | get_site_local_search_block | Nested under existing planner `/site` |
| local_search_payload | leaderboard_rows | Each row: site, window, feasible, score, companion_score, hazard_gap_star, delta_vs_origin |
| local_search_pick | top_row_plus_full_board | Explicit best pick; board still listed |
| local_search_query_flag | local_search | `1`/`true` enables; omit or `0` skips compute for light paths |

## Expected behavior and validation

Wrong if the UI cannot show the dual score and starred hazard gaps from the payload, or if enabling search doubles latency past demo tolerance without the cost-fallback in `D-72bc`.

## Consequences

- `api/app.py` / `planner_payload` grow a `local_search` object when flagged.
- `web/index.html` renders the board from that block.
- No separate `/search` route in v1.
