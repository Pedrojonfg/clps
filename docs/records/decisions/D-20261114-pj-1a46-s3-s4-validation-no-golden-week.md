---
id: D-20261114-pj-1a46
title: "S3/S4 validation without a committed golden week series"
date: 2026-11-14T18:29:25Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-8138
concepts: [success X/Y/Z, provenance]
supersedes: []
relates: [D-20261114-pj-41fa, D-20261114-pj-9e53, D-20261114-pj-f369, D-20261114-pj-7520]
ai: options+critique
---
# S3/S4 validation without a committed golden week series

## Context

pj asked whether to add a CI golden file for a full Site01 week (e.g. 2027-01). `D-41fa` already defines X (kernels vs Horizons), Y (28-point mask hour tolerances), and Z (hand score fail-closed). Unit tests cover visibility primitives and score scenarios; `test_dem_site` runs a short E2E slice.

## Framing

How much regression protection S3/S4 need before S6 without maintaining a large frozen JSON.

## Options considered

1. **A — Golden week series in repo**: assumes regressions in aggregation are common; consequence: maintenance on every legitimate formula change.
2. **B — Rely on X/Y/Z, unit tests, short E2E, and hand Z cases including new layer-0 `lit` and layer-1 shape**: assumes gaps in long-window aggregation are acceptable until a failed checkpoint; consequence: no frozen full-week oracle in v1.
3. **C — Golden only for aggregates, not hourly arrays**: middle ground; deferred unless a regression appears.

## Decision

**B.**

## Rationale

pj initially saw no need for a golden oracle after the X/Y/Z explanation.

## Checks raised

- Long-window aggregation bugs may slip through → accepted for v1; add golden or aggregate fixture only if a regression is found or Sunday checkpoint fails.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s3_s4_golden_week_series | out_v1 | No committed full-week expected output in CI |
| s3_s4_validation | d_41fa_xyz_plus_unit_and_short_e2e | Extend Z for `lit` minimum and layer-1 hand checks when implemented |
| s3_s4_golden_reopen | on_regression_or_failed_checkpoint | Option C or A without reversing B |

## Expected behavior and validation

Wrong if a silent change to `series()` or `score()` breaks a week-long window but short tests stay green and the demo lies; mitigation is extend E2E window or add a golden when discovered.

## Consequences

- Production test window `D-aa58` (2027-01-01–07) remains for richer tests but not a frozen golden file obligation in v1.