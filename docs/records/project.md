---
legacy: []
default-branch: main
---
# Project

Solo portfolio project: a **site×time landing evaluator** with a Moon beachhead (south-pole power and DTE under local horizon), inspired by the NASA Space Apps 2026 challenge “CLPS Lunar Mission Browser.” Not a contest team entry and not scheduled against the 14–15 November 2026 hackathon window. Owner builds alone; challenge text is heritage for the problem shape (`D-20261114-pj-7e2a`).

## Language

- Chat: each person's choice (owner: Spanish)
- Repo (records, code comments, docs): English

## Ownership

| Domain | Mode | Notes |
|--------|------|-------|
| problem framing | own | the question the project answers and for whom |
| scope & success criteria | own | what is in/out for portfolio v1, what "done" means |
| method & validation | own | everything that changes what is computed, against what it is checked, what error is acceptable |
| data & sources | own | datasets, versions, which sites/regions, what is cited |
| claims & interpretation | own | what the project says its results show |
| team & roles | own | solo; no recruitment |
| architecture | advise | include body-agnostic seams early (`D-b8d3`) |
| contracts | advise | data formats between modules |
| testing | advise | |
| presentation | advise | portfolio README, demo story (not Space Apps submission page) |
| dependencies & ops | advise | libraries, hosting, licences |
| engineering hygiene | auto | naming, layout, style matching the repo |
| rules & eligibility (Space Apps) | out | not targeting contest submission |

When unsure, prefer own over advise, and advise over auto. `people/<h>.md` may tighten a mode for one person.
Owner defends every own decision; reopen explicitly via a new decision record (do not silently drift).

## Sources

- `docs/sources/challenge-statements/clps-lunar-mission-browser.md` — full statement (Background, Objectives, Considerations) from owner copy 2026-11-11; Resources tab empty at copy time. Heritage only.
- https://www.spaceappschallenge.org/2026/challenges/clps-lunar-mission-browser/ — official challenge URL (heritage).
- https://naif.jpl.nasa.gov/pub/naif/pds/pds4/clps/clps_spice/document/spiceds_v003.html — CLPS SPICE Data Archive documentation.
- https://ntrs.nasa.gov/citations/20240005553 — NASA Ames “Lunar Browser” trajectory tool (different product; out of our scope per `D-b8d3`).
- `docs/research/briefs/research-brief-clps-domain.md` — domain brief for planning scales and data menu.
- https://ssd.jpl.nasa.gov/horizons/ — JPL Horizons (ephemerides; surface observer geometry).
- https://pgda.gsfc.nasa.gov/products/69 — PGDA polar illumination / Earth visibility maps.
- https://trek.nasa.gov/moon/ — Moon Trek (LRO-based visualization tiles).
- Official Space Apps challenge resources for Lunar Landing Site Navigator (QuickMap, Moon Trek, Horizons, CSA portal) — useful as viz/ephemeris references; datasets still LOLA/PDS for terrain.

## Product decisions (current)

| ID | Title | Status |
|----|-------|--------|
| `D-20261111-pj-60ab` | Product question (scored site-time + search) | accepted |
| `D-20261114-pj-7e2a` | Solo portfolio frame | accepted |
| `D-20261114-pj-3c91` | Audience (portfolio-technical) | accepted (supersedes `D-ea51`) |
| `D-20261114-pj-9f04` | Portfolio scope & done | accepted (supersedes `D-5cf6`) |
| `D-20261114-pj-b8d3` | Layer B surface / trajectory / multi-body | accepted |

## Milestones

- Product ledger closed for portfolio frame — 2026-11-14 (`T-20261114-pj-a1b2`)
- Next: engine ledger (score/X,Y,Z, recommender, data/horizon, layer-B models, validation/claims)
- No hackathon submission milestone
