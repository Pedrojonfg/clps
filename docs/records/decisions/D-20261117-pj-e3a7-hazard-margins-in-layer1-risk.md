---
id: D-20261117-pj-e3a7
title: "Temperature and dust margins enter the layer-1 risk product (values open)"
date: 2026-11-17T20:05:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: method & validation
task: none
concepts: [layer 1 risk, hazard margins, temperature, dust]
supersedes: []
relates: [D-20261114-pj-5cfa, D-20261114-pj-de42, D-20261114-pj-7520, D-20261114-pj-41a2, D-20261115-pj-06cb, D-20261117-pj-7b2d]
ai: options+critique
---
# Temperature and dust margins enter the layer-1 risk product (values open)

## Context

`D-5cfa` makes temperature and dust limits layer-0 gates only. In `score.py` the layer-1 risk `R` is built from
schedule terms alone (night or battery, no-Earth, lit) and `layer2 = 0.0`. So a site at 99 % of a temperature
limit scores the same as one at 50 %, while for night or Earth the margin counts. pj's view: if the user sets a
temperature or dust limit so that it is in the score, it is logical that it is also in the risk part.

## Decision

1. Temperature and dust enter `R` as `Φ(slack / σ)` terms, like the schedule terms, when the user sets the
   corresponding limit (as the lit term only exists when its minimum is > 0).
2. Slack is the distance to the limit: `max_temperature_k − temperature_k`, `temperature_k_min − min_temperature_k`
   (if set), and `soil_resistance − min_soil_resistance`.
3. Layer 0 (`D-5cfa`) is unchanged: crossing a limit still gives 0.
4. **σ comes from spreads wherever one exists (pj's rule)**; where none is published, from the spread of our own
   data. Numeric values are still open (see below).

## Why σ is open

The hazard providers return a single value with no uncertainty. Temperature is a Diviner seasonal local-time
climatology, not the temperature of that hour (`D-41a2`); dust is a soil-resistance proxy with a label that says
it is not a lofting rate (`D-06cb`). The error of either as a prediction is not recorded anywhere in the code.

## Research on spreads (2026-11-17)

**Temperature (Diviner PCP, `D-41a2`).** The published product has no spread: the PDS/ODE description lists
position, longitude, latitude and the average bolometric temperature, with no standard deviation, observation
count or error file, and says only that empty bins are excluded. The Williams et al. (2019) paper could not be
read (HTTP 403) and the LPSC abstract has no uncertainty figure, so an absolute calibration error is not
established here. Consequence: a published per-bin σ does not exist for what we serve.

**What we can measure from our own PCP bins** (illustrative, Site01, 5 bins around the site, not a test):
spread of the pixels within 1 km of the point is ~3–12 K in summer and ~1.4–2.5 K in winter; the same pixel
changes by ~2–6 K between adjacent 0.25 h bins in summer and ≤ ~2 K in winter. This is terrain and timing
variability of the climatology, not instrument error.

**Dust (`D-c82e` constants).** No published σ for the proxy, but its inputs have verified ranges (Metzger 2024,
Parts 1–2): bulk density 1100–1920 kg/m³, ⟨D⟩ 1.1–2.0 · D84 (196–356 µm), cohesive energy density α 0.11–1.72 J/m³
(analogs; k only known within a factor of 3). An illustrative propagation gives a resistance of ~0.2–2.5 J/m³,
about one decade (σ_ln ≈ 0.6). The earlier Apollo kPa ranges (Mohr-Coulomb cohesion) do not belong in this proxy.

## Options for σ

1. **A — Fraction of the limit**: arbitrary k; not a spread. Not chosen (does not follow pj's rule).
2. **B — Published spread**: not available for temperature; possible for dust once the constants' ranges are
   verified.
3. **C — Spread of our own data (temperature)**: σ_T = combination of the spatial spread of the PCP pixels around
   the site and the difference to the adjacent local-time bin; computed per request from bins already loaded.
   Honest label: variability of the climatology, not calibration error.
4. **D — Propagated spread (dust)**: interval/Monte-Carlo propagation of the constants' ranges through the
   proxy.

**Decided by pj:** C for temperature, **for v1 only; to be reopened** (a published or better-grounded spread, or
the calibration error, should replace it). For dust, D, **grounded in scientific research** (deep-research pass
to verify the constants' ranges and find the best-supported spread); until it lands the dust σ stays open.
Both labelled provisional in provenance.

## Criteria for change

- Wrong if, after adding the terms, the ranking of feasible sites on the validated cases changes in ways that
  hazards alone do not explain (the product is multiplicative, so a weak hazard margin can dominate `R`).
- Wrong if the dust term, being a proxy, makes `R` swing on differences smaller than the proxy's own error.
- If neither a source nor a defensible k exists for a factor, keep it layer-0 only for that factor and say so in
  provenance.

## Consequences

- `_layer1_score` takes hazards; provenance lists the σ used and marks them provisional.
- The temperature dependence of battery capacity and heater load stays out of v1 (`D-7b2d`); this decision does
  not couple them.
- Before implementation: verify the dust constants' ranges against the papers, and decide how to combine the
  spatial and adjacent-bin spreads for temperature (sum in quadrature is the simplest).
