---
id: D-20261114-pj-beb5
title: "Golden aggregate fixture for Site01 week 2027-01-01–07"
date: 2026-11-14T18:38:12Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-8138
concepts: [success X/Y/Z, visibility series]
supersedes: [D-20261114-pj-1a46]
relates: [D-20261114-pj-1a46, D-20261114-pj-41fa, D-20261114-pj-aa58, D-20261114-pj-7520, D-20261114-pj-7af3]
ai: options+critique
---
# Golden aggregate fixture for Site01 week 2027-01-01–07

## Context

`D-1a46` excluded a full-week golden series. pj revisited validation after the probabilistic layer-1 and `min_continuous_lit_h` decisions. Full hourly frozen output is costly; aggregate-only catches most aggregation and score wiring bugs.

## Framing

Regression guard for S3/S4 on the production test window (`D-aa58`) without committing 168× fractional arrays.

## Options considered

1. **A — Full weekly hourly golden**: highest coverage, highest maintenance.
2. **B — No golden (prior)**: light CI, gap on long-window aggregates.
3. **C — Aggregate golden only**: frozen longest_* , hour counts, layer-0 feasibility, R, B, score for one fixed scenario.

## Decision

**C.**

## Rationale

pj: “golden agregados me parece bien.”

## Checks raised

- Changing σ or β updates expected score → regenerate fixture when `D-6ce5` tune completes or formula version bumps; fixture records `score_formula_version` or decision IDs.
- Site01 only → does not guard arbitrary coordinates; accepted for v1.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s3_s4_golden_week_series | aggregate_only | Supersedes `out_v1` in `D-1a46` |
| golden_fixture_path | tests/fixtures/site01_20270101_07_aggregates.json | Generated once real stack present; gitcommitted |
| golden_site | Site01 | `D-da5f` coordinates |
| golden_time_window | 2027-01-01T00:00:00Z through 2027-01-07T23:00:00Z hourly | `D-aa58` production test window |
| golden_needs | fixed dict in test module | Document template id or explicit needs + thresholds + bridge_h |
| golden_fields | longest_night_h; longest_no_earth_h; longest_lit_h; hours_sun_above_threshold; hours_earth_above_threshold; any_both; feasible; layer1_R; layer1_B; score | Optional tolerances on floats in test code, not in JSON |
| golden_hourly_fractions | out | Not stored |
| s3_s4_validation | horizons_xyz_plus_unit_short_e2e_plus_aggregate_golden | Restates validation bundle |
| s3_s4_golden_reopen | full_hourly_golden_if_aggregate_insufficient | Escalate only on repeated misses |
| golden_regenerate_when | score_formula_version or cited D- IDs change | Manual regen when layer-1 or visibility defs change |

## Expected behavior and validation

Wrong if a refactor breaks week-long longest_lit or bonus counts but unit tests still pass; this pytest should fail. Wrong if the fixture rots because β/cap change without regen — mitigation: bump version key in test when recording tune.

## Consequences

- Add `tests/test_site01_week_aggregates.py` (or extend `test_dem_site`) when kernels, DEM, and new S3 fields exist.
- Full weekly fraction golden remains out unless a regression forces it.