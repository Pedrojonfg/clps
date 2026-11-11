# Research Brief: CLPS challenge domain (planning, data, landing factors)

**Depth:** focused  
**Date:** 2026-11-11  
**Purpose:** Facts for the owner before any product decisions (`T-20261111-pj-c84f`). Not a build spec.

## Executive Summary

Real lunar landing **site selection** joints many disciplines (terrain, illumination, comms, traverse, science, EDL hazards). The **Space Apps CLPS Lunar Mission Browser** brief (mirrored text; official page not archived in-repo) narrows the ask to an **intuitive comparison of candidate sites and dates** via **Sun and Earth relative to the local horizon**, for **solar power** and **direct-to-Earth (DTE) communication** near the **south pole**. Public NASA data exists at multiple levels of readiness (precomputed maps, DEMs, Horizons, SPICE). A **recommendation engine** only becomes meaningful after defining the **search space** (which sites, which time granularity, which metrics, which constraints)—all `own` domains still open.

## Two layers (do not conflate)

| Layer | Question | Typical factors | Hackathon brief (mirror) |
|-------|----------|-----------------|---------------------------|
| **A. Challenge product** | Compare sites/dates quickly with a visual UI | Horizon Sun/Earth, power & DTE windows | Explicitly in brief |
| **B. Real landing campaign** | Can we land and operate safely and complete mission goals? | Slope/roughness, PSR proximity, thermal, regolith, dust, EDL lighting along approach, ΔV, mass margins | Mostly **out of brief** unless we voluntarily expand scope |

Decisions about layer B before understanding layer A tends to produce nonsense scope (your point).

## How much flexibility do planners actually have?

Scales differ by **what is being traded**. Figures below are illustrative ranges from open literature on south-pole crewed/Artemis-style planning and CLPS delivery model—not a single NASA handbook.

| Knob | Typical planning granularity | Notes |
|------|-------------------------------|-------|
| **Launch date** | Weeks to **months** (sometimes wider for CLPS task orders) | Tied to vehicle readiness, pad, and trajectory families (Ames Lunar Browser trajectory DB is about this scale). |
| **Landing date/time within a mission** | **Hours** (sometimes days of slip) | Illumination and DTE at the pole are time-sensitive; studies often use **1 h** sampling (e.g. Artemis III suitability analysis on LOLA terrain, SPIE 2024). |
| **Landing region** | **Kilometres** (named sites/regions) | Artemis III uses **13 pre-selected regions**; CLPS vendors work inside NASA-approved areas (see NASA CLPS landing sites map). |
| **Point within region** | **Metres to hundreds of metres** (terrain-dependent) | High-res DEMs at 5–20 m/posting (PGDA 78, 90) support local slope/horizon; ellipse size is mission-specific. |
| **“Flexible location” for a recommender** | Must be **defined in data** | Useful flexibility is whatever you can evaluate: discrete site list, lat/lon grid, or rover traverse—not continuous “anywhere on the Moon” without a model. |

**Time cycles that matter at the south pole (challenge-relevant):**

- **~2-week-scale** coupling between libration-related **DTE** and **solar** conditions appears in NASA south-pole approach analyses (NTRS 20220011040).
- **~27.3 d sidereal** motion of Earth in the sky as seen from the pole region (Artemis constraint papers).
- **Mission duration** for short sorties: order **days** on surface (e.g. Artemis III planning references ~**6.5 Earth days** max surface ops in recent pole constraint work—not necessarily CLPS lander ops).

**Cost of “flexibility”:** Changing approach direction or timing to fix lighting/comm often costs **ΔV** and integration work (NTRS 20220011040). A serious recommender should treat big moves as expensive, small moves as cheap—once you define what a “move” is.

## What the hackathon text actually asks (mirror sources)

Unofficial but consistent mirrors (UAE, Seoul, LinkedIn): build a tool for **mission planners, educators, and the public** to **compare landing sites and dates**, visualizing **Sun and Earth vs the horizon** to assess **power generation** and **DTE communication windows**. Existing tools exist but **complicated interfaces** hinder quick evaluation—UX/product problem plus correct geometry.

**Official challenge page + 2026 rules:** still **NOT YET READ** in repo (`project.md` Fog). Dataset list may appear when NASA releases challenge resources (~2026-11-13 per milestones, unconfirmed).

## Landing factors: in the real world vs this challenge

| Factor | Role in real site selection | In narrow brief (A)? |
|--------|------------------------------|----------------------|
| **Solar illumination** (duration, incidence) | Core | **Yes** (power) |
| **Earth visibility / DTE comm** | Core for ops without relay | **Yes** |
| **Local horizon / topography** | Horizon blockers dominate at poles | **Implied** (Sun/Earth *relative to horizon*) |
| **Slope, roughness, rock abundance** | EDL safety | No in brief; data exist (LOLA slope, PGDA) |
| **Permanently shadowed regions (PSR)** | Science, volatiles, thermal | Optional context; PGDA PSR masks exist |
| **Temperature / thermal design** | Hardware survival | No in brief |
| **Dust, plume, regolith bearing** | Landing and optics | No in brief |
| **Landing attitude / “land upright”** | GNC + terrain | No in brief |
| **Approach corridor lighting** | Crewed HLS navigation | Important for Artemis; **optional** for CLPS browser unless you expand scope |

Peer-reviewed pole work (e.g. Speyerer & Robinson, LEAG 2025 summary; Artemis III engineering suitability with LOLA) stresses **joint** Sun **and** Earth visibility over the **planned surface duration**, not annual averages alone—relevant if you claim “planner-grade” validation.

## Data catalog (accessible without proprietary NASA internal tools)

Use this as a **menu**, not a commitment. Verify formats before coding.

| Asset | Provider | What it gives you | Fit to brief A |
|-------|----------|-------------------|----------------|
| **JPL Horizons API** | SSD | Azimuth/elevation of Sun, Earth, etc. from a surface point vs time | Direct match to horizon-style questions |
| **SPICE Toolkit + CLPS archive** | NAIF/PDS | Kernels for CLPS missions, DE440 planets, frames, times | Rigorous geometry; steeper learning curve |
| **PGDA Product 69** | NASA GSFC | Multi-year illumination / Earth visibility / PSR maps | Fast power/comm **without** coding ray-tracing |
| **PGDA Products 78, 90** | NASA GSFC | 5–20 m south-pole DEMs, slopes, uncertainties | Local horizon if you ray-trace; slope for expanded scope |
| **Moon Trek tile layers** | NASA Treks | South pole WAC illumination %, Earth visibility layers (WMTS) | Visual UI + quick comparison |
| **LRO LOLA via PDS** | Geosciences Node | Gridded topography, ODE REST search | DEM source of truth |
| **CLPS SPICE bundle (DOI 10.17189/x5nq-2w30)** | PDS | Observation geometry for flown CLPS deliveries | Validate against real mission times |
| **NASA CLPS landing sites 3D map** | NASA.gov | Named CLPS-related sites (outreach map) | Candidate **labels** for UI, not sole engineering authority |
| **Ames Lunar Browser (NTRS)** | NASA Ames | Trajectory solution DB for Earth–Moon transfers | **Different problem** (launch/cruise); related to CLPS program but not同名 product |

Third-party **Space Data Atlas** pages list APIs above for lunar hackathon-style projects; treat as a index, not primary citation.

**Imagery:** LRO **WAC** global mosaic and south-pole products (via Moon Trek, PDS Imaging); higher-res NAC exists but is heavier to serve in 48 h.

## Existing “complicated” landscape (why the challenge exists)

- **STK / GMAT / SPICE scripts:** full-fidelity but expert-oriented.
- **Precomputed PGDA / Trek maps:** fast to consume, less flexible for arbitrary dates/sites.
- **Horizons:** approachable API, must wire lunar fixed point + horizon definition consistently.
- **Lunar Browser (Ames):** trajectory trades, not necessarily pole horizon UI.

A recommender sits **on top of** whichever geometry layer you pick (maps vs on-the-fly Horizons vs SPICE).

## “Serious validation” (levels)

| Level | Meaning | Feasible in understand-then-48h? |
|-------|---------|----------------------------------|
| **V0** | Spot-check a few cases against published figures or Horizons | Yes |
| **V1** | Cross-compare two independent data paths (e.g. Trek layer vs Horizons) | Maybe, if scoped |
| **V2** | Reproduce a published south-pole case study (e.g. named Artemis region, hourly window) | Stretch goal |
| **V3** | Sign off like mission ops | **No** for hackathon |

Planner-first UX does not automatically require V3; it requires **honest claims** (`claims` domain) about which level you reached.

## Open questions (need official brief or SME)

- Exact **candidate site list** NASA expects teams to use in 2026.
- Whether challenge **requires** on-the-fly computation vs allowing PGDA/Trek products.
- Mandatory **citation** of specific datasets for global judging.
- How 2026 **judging** weights outreach (educator/public) vs technical depth.

## Suggested learning order (before Decide)

1. Read mirrored brief once; archive official text when available.  
2. Walk through **one** site and **one** 48 h interval with Horizons **or** read values off Moon Trek/PGDA for same site.  
3. Write in your words: **what is being compared** (metrics) and **what one “recommendation” would change** (time only, site only, or both).  
4. Only then lock product decisions (audience, recommender search space, validation level).

## Sources

- https://nasaspaceapps.ae/challenges — CLPS Lunar Mission Browser brief text (unofficial mirror)  
- https://naif.jpl.nasa.gov/pub/naif/pds/pds4/clps/clps_spice/document/spiceds_v003.html — CLPS SPICE archive  
- https://pds-geosciences.wustl.edu/missions/clps/index.htm — CLPS PDS payloads + SPICE DOI  
- https://ssd.jpl.nasa.gov/horizons/ — Horizons system (API documented on SSD)  
- https://pgda.gsfc.nasa.gov/products/69 — Polar illumination / visibility maps  
- https://pgda.gsfc.nasa.gov/products/78 — High-resolution south-pole site DEMs  
- https://trek.nasa.gov/moon/ — Moon Trek (tile layers)  
- https://doi.org/10.1117/12.3010268 — Artemis III sites, illumination/comm/slope on LOLA (hourly)  
- https://ntrs.nasa.gov/citations/20220011040 — HLS approach, lighting & DTE, ΔV trades  
- https://www.hou.usra.edu/meetings/leag2025/pdf/5069.pdf — Artemis III pole constraints (Sun, Earth, approach)  
- https://ntrs.nasa.gov/citations/20240005553 — Ames Lunar Browser (trajectories)  
- https://www.nasa.gov/commercial-lunar-payload-services/landing-sites/ — CLPS landing sites (outreach)
