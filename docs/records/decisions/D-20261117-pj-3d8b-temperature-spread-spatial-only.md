---
id: D-20261117-pj-3d8b
title: "Temperature spread for the layer-1 margin is spatial only"
date: 2026-11-17T22:30:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: method & validation
task: none
concepts: [temperature spread, layer 1 risk, Diviner PCP climatology]
supersedes: []
relates: [D-20261117-pj-e3a7, D-20261114-pj-41a2, D-20261114-pj-7520]
ai: options+critique
---
# Temperature spread for the layer-1 margin is spatial only

## Context

`D-e3a7` set the v1 temperature σ as the spatial spread of the PCP pixels around the site combined, in
quadrature, with the mean change to the adjacent 0.25 h local-time bins. Implemented and run on Site01
(one day), that gave σ ≈ 117 K at the hottest hour and ≈ 93 K at the coldest. Reducing the spatial radius from
1 km to 300 m did not change it, so the adjacent-bin term was the driver: at that site the temperature of the same
pixel jumps by ~100 K between consecutive bins (lit ↔ shaded). With σ ≈ 100 K against a 320 K limit the margin
term `Φ(slack/σ)` is ~0.8 for any site and does not separate safe from unsafe ones.

## Decision

Drop the adjacent-bin term. The temperature σ is the standard deviation of the PCP pixels of the same
local-time bin around the site, nothing else. This amends only the temperature σ rule of `D-e3a7`; the rest of
that record (margins in `R`, dust, layer 0 unchanged) stands.

## Rationale

pj: the Sun does not move, so the neighbouring local-time bins are not an uncertainty of the site's temperature.
(Not independently verified here; see the criteria.)

## Values

| Name | Value | Notes |
|------|-------|-------|
| temperature_sigma_source | pcp_spatial_spread_v1 | Goes in provenance |
| temperature_sigma | std of same-bin pixels | Not the adjacent bins |
| temperature_sigma_radii_m | 300, 500, 1000 | Smallest radius holding ≥ 4 pixels; the product omits empty bins, so the 3×3 neighbourhood (~5 pixels) is often too sparse |
| temperature_sigma_none | no pixels ≥ 4 within 1 km | The temperature margin then stays layer 0 only, as in `D-e3a7` |

## Result on Site01 (one day, same run as above)

σ ≈ 4.6 K at the hottest hour and ≈ 3.2 K at the coldest, from ~100 K. In a sample of bins around Site01 the
300 m spread is 15–40 K where it exists, and several bins have no pixels within 300 m (some none within 1 km).

## Known cost

The adjacent-bin term was the only part that reflected sensitivity to a timing error. Without it a site
whose temperature swings between lit and shaded in minutes gets no extra uncertainty from that.

## Criteria for change

- Reopen if the spread is None (no margin) for a large share of sites in a region scan, since those fall back to
  layer 0 only. A scan of sites with counts of None would show it.
- Reopen if a published absolute calibration error or per-bin uncertainty of the Diviner PCP is found; it should
  replace this estimate.
- Reopen if timing sensitivity turns out to matter for scores (sites at the lit/shaded boundary ranked too high).

## Consequences

- `pcp.spread_k` takes only the bin and the site and widens the radius; `sigma_at_site_time` no longer loads the
  neighbouring bins, which also removes two PCP bin reads per limiting hour.
- `D-e3a7` text on temperature (option C) is superseded by this record for the temperature term.
