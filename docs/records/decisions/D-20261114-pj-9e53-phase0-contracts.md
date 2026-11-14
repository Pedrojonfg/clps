---
id: D-20261114-pj-9e53
title: "Phase 0 engine contracts: sky, mask, visibility, score signature, seams, stack, fixtures"
date: 2026-11-14T14:21:18Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: contracts
task: T-20261114-pj-b63a
concepts: [visibility series, provenance]
supersedes: []
relates: [D-20261114-pj-de42, D-20261114-pj-41fa, D-20261114-pj-b8d3, D-20261114-pj-f369, D-20261114-pj-4ffe]
ai: recommended
---
# Phase 0 engine contracts: sky, mask, visibility, score signature, seams, stack, fixtures

## Context

The approved implementation plan locked P1–P3 and P5–P7 at the gate, plus the `score(...)` signature (P4 contract; formula is `D-de42`). `lunar_eval/providers.py` on `scope/ops-skeleton` already declares P1, P2 and P5. Without a decision record the types are uncited and lanes can diverge.

## Framing

One shared shape for Sky, Terrain, Engine, Search and Viz. Changing a field later is a new decision, not a silent edit.

## Options considered

1. **A — Record the plan-gate contracts as written**, including the `score` signature.
2. **B — Same, with a field changed now.**
3. **C — Do not record; the code is the source of truth.**

## Decision

**A.** The contracts below. Azimuth is from north through east. Elevation in the ephemeris is above the smooth horizon; the mask is topographic (`D-f369`). Moon is the only implemented body (`D-b8d3`).

## Rationale

Accepted the recommendation: record the plan-gate contracts as written.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| ephemeris_contract | sky(site, times) → {time_utc, sun_az_deg, sun_el_deg, sun_radius_deg, earth_az_deg, earth_el_deg, earth_radius_deg} | P1; az north-through-east; el above smooth horizon |
| horizon_mask_contract | mask(site) → float32[720] + {x_m, y_m, lat, lon, h0_m, observer_height_m, schedule_version, dem_ids} | P2; 0.5° bins; bin count already `mask_azimuths` in `D-f369` |
| horizon_mask_store | mmap npy per 100 km tile + parquet index | P2 |
| visibility_series | hourly sun_fraction, earth_fraction in [0,1]; flags from user fraction thresholds; longest night; longest lit with bridged shadows | P3; metrics in `D-f369` |
| score_contract | score(series, hazards, needs) → {score, feasible, breakdown, provenance} | P4 signature; formula `D-de42` |
| provider_seam | Body, EphemerisProvider, HorizonProvider, SurfaceHazardProvider | P5; Moon only |
| stack | package lunar_eval; FastAPI; static web page; pyproject.toml owned by Ops | P6 |
| fixtures_layout | Horizons tables under tests/fixtures/horizons/ (fetched once, app User-Agent); DEMs and masks in data/ (gitignored), never in git | P7 |

## Expected behavior and validation

S1–S4 and the views consume these field names. A PR that adds, removes or renames a sky, mask, series or score field without a new decision is a contract break. Pytest on the skeleton already imports `SkySample` and `HorizonMask` with this shape.

## Consequences

- Citations: `# per D-20261114-pj-9e53` on the provider types. `observer_height_m` and 720 bins stay owned by `D-f369`.
- Neutral hazard term until P13 (`D-de42`).
- SpiceyPy vs Skyfield is not set here (`D-4ffe` still deferred).
