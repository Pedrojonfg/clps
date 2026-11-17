# Domain + UI brief for the 3-4 min talk

Paths are relative to /home/pedrojon/clps. CS = docs/sources/challenge-statements/clps-lunar-mission-browser.md, DB = docs/research/briefs/research-brief-clps-domain.md, VB = docs/research/briefs/research-brief-data-viz-sources.md.

## 1. The problem

**Why it is hard:**
- The south pole is where missions want to go because of water ice. But its geometry creates "extreme variations in solar illumination and Earth visibility". "Small changes in landing location or date can dramatically affect both power generation potential and communication windows" (CS:17).
- The Sun gives power and sets the thermal conditions. Earth decides whether you can talk directly without a relay (CS:15).
- There is no atmosphere, so the horizon is local terrain plus the curve of the Moon (CS:43). At the pole "the terrain term dominates" (VB:38). Crater rims and slopes block a Sun and Earth that sit low in the sky (CS:52).
- Schedules slip. Hardware or launch delays force a fast re-plan: the same site on another date, or another site on the same date (CS:19).
- Time scales: landing time is chosen to the **hour**, and studies sample at 1 h (DB:27). Sun and Earth-link conditions couple on a **~2-week** cycle (DB:33). Earth moves around the sky on a **~27.3-day** sidereal cycle (DB:34). Artemis III plans **~6.5 Earth days** of surface stay (DB:35). What matters is Sun **and** Earth together over the actual stay, not yearly averages (DB:59).
- Permanent shadow (PSR), temperature, slope and dust are "Layer B" real-campaign factors. They are outside the challenge brief (DB:15, DB:47-57). No public time series exists for temperature or dust, so the project uses Diviner climatology and static hazard proxies, labelled as such (VB:9, VB:124-125).
- **Caveat:** the briefs give **no specific sun-angle or temperature figures** (for example "~1.5° sun" or "40 K craters"). Do not quote such numbers as coming from the repo. Source them yourself or leave them out.

**Existing tools and the gap:**
- **QuickMap** (commercial ACT/LROC web GIS): has TerrainShadows, but no public API for "illumination at a time" (VB:31, VB:118).
- **Moon Trek**: NASA viewer with tiles for illumination % and Earth visibility. These are long-term averages, so they cannot replace a score (VB:32).
- **PGDA 69**: illumination, permanent shadow and Earth visibility averaged over **~18.6 years** at hourly steps. "Averages hide the date the planner actually has" (VB:58). It also counts Earth as visible if any part of the disc clears terrain, which is slightly optimistic (VB:58).
- **Horizons**: gives Sun and Earth azimuth/elevation, but measured against a smooth ellipsoid rather than the visible horizon, and it must not be called from a browser (VB:33, VB:36-38).
- **Ames Lunar Browser**: about launch and cruise trajectories, which is a different problem (DB:77, DB:88).
- **STK/GMAT/SPICE**: full fidelity, but built for experts (DB:85).
- **The gap:** these tools are "built for detailed analysis" and "difficult for non-specialists… for rapid scenario comparison". Each site-date pair means "navigating multiple interfaces and interpreting raw data" (CS:21). The four official links "do not expose the site×time score" (VB:9).

## 2. What the user sees

**Horizon planner (`web/index.html`)**
- Inputs:
  - lat/lon (default is PGDA Site01, -89.463, 222.510)
  - UTC start/end and step in hours (default is a 24 h window, so set 7 days for a "week planner")
  - a mission template with 10 presets: Blue Ghost, VIPER, Artemis III stay, DTE priority, long-night survival, and others (`lunar_eval/planner_templates.py`)
  - thresholds: max night, max no-Earth, min continuous lit, Sun/Earth lit %, shadow bridge
  - toggles: require-both, Layer-B hazards, local search
- Outputs:
  - a **polar sky chart**: the filled terrain horizon silhouette, with Sun and Earth tracks
  - an hourly **case strip**: Sun / Earth / Both / Neither
  - **Score**: fail-closed. If a planner minimum is violated it shows "0.000 (infeasible)" (index.html:574-576)
  - series metrics: longest night, longest no-Earth, longest lit, any Sun∧Earth
- **Local search (time slide)**: a leaderboard with Δh and km offsets, plus a filter for hazard-gap (*) rows.
- **Deep search**: a lat/lon rectangle snapped to a 1 km cap, with modes optimized or total_coverage. It shows a leaderboard (lat, lon, start, feasible, score, companion) and a CSV export. It is labelled "provisional".
- **Provenance**:
  - a one-liner ("mask: computed/cached" vs "mask: mocked", the formula, the schedule version)
  - expandable details (decision IDs, sigmas, dust label with the Metzger β)
  - a header tag reading "Mock" plus a NASA non-affiliation footer

**First-person view (`web/firstperson.html/js`)**
- Opens with the same site and time as the planner.
- Eye-level look-around 2 m above the site, on Cesium Moon terrain (about 5 m terrain and about 1 m NAC imagery near the pole, VB:100).
- Sun and Earth markers and the horizon line come from the project's own geometry. An hour slider scrubs through the window.
- Provenance is explicit: "Backdrop: Cesium Moon — not our model."
- With no ion token, or if Cesium fails, it falls back to a **2D mask panorama** on canvas (the silhouette with Sun and Earth dots).

**Desktop (`desktop/`)**
- A Tauri + React + Blueprint dark shell. So far it is only a navbar and a callout ("Evaluator compute stays on this machine; remote role is horizon masks only").
- Present it as the product direction, **not** as a demoed feature.

**Honesty points for the talk** (docs/demo-data-and-masks.md)
- About 290k masks at 1 km spacing were actually computed offline (~839 MB).
- The curves on Pages are **mocked**.
- A 100 m cap and a mask API are planned, not done.

**90-second demo path**
1. (10s) Planner opens on PGDA Site01. Point at the "Mock" tag and the provenance line: "we say what is real."
2. (20s) Pick "VIPER (conservative / 70 h)", set a 7-day window, run. Read the sky chart: the terrain silhouette, the Sun skimming the rim, the Earth track. Then the case strip and the score.
3. (15s) Switch the template to "Direct-to-Earth priority" (max no-Earth 8 h) and run. The score flips to infeasible: same site and date, different mission, different answer.
4. (15s) Turn on local search. The leaderboard shows a slip of a few hours or a few hundred metres that restores feasibility. That is the "schedule slipped" use case (CS:19).
5. (15s) Run deep search on the default rectangle. Show the ranked site×time leaderboard and the CSV export.
6. (15s) Click First-person view. Stand 2 m above the pick, scrub the hour, and watch the Sun graze the crater rim. Point at "Backdrop: not our model". If there is no token, show the 2D panorama.

## 3. Hook and one-liner

- **Hook:** "At the lunar south pole, moving your landing a few hundred metres or slipping it a few hours can be the difference between a lander that has power and talks to Earth and one that freezes in silence. Today, checking that means juggling expert tools built on 18-year averages."
- **One-liner:** "Pick a site, a time window and your mission's limits, and it shows the local horizon with Sun and Earth over every hour, tells you yes or no on power and direct-to-Earth comms with a score, and searches nearby places and times for a better option, always labelling what is computed and what is mocked."
