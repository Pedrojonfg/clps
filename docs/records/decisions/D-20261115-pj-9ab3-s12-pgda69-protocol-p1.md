---
id: D-20261115-pj-9ab3
title: "S12 PGDA 69 protocol: ~18.6 y average illumination at PGDA-78 sites; report only"
date: 2026-11-15T12:05:59Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: method & validation
task: T-20261115-pj-98c4
concepts: [PGDA 69 averages, illumination metrics]
supersedes: []
relates: [D-20261114-pj-f369, D-20261114-pj-41fa, D-20261115-pj-fe17, D-20261115-pj-1a9e]
ai: recommended
---
# S12 PGDA 69 protocol: ~18.6 y average illumination at PGDA-78 sites; report only

## Context

`D-f369` names an objective check: average illumination at PGDA 78 sites vs published PGDA 69. `D-41fa` notes the ~18.6 y nutation cycle and matching light definition. pj asked for advise on protocol parameters.

## Framing

Make the comparison defendable (same span and light definition as the map) without inventing a product pass/fail bar in v1.

## Options considered

1. **P1 — ~18.6 y, aligned light def, PGDA-78 sites, report only** (recommended).
2. **P2 — P1 plus a CI threshold (e.g. \|Δ\| ≤ 5 percentage points).**
3. **P3 — Single year (e.g. 2027) with explicit caveat.**
4. **P4 — One or two demo sites only.**

## Decision

**P1.** Compare **average solar illumination** from PGDA 69 (south polar product covering the sites) to our computed mean lit fraction at **PGDA 78 / 5 m** sites used for the schedule work (or the documented subset with clear coordinates and fine DEM). Our mean uses the **same light definition** as the map (any part of the solar disc visible, unless the product label states otherwise — cite the label in the report) over **~18.6 years** (or the exact span of the chosen PGDA 69 file). Metric: per-site difference in **percentage points** (ours − map). Write results to `docs/validation.md` via script. **No product pass/fail threshold** in v1.

## Rationale

Accepted the recommendation: P1 is the most coherent with what is already decided.

## Checks raised

- Heavy compute / tests may fail overnight → accepted; fix before final product (`D-1a9e`).
- README must not claim completed PGDA 69 validation until numbers exist → agreed (`D-fe17`).

## Values

| Name | Value | Notes |
|------|-------|-------|
| s12_pgda69_product | average_solar_illumination_south | PGDA 69; cite exact file/resolution in validation.md |
| s12_pgda69_sites | pgda78_5m_schedule_set | Document actual IDs/coords in validation.md |
| s12_pgda69_span | ~18.6y_or_product_label_span | Required for fair comparison (`D-41fa`) |
| s12_pgda69_light_def | match_product_label_any_disc_default | State in report |
| s12_pgda69_metric | delta_percentage_points_per_site | ours − map |
| s12_pgda69_pass_fail | none_v1_report_only | Threshold would be a new decision |
| s12_pgda69_output | docs/validation.md_plus_script | |

## Expected behavior and validation

Wrong if the comparison uses a mismatched year span or light definition while claiming agreement with PGDA 69. Overnight failures allowed until final product.

## Consequences

- Informs report/README role (`D-fe17`); does not enter score or X/Y/Z.
- Implementation is overnight-friendly scripts (`D-1a9e`).
