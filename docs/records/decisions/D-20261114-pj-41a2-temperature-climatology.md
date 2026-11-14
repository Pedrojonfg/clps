---
id: D-20261114-pj-41a2
title: "Temperature is the polar seasonal local-time climatology"
date: 2026-11-14T15:09:49Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: data & sources
task: T-20261114-pj-d4ce
concepts: [climatology, layer-B in the score, provenance]
supersedes: []
relates: [D-20261114-pj-de42, D-20261114-pj-b8d3, D-20261114-pj-9e53, D-20261114-pj-41fa]
ai: options+critique
---
# Temperature is the polar seasonal local-time climatology

## Context

Layer B is in scope (`D-20261114-pj-b8d3`, `D-20261114-pj-41fa`). The score takes a hazard term (`D-20261114-pj-9e53`, `D-20261114-pj-de42`). No public series predicts temperature at an arbitrary future hour (`docs/resources.md`). For 80–90°S, Diviner's polar cumulative maps give bolometric brightness temperature at 240 m, split into summer and winter, and into local-time bins of 0.25 h (Williams et al. 2019). Empty bins are omitted. At these latitudes topography dominates, and a formula with incidence, albedo and thermal inertia and no terrain is not that measurement.

## Framing

The number attached to a site and an hour is a published climatology for that season and that local solar hour. An extra correction of those kelvin by solar elevation stays out until a temperature problem is noticed by eye.

## Options considered

1. **A — No temperature number**: assumes the score can omit it; consequence: a thermal limit cannot zero or rank a case.
2. **B — One static map per site**: assumes the hour does not matter; consequence: the chosen hour does not change the number.
3. **C — Day bin or night bin, and a distance-weighted mean of the two nearest pixels when the point is missing**: assumes local-time day and night are the right split; consequence: two boxes, and the fill crosses pixels the product leaves empty.
4. **D — Look up the polar map for that season and that local-time bin**: assumes the published climatology is the number; consequence: 96 bins per season at 240 m from 80°S to the pole. Still not the future hour.
5. **E — Compute temperature from incidence angle, albedo and thermal inertia**: assumes that formula is the finer instrument; consequence: a model on top of measurements that already include slope, albedo and rocks.

## Decision

**D.** Polar seasonal local-time climatology. No extra kelvin adjustment by solar elevation.

## Rationale

For now we simply use the climatology, simple and sufficient. Because the dataset already takes solar hours into account, the change will not be necessary at first.

## Checks raised

- A physical model (incidence, albedo, thermal inertia) was taken to be the more precise number → kept D after the polar-measurement check.
- Solar elevation as a further kelvin correction, including a proposed neighbor-bin comparison as the reopen trigger → neighbor-bin comparison dropped. Reopen only if a temperature problem is noticed by eye.
- Lunar wind as another easy input → not used.
- What to return when the bin has no pixel → `D-20261114-pj-affb`.

## Values

| Name | Value | Notes |
|------|-------|-------|
| temperature_quantity | polar_seasonal_local_time_climatology | 80–90°S, 240 m, summer/winter as published, local-time bins of 0.25 h (Williams et al. 2019). Bolometric brightness temperature. Not the temperature of the future hour. |
| temperature_hour_selection | local_solar_time_from_ephemeris | The ephemeris selects the bin. This is not an elevation correction. |
| temperature_elevation_adjustment | deferred — reopen only if a temperature problem is noticed by eye | No kelvin correction until then. |
| temperature_product_id | deferred — pin the PDS release id when the grids are fetched | |

## Expected behavior and validation

This choice would be wrong if elevation were relevant. Reopen only if a temperature problem is noticed by eye.

## Consequences

- S5 reads this climatology for the season and the local solar hour, and names the product, the season and the bin in provenance (`D-20261114-pj-de42`, `D-20261114-pj-3c91`).
- No elevation term is implemented with the score.
- Empty-pixel behavior is `D-20261114-pj-affb`.
