---
id: D-20261116-pj-4902
title: "Mock mode ships a local-search leaderboard so the top-N UI can be checked"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: testing
task: T-20261116-pj-9eee
concepts: [mock data labelled as mock, local-search leaderboard]
supersedes: []
relates: [D-20261114-pj-9cc5, D-20261114-pj-8588, D-20261115-pj-a988]
ai: recommended
---
# Mock mode ships a local-search leaderboard so the top-N UI can be checked
## Context

With "Local search" ticked the planner showed no leaderboard. Cause: `GET /site?mock=1` returns a fixed payload with no `local_search` block, so in mock mode (the default, and the only mode of the static demo) the table never renders. With real data the block exists. pj (2026-11-16): if there is no data, mock it and make sure the whole UI (the N best cases) looks right.

## Framing

Every UI surface must be checkable without kernels or DEMs, and mocked numbers must never read as results.

## Options considered

1. **Leave it: leaderboard only with real data**: consequence: the UI cannot be reviewed in mock mode or on the public demo.
2. **Mock payload includes a synthetic leaderboard when `local_search=1`, same shape and same ordering rule as the real search**: consequence: one more mocked block to label.
3. **Fabricate rows in the front end**: consequence: the UI would be tested against a shape the API does not produce.

## Decision

**2.**

## Rationale

pj asked for it. Producing the rows in the API's mock path, sorted by the real `D-9cc5` key, keeps the contract honest: the UI is exercised with the shape the real search returns.

## Checks raised

- Mock rows could be mistaken for results → the table carries a "mock data" tag whenever `data_source` is not `real`, and the static demo keeps its banner.
- The leaderboard holds 2h+1 rows per site, which is long → the UI shows the best N first with a control to show all.

## Values

| Name | Value | Notes |
|------|-------|-------|
| mock_local_search | synthetic_when_requested | Only when `local_search=1`; deterministic |
| mock_local_search_order | same_sort_key_as_real | `D-9cc5` / `D-72bc` / `D-5577` |
| planner_leaderboard_default_rows | 10 | "Show all" expands |

## Expected behavior and validation

Wrong if mock mode with local search ticked shows no leaderboard, or shows one without a mock label. A contract test covers the mock block.

## Consequences

- `scripts/export_demo_data.py` exports the mock site payload with the local-search block so the static demo shows it too.
