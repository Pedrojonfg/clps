---
id: U-20261114-pj-3839
person: pj
date: 2026-11-14T11:20:02Z
task: T-20261114-pj-12b7
---
# Data and visualization sources — pj

## Concepts

| Concept | Role | Status | Source | Evidence | Next check |
|---------|------|--------|--------|----------|------------|
| Quickmap / Moon Trek / Horizons roles | prerequisite | shaky | warm-up retrieval | Could not say what Horizons returns for a south-pole site or what it lacks for the real horizon ("ni idea"); AI then explained ellipsoid elevation vs DEM horizon mask | before agenda item 2 (geometry path): explain in own words what Horizons lacks at Shackleton rim |
| appetite | core | introduced | D-20261114-pj-d7d9 | Chose full portfolio scope for a day and a half and proposed a later window (to 20 Nov) with a hack cut after the fixed-time check was raised; falsification answered ("run out of time by tomorrow") | — |
| scope | core | introduced | D-20261114-pj-d7d9 | Kept D-9f04 whole and rejected the lite plan; cut to be defined later, prompted by the checks | — |
| Quickmap / Moon Trek / Horizons roles | prerequisite | shaky | decision 3 prompt | Correctly said Horizons has no knowledge of local relief so cannot tell if terrain blocks the Sun; restates the AI's earlier explanation, not yet applied | when the first DEM mask exists: explain why a site with Sun at +1.58° can be dark |
| ephemeris | core | introduced | D-20261114-pj-4ffe | After teaching (service vs local kernels), chose local kernels for learning; proposed, unprompted, a runtime cross-check limited to the search-proposed solution; falsification answered | first test vs Horizons: explain which convention caused the largest residual |
| topographic horizon mask | core | introduced | D-20261114-pj-f369 | After teaching (formula, curvature, disc size), noted unprompted that the mask depends on the site and not the date, proposed precompute-plus-refine and the "tallest relief can't matter beyond some distance" cut; said "I understand the formula but not the decision" before the 15-year-old explanation | on the demo site: predict which distance band dominates its mask error, then check |
| illumination metrics | core | introduced | D-20261114-pj-f369 | Needed a 10-year-old explanation of why mask error matters only where the horizon lies in the Sun's elevation band; then anchored tolerances in mission data (5 h from Blue Ghost) and asked whether a short shadow really hurts a CLPS lander, leading to bridged lit periods | explain why a 75%-of-disc light definition is less robust than "any sliver" |
| hosting | supporting | introduced | D-20261114-pj-5994 | Accepted the AI recommendation; set the budget (~20 EUR/month, a second month if needed) | — |

## Notes

- Warm-up on the debt carried from U-20261111-pj-9197. Teaching given: Horizons elevation is relative to the plane perpendicular to local zenith on the reference surface (Horizons manual, EL), not the visible terrain horizon; terrain profile comes from a LOLA DEM (PGDA); QuickMap/Trek show long-term averages or pictures, not a number at a chosen date through an API.
