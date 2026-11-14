---
id: D-20261114-pj-f369
title: "Horizon mask from LOLA DEMs with a distance-graded resolution schedule to 250 km"
date: 2026-11-14T13:01:55Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-12b7
concepts: [topographic horizon mask, illumination metrics]
supersedes: []
relates: [D-20261114-pj-4ffe, D-20261114-pj-d7d9, D-20261114-pj-9f04, D-20261111-pj-60ab]
ai: options+critique
---
# Horizon mask from LOLA DEMs with a distance-graded resolution schedule to 250 km

## Context

Horizons and the local kernels (`D-20261114-pj-4ffe`) give Sun and Earth elevation above a smooth horizon; they know nothing about terrain. Blocking comes from a topographic horizon mask computed from LOLA DEMs published by PGDA (5 m site and 87–90°S mosaics, 10 m from 83°S, 20 m and 80 m from 80°S, 120 m and 240 m from 60°S; nothing finer than 5 m). The mask is θ(az) = max over distance d of atan((h(d) − h0 − d²/2R) / d), R = 1737.4 km. It depends on the site, not the date, so it can be precomputed. Storage is cheap (2.9 KB per mask); compute is the bottleneck.

Evidence gathered 2026-11-14 (scripts kept outside the repo; to be ported into tests):

- **Reach.** On 56 sites between 80°S and 90°S (240 m DEM), the point that sets the horizon was never farther than 196 km; cutting at 150 km lost up to 0.49° (about one solar disc), cutting at 200 km lost nothing. The pure worst case (deepest floor, −9,127 m, looking at the highest peak, +7,025 m) gives 237–269 km.
- **Resolution by distance.** On 28 points (4 PGDA 78 sites at 5 m), degrading one distance band at a time: the first 250 m dominate (10 m there: up to 1.6°); errors fall roughly as height error / distance; 240 m is enough beyond 25 km.
- **Sun.** Hourly 2027 sub-solar points from Horizons; local az/el derived from them matched Horizons topocentric values to 0.0013° in elevation. At these sites the Sun stays within ±2.9° of the smooth horizon and visits every azimuth each lunar day, so mask errors matter only where the horizon lies in that elevation band (median 33% of azimuths), and they are amplified in time because the Sun's elevation changes by only ~0.004°/h near the pole.
- **Output-level error of the chosen schedule** vs a reference (5 m to 5 km, 80 m to 250 km), 28 points, 2027: longest night max 1 h; longest lit period max 1 h (any part of the disc), 2 h (half disc, shadows ≤ 5 h bridged), 46 h at one point (75% of the disc, bridged); average illumination max 0.32 points. With 240 m in 5–25 km the longest night was off by 7 h at one point.
- **Mission data.** VIPER: 50 h hibernation in darkness (70 h in the requirement), 9 h of shadow operations, safe havens picked on a 1 m DEM. Blue Ghost M1 (CLPS): about 5 h on battery after sunset. Artemis III: continuous light for the 6.5-day stay; ≥ 10 consecutive days considered favourable.
- **Compute.** The schedule costs ~2,600 samples per ray × 720 rays; measured ~150 ms per mask on one core, 22 masks/s on pj's 12 threads.

## Framing

Pick the DEM resolution at each distance and the maximum distance so that what the user sees (longest night, consecutive days of light) stays within a tolerance taken from real missions, at a compute cost that a ~20 EUR/month server and pj's PC can absorb.

## Options considered

1. **A — One DEM resolution for the whole ray**: simple; 240 m everywhere was off by up to 37 points of illumination and 1,289 h of longest night; fine resolution everywhere is unaffordable over the region.
2. **B — Two maps (fine near, coarse far)**: cheaper; the cut distance decides the error.
3. **C — Distance-graded schedule, finer near, precomputed over the region and refined on demand**: pj's proposal; cost dominated by the far bands, error by the near bands.

## Decision

**C.** Masks use the resolution schedule and 250 km reach in Values. The whole 80–90°S cap is precomputed (1 km spacing for the demo, 100 m during the paid server month). When a user loads a site, a finer mask is computed and added to the dataset. Results shown to the user are computed from the stored masks at query time, so the user chooses what counts as light (a fraction of the solar disc) and how long a shadow can be bridged. The default tolerance for both the longest night and the longest lit period is 5 h. When the user's settings fall outside what the schedule guarantees, the interface warns.

## Rationale

"The mask depends on the site, not on the date, so most of it can be precomputed. Higher precision near than far. Precompute everything following that same principle at a lower level, refine when a user loads a site, and add the result to the dataset. Maximum distance: where the tallest relief at the south pole can no longer change anything significantly — Everest can't block my Sun."

On the tolerance: "If a typical CLPS has about 5 h, our limit has to be about 5 h, no more." On the lit period: "5 h, the same as for the longest night (based on a typical CLPS); that is the default and can be changed; if it is not guaranteed, we warn in the interface." On what counts as light: "The user marks what light is for them (a fraction)." On bridging short shadows: "It makes complete sense."

## Checks raised

- An error in degrees says little near the pole; pj asked for the threshold in output terms → longest night and longest lit period, in hours.
- The first schedule (240 m in 5–25 km) failed the 5 h limit at 1 of 28 points → pj moved 5–25 km to 80 m.
- A strict "continuous light" count is fragile: one short grazing shadow splits a period → bridging shadows up to N h, N chosen by the user.
- The 28 test points all had long nights (≥ 392 h); the error near the 50 h VIPER-like regime is not yet measured → re-check on the demo site.
- The reference is the 5 m LOLA DEM, not ground truth; it is ~90% interpolated and has 0.3–0.5 m RMS height error (Barker et al. 2021).
- Observer height 2 m and 720 azimuths were the AI's test settings, not pj's choice; results change with observer height.

## Values

| Name | Value | Notes |
|------|-------|-------|
| horizon_max_distance_km | 250 | Observed max 196 km; theoretical worst case 237–269 km |
| dem_schedule_0_250m | finest available: 5 m (87–90°S mosaic, PGDA 78 sites), else 10 m (from 83°S), else 20 m (80–83°S) | pj: "si hay datos, adelante" |
| dem_schedule_250m_1km | 20 m | |
| dem_schedule_1_2km | 40 m | |
| dem_schedule_2_5km | 100 m | Same result as 80 m in the test, ~10% cheaper |
| dem_schedule_5_25km | 80 m | 120 m where rays leave the 80 m coverage (north of 80°S) |
| dem_schedule_25_250km | 240 m | Existing PGDA product |
| mask_azimuths | 720 (0.5°) | AI test setting |
| observer_height_m | 2 | AI test setting; to be confirmed |
| longest_night_tolerance_h | 5 | Default, user-adjustable; from Blue Ghost M1 |
| longest_lit_tolerance_h | 5 | Default, user-adjustable; warn in UI when not guaranteed |
| light_definition | user-chosen minimum fraction of the solar disc | |
| shadow_bridge_h | user-chosen; default 5 | Shadows up to this long do not break a lit period |
| precompute_demo | 80–90°S at 1 km spacing | ~4 h on pj's PC, ~6–13 h on a CX43 |
| precompute_full | 80–90°S at 100 m spacing during the paid server month | ~26–52 days on a CX43; a second month if needed |
| demo_site_refinement | deferred — spacing and resolution around the demo site, decided when the site is chosen (computed on pj's PC) | |
| refined_masks_policy | user-triggered fine masks are added to the dataset | |

## Expected behavior and validation

"That much more resolution is needed and the current one is poor (judged against the 3D view we build, or another way)."

Objective check available: compare average illumination at PGDA 78 sites against the published PGDA 69 long-term averages.

## Consequences

- Precompute and serving need a server; hosting is a separate advise decision.
- The ~2,600 samples per ray are 86% far-field (5–250 km); sharing the far field between neighbouring sites is an experiment that could cut the 100 m run to days.
- PGDA files are needed locally on the compute host (the 5 m mosaic cannot be read by HTTP range requests); DEMs are processed in tiles because 10 m and 20 m mosaics do not fit in pj's 7 GB RAM.
- The tolerance test (schedule vs 5 m/80 m reference on fixed sites and a fixed year) becomes part of the test suite.
