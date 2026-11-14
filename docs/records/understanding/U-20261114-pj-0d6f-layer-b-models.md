---
id: U-20261114-pj-0d6f
person: pj
date: 2026-11-14T14:45:00Z
task: T-20261114-pj-d4ce
---
# Layer-B models — pj

## Concepts

| Concept | Role | Status | Source | Evidence | Next check |
|---------|------|--------|--------|----------|------------|
| climatology | core | shaky | teaching this session; Williams et al. 2019; `D-20261114-pj-41a2` | Confirmed the climatology and rejected an elevation correction. Reason tracks the teaching: the dataset already bins by solar hour. Falsification: wrong if elevation were relevant; reopen only if a problem is noticed by eye. No unaided mechanism | 2026-11-20 explain why the seasonal hourly map is the temperature number |
| nodata fill | core | shaky | `D-20261114-pj-affb`; gdal_fillnodata | Chose four-quadrant inverse distance with GDAL defaults. The conventional reason repeats the brief. Own failure case: a crater at the point only. Kept the fill after being told relief does not zero the score | 2026-11-20 say what actually zeros the score when the filled kelvin is wrong |
| hazard proxy | core | shaky | `D-20261114-pj-050d`; Metzger 2024 | Chose Metzger soil-resistance with Apollo-average soil and PGDA slope when the slope factor is found; rock and roughness out. Falsification: unidentified factors; still called it the best available approximation. Accepted label is resistance not lofting rate | 2026-11-20 state what the dust row in provenance must name |
| layer-B in the score | hazard | introduced | `U-20261114-pj-6692`; this session | Prior session expected an hourly temperature dataset. This session restated that the public products are not that dataset, before pj chooses the number | when pj states the temperature number: the label has to match the product |

## Notes

- Agenda accepted 2026-11-14. Teaching is on the way, inside each decision, not a prior exam.
