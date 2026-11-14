# CLPS site×time evaluator — Implementation Plan (Sat 14 → Sun 15 Nov 2026, buffer to Thu 20)

Window: Sat 2026-11-14 14:30 → Sun 2026-11-15 23:00 (UTC+1) for the full scope; the Space Apps submission closes Sun 23:59 local. Mon 16 → Thu 20 Nov is the buffer for anything the Sunday freeze cuts, and for the long-running 100 m precompute.
People: pj (builder, decider, merger) with parallel agent lanes. Challenger: n/a (solo). Project type: software/git, greenfield (no application code yet).
Cycle position: bet / kick-off.
Approval: **pending pj nod** (approval gate at the end).

Governing records: frame `D-20261114-pj-d7d9`, Sunday target `D-20261114-pj-a3b3` (full scope; cut only at failed checkpoints), scope `D-20261114-pj-9f04`, product question `D-20261111-pj-60ab`, layer B / seams `D-20261114-pj-b8d3`, ephemeris `D-20261114-pj-4ffe`, horizon mask `D-20261114-pj-f369`, hosting `D-20261114-pj-5994`. Resource facts: `docs/resources.md`. This plan replaces the rejected `2026-11-14-hackathon-lite-plan.md`.

## 1. Assumptions

- **(Recommended confirm)** pj has ~8 focused hours left on Saturday (14:30–23:30) and ~12 on Sunday (09:00–21:00), then 21:00–23:00 for the submission. At focus 0.85: ~17 h of pj attention before the freeze.
- **(Recommended confirm)** "Several people" means agent lanes. pj is the only decider and the only merger. Lanes never take own-mode decisions; they stop and ask.
- **(Recommended confirm)** The Space Apps entry is a **video ≤ 30 s or ≤ 7 slides** plus the repo link and, if S11 lands, a public URL.
- **(Safe default)** Stack: Python 3.12, numpy/scipy/rasterio for terrain, FastAPI for the API, one static web page (plain ES modules) with a chart library, a 2D map and, for the first-person view, the library chosen in P11. Advise-mode proposal; pj can swap at the gate.
- **(Safe default)** Chat in Spanish; code, records and docs in English (`docs/records/project.md`).

## 2. Appetite and capacity

- Fixed: Sunday 23:00. Variable: scope, but the target is all of `D-9f04` (`D-a3b3`). No extension: a scope still uphill at its checkpoint follows the cut order and moves to Mon–Thu. [Book ch02, ch07]
- Capacity [Inference]: ~60 h of lane work against ~17 h of pj attention. pj's review and integration (~30% of lane hours) is the binding constraint, so lanes must integrate small, tested slices and pj reviews contracts and outputs, not every line. Sunday 18:00–21:00 is reserved for integration, edge QA and cuts.
- Long-running compute is free capacity: the 1 km cap (~4 h on pj's PC) runs overnight Saturday; the 100 m cap on the CX43 (~26–52 days) starts on Sunday and keeps running after the submission. It is not a Sunday deliverable.

## 3. Outcome, problem, no-gos

**Use case.** A mission planner picks a south-pole site and a time window, sets survival needs (maximum hours without Sun, without Earth, whether both are needed at once, what fraction of the solar disc counts as light, how long a shadow the battery can bridge) and surface limits (temperature, dust). They see when the Sun and Earth clear the real terrain horizon, a score that is zero when the minima fail, the nearest time and nearby sites that meet them, and the best site×time over ranges they choose. (`D-60ab`, `D-9f04`, `D-f369`)

**Must-have outcomes by Sunday (`D-a3b3`):**

1. Real Sun/Earth geometry from local kernels, passing a tolerance test against saved Horizons fixtures (`D-4ffe`).
2. Real horizon masks from LOLA DEMs with the `D-f369` schedule: the demo site refined, the 80–90°S cap at 1 km.
3. An hourly visibility timeline per site: Sun fraction, Earth fraction, four cases, longest night, longest lit period with bridged shadows.
4. A needs-adapted score with explained thresholds and provenance; zero when minima fail (`D-60ab`).
5. Layer-B surface factors (temperature, dust) in the score (`D-9f04`, `D-b8d3`).
6. Local search: nearest feasible time on the site and better neighbouring sites on the grid.
7. Deep search over user time–space ranges (`D-60ab`).
8. Views: horizon chart, region score map, first-person view from the site (`D-9f04` useful viz set).
9. The app served from the CX43 with the 1 km dataset; the 100 m run started (`D-5994`).
10. Validation: tolerance re-check on short-night sites and the PGDA 69 comparison (`D-f369`).
11. The submission pack: ≤ 7 slides or a 30 s video, SI disclosure, V0 claims, portfolio README.

**No-gos:** trajectory optimization and the approach-corridor filter (`D-b8d3`); Mars or a second body pack (seam only); native mobile; QuickMap at runtime; Horizons in the request path or from the browser; DEMs in the browser; any claim beyond V0; NASA logos or branding in any AI-generated material.

## 4. Rabbit holes and spikes

| Unknown | Why risky | Resolution | Owner | Timebox |
|---|---|---|---|---|
| Ephemeris library, kernel set and lunar frame (agenda item 5) | Frame or aberration mismatch gives plausible wrong angles near a 1° Sun | **Spike K**: SpiceyPy with the current NAIF DE440 lunar orientation (PA) and frame kernels and the DE440 planetary ephemeris; compare to saved Horizons fixtures at 3 PGDA 78 sites × 2 months. pj decides library and kernels on the result. Fallback (`D-4ffe`): cached Horizons tables for the demo site through the same provider. | Lane Sky | 2 h (Sat 14:30–16:30) |
| DE421 (LOLA) vs DE440 (kernels) frames | Site coordinates shift by tens of metres | Patch: convert once with the frame kernel; residual in provenance | Lane Sky | inside Spike K |
| Large DEMs on a 7 GB machine | 10 m and 20 m mosaics do not fit in RAM | Patch: tiled windowed reads with a 5 km halo for the fine bands; 80 m and 240 m grids in RAM | Lane Terrain | — |
| DEM downloads (~15 GB at ~1–2 MB/s) | ~2–3 h | Start now in the background; the 240 m and 80 m grids and 4 site DEMs are already local | Lane Ops | start 14:30 |
| Score formula and success X/Y/Z (`D-60ab`, `D-9f04`) | Score, both searches and the map consume it | **pj session** (own) Sat 15:00–16:00 → locks P4 | pj | 60 min |
| Layer-B models (temperature, dust) | No public time series predicts temperature at an arbitrary hour (`docs/resources.md`) | **pj session** (own) Sat 17:00–17:45 on the options in the resource brief (Diviner climatology, slope/roughness/PSR proxies) → locks P13; lane builds against `SurfaceHazardProvider` | pj, then Lane Hazards | 45 min |
| Deep search cost | Global search over sites × hours can explode | Patch: search over the precomputed 1 km grid with vectorized visibility per site; coarse-to-fine in time; stopping rules stated in the UI | Lane Search | — |
| First-person view (agenda item 6) | Viewer choice, licence (Cesium Moon free plan is non-commercial and excludes funded research) | **Advise call** Sat 17:45 (P11); build from our own DEM tiles if the ion plan does not fit | pj, then Lane Viz-3D | 15 min |
| Error near short nights (~50 h) | Tolerance tested only on long nights | Re-run on the demo site and short-night PGDA 78 sites | Lane Terrain | 1 h, Sunday |

## 5. Decision log

Planning round: ran inside this document (solo; complexity gate fired on unclear contracts and novel geometry). Decider: pj. [Inference]

| # | Decision | Class | Locked by | Constrains |
|---|---|---|---|---|
| P1 | **Ephemeris contract** `EphemerisProvider.sky(site, times) → {time_utc, sun_az_deg, sun_el_deg, sun_radius_deg, earth_az_deg, earth_el_deg, earth_radius_deg}`; azimuth from north through east; elevation above the smooth horizon | Team-lock | pj (gate) | Sky, Engine, Search, Viz |
| P2 | **Mask contract** `HorizonProvider.mask(site) → float32[720]` (0.5° from north through east) + `{x_m, y_m, lat, lon, h0_m, observer_height_m, schedule_version, dem_ids}`; store = memory-mapped `.npy` per 100 km tile + parquet index | Team-lock | pj (gate) | Terrain, Engine, Search, Viz |
| P3 | **Visibility series** per hour: `sun_fraction`, `earth_fraction` in [0, 1]; flags from the user's fraction thresholds; longest night; longest lit period with bridged shadows (`D-f369`) | Team-lock | pj (gate) | Engine, Search, Viz |
| P4 | **Score contract** `score(series, hazards, needs) → {score, feasible, breakdown, provenance}`; formula from the pj session | Team-lock, own content | pj (15:00) | Engine, Search, Viz |
| P5 | **Provider seam** (`D-b8d3`): `Body`, `EphemerisProvider`, `HorizonProvider`, `SurfaceHazardProvider`; Moon only | Team-lock | pj (gate) | all engine code |
| P6 | **Stack**: package `lunar_eval`, FastAPI, static web page; `pyproject.toml` owned by Ops | Team-lock (advise) | pj (gate) | all lanes |
| P7 | **Fixtures and data**: Horizons tables under `tests/fixtures/horizons/` (fetched once, app User-Agent); DEMs and masks in `data/` (ignored), never in git | Team-lock | pj (gate) | Sky, Terrain, Ops |
| P8 | **Sunday target** = full scope, fallback cut order §12 | own | pj — `D-20261114-pj-a3b3` | everything |
| P9 | **Demo site** and its refinement | own (`D-f369` deferred value) | pj, Sat ~20:00 | Terrain, slides |
| P10 | **Basemap** (agenda item 7): Moon Trek south-polar WMTS backdrop or none | advise | pj, Sat 17:45 | Viz |
| P11 | **First-person viewer** (agenda item 6) | advise | pj, Sat 17:45 | Viz-3D |
| P12 | **PGDA 69 role** (agenda item 4) | own | pj, Sunday after S15 | claims, Viz |
| P13 | **Layer-B models** (temperature, dust) | own | pj, Sat 17:00 | Hazards, Engine |
| P14 | **Deep-search ranges and stopping rules** | own (method) | pj, Sat 23:00 | Search |

## 6. Scopes (all must-have by Sunday; cut order in §12)

Hours are lane hours; pj review is ~30% on top.

| ID | Scope | Lane | Hours | Confidence | Critical path | Reads / writes | Depends on | Done looks like |
|---|---|---|---|---|---|---|---|---|
| S1 | Sky at a site | Sky | 3 | partial | yes | `lunar_eval/ephemeris/`, tests, fixtures | P1, P7, Spike K | Hourly Sun/Earth az/el for any site; Horizons fixture test passes at pj's tolerance |
| S2 | Horizon masks + 1 km cap | Terrain | 4 + overnight | partial | yes | `lunar_eval/horizon/`, `scripts/precompute.py`, tests | P2, downloads | `D-f369` schedule; 28-point tolerance test ≤ 5 h; cap stored |
| S3 | Visibility timeline | Engine | 2 | known | yes | `lunar_eval/visibility.py`, tests | P1–P3 | Fractions, four cases, longest night, bridged lit periods; matches the prototype numbers |
| S4 | Needs-adapted score | Engine | 3 | partial | yes | `lunar_eval/score.py`, tests | P4, S3 | pj's hand scenarios pass; infeasible → 0 naming the failing minimum |
| S5 | Layer-B surface factors | Hazards | 6 | unknown | yes (Sunday) | `lunar_eval/hazards/` | P5, P13 | Temperature and dust terms per site×time with provenance, consumed by the score |
| S6 | Local search | Search | 3 | unknown | no | `lunar_eval/search/local.py` | S4 | Nearest feasible time; better neighbours within ±N km; or an honest "none" |
| S7 | Deep search over ranges | Search | 6 | unknown | no | `lunar_eval/search/deep.py` | S6, P14 | Best site×time over user ranges with the stated stopping rule and its runtime |
| S8 | Horizon chart | Viz | 3 | partial | yes | `web/horizon.*`, `api/routes/site.py` | P1–P3 (mock first) | Mask silhouette, Sun and Earth tracks, case strip, thresholds |
| S9 | Region score map | Viz | 4 | partial | no | `web/map.*`, `api/routes/region.py` | S2 cap, S4 | Score heatmap over 80–90°S at 1 km; click a cell → chart; deep-search result highlighted |
| S10 | First-person view | Viz-3D | 4 | partial | no | `web/firstperson.*` | P11, S1, S2 | Terrain from the site with the Sun and Earth placed from our geometry at the chosen hour |
| S11 | Server and 100 m run | Ops | 3 | known | no | `deploy/`, `scripts/precompute.py` | S2, `D-5994` | CX43 benchmarked for an hour; app over HTTPS with the 1 km dataset; 100 m run started with resume |
| S12 | Validation | Terrain | 3 | partial | no | `tests/`, `docs/validation.md` | S2, S3 | Short-night tolerance re-check; PGDA 69 comparison at PGDA 78 sites; results recorded (informs P12) |
| S13 | `~` Far-field sharing experiment | Terrain | 3 | unknown | no | `scripts/` | S2 | Error and speed-up of reusing 5–250 km rays between neighbours |
| S14 | Claims, provenance, README | pj | 2 | known | last | footer, `README.md` | all | Every number names ephemeris, kernels, DEMs, schedule version, hazard models, V0 limit |
| S15 | Submission pack | pj | 2.5 | known | last | `docs/submission/` | S8–S14 | ≤ 7 slides or 30 s video, SI disclosure, repo link (+ URL); submitted by 23:00 |

## 7. Dependencies and critical path

| Pair | Class | Handling |
|---|---|---|
| S1 / S2 vs S3 | contract-coupled | P1–P3 locked at the gate; S3 builds on synthetic sky and a stub mask from hour 0 |
| S3 → S4 → S6 → S7 | strictly sequential | S4 tests on synthetic series; S6 starts when S4 is green; S7 when S6 is green and P14 is set |
| S5 vs S4 | contract-coupled | P4 includes the `hazards` argument; S4 ships with a neutral hazard term until S5 lands |
| S8 / S9 / S10 vs engine | contract-coupled | Mocks in P1–P4 shape; swap at checkpoints |
| S9 vs S2 cap | sequential | Synthetic grid until the overnight cap lands |
| S11 vs S2 | sequential | Server receives the cap Sunday morning |
| `pyproject.toml`, `api/app.py` routes | hotspot | Ops owns `pyproject.toml`; Viz owns the route list; others add entries in small merges |

**Critical path:** gate nod → Spike K + S2 port → S3 on real data (Sat 18:00) → S4 with pj's formula (Sat 22:00) → S5 hazards in the score (Sun 13:00) → S9 map on the cap with S7 results (Sun 17:00) → S14 → S15. Calendar floor ≈ 15 h of clock time if Spike K passes — inside the window, with little slack.

## 8. Phases and timeline

**Phase 0 — Sat 14:30–18:00, parallel. Exit: one site end-to-end on real data; P1–P7 honoured; P4, P10, P11, P13 decided.**

- Ops: all DEM downloads; repo skeleton (`pyproject.toml`, `lunar_eval/`, `api/`, `web/`, `tests/`, `.gitignore` for `data/`), CI with `pytest`; order the CX43.
- Sky: Spike K, then S1.
- Terrain: port `/tmp/masktest.py`, `/tmp/restest2.py`, `/tmp/illum*.py` into `lunar_eval/horizon/` with the tolerance test; tiled reader.
- Engine: S3 on synthetic inputs.
- Viz: S8 on a mock.
- pj: 15:00–16:00 score session (P4); 16:30 ephemeris library from Spike K; 17:00–17:45 layer-B session (P13); 17:45 basemap and viewer calls (P10, P11).

**Phase 1 — Sat 18:00–23:30. Exit: score on one site with a neutral hazard term; local search running; 1 km cap computing.**

- Engine: S3 on real data, then S4.
- Hazards: S5 against P13.
- Search: S6 once S4 is green.
- Terrain: 1 km cap at ~20:00 (overnight); refined demo neighbourhood once pj picks the site (P9).
- Viz: S8 on real data; S9 on a synthetic grid. Viz-3D: S10 scaffold on the chosen viewer.
- pj: demo site (~20:00); hand scenarios for S4; 23:00 deep-search ranges and stopping rules (P14).

**Phase 2 — Sun 09:00–18:00. Exit: every scope integrated or cut by the checkpoint rules.**

- Ops: S11 server with the cap; start the 100 m run.
- Search: S7 on the cap.
- Hazards: S5 into the score by 13:00.
- Viz: S9 on the cap with S7 results; Viz-3D: S10 on real geometry.
- Terrain: S12 validation; `~` S13.
- pj: P12 after S12; S14 claims and README.

**Final window — Sun 18:00–21:00.** Edge QA only: empty range, all-dark site, PSR cell, threshold 0, fraction 100%, bridging 0 h, site at 80°S, deep search with a one-cell range. Apply the cut order to anything still uphill. Freeze copy. No new scope.

**Submission — Sun 21:00–23:00.** S15: slides or video, SI disclosure, NASA-branding check, repo link and URL; submit by 23:00.

**Mon 16 → Thu 20 (buffer).** Finish whatever the freeze cut, in the reverse of the cut order; watch the 100 m run; close the task records.

## 9. Assignments (draft)

| Person / lane | Owned scopes | Load (lane hours) | Buddy | First independent slice |
|---|---|---|---|---|
| pj | P4, P9–P14 decisions, S14, S15, reviews, merges | ~7 h own work + ~10 h review | — | Score session at 15:00 |
| Sky | Spike K, S1 | 5 h | pj (decides library) | Horizons fixtures + SpiceyPy az/el for one site |
| Terrain | S2, S12, `~` S13 | 7 h + overnight compute | — | Ported mask passing the 28-point test |
| Engine | S3, S4 | 5 h | pj (scenarios) | `visibility.py` on synthetic inputs |
| Hazards | S5 | 6 h | pj (models) | `SurfaceHazardProvider` with a constant model behind P4 |
| Search | S6, S7 | 9 h | Engine (consult) | Nearest feasible hour on a failing synthetic series |
| Viz | S8, S9 | 7 h | — | Horizon chart on the mock |
| Viz-3D | S10 | 4 h | Viz (consult) | Viewer scaffold showing a DEM tile |
| Ops | skeleton, downloads, S11 | 4.5 h | — | `pyproject.toml` + CI + downloads |

Imbalance check: Search carries the most uncertain work (S7); it is first in the cut order after `~`. pj's review load (~10 h) is the real constraint — lanes merge one tested slice at a time and pj reviews contracts and outputs.

## 10. Ownership and collision rules

| Area | Owner | Others may |
|---|---|---|
| `lunar_eval/ephemeris/` | Sky | import |
| `lunar_eval/horizon/`, `scripts/precompute.py` | Terrain | import |
| `lunar_eval/visibility.py`, `score.py` | Engine | import |
| `lunar_eval/hazards/` | Hazards | import |
| `lunar_eval/search/` | Search | — |
| `api/`, route list, `web/` (except `firstperson.*`) | Viz | Engine adds fields only through P1–P4 |
| `web/firstperson.*` | Viz-3D | — |
| `pyproject.toml`, CI, `.gitignore`, `deploy/` | Ops | request changes in one small merge |
| `tests/fixtures/` | Sky (Horizons), Terrain (reference masks) | read |
| `README.md`, claims, `docs/submission/` | pj | — |
| `docs/records/` | pj (decision-flow) | lanes never edit records |

Branches: trunk-based; `scope/<id>-<name>`, under a day; merge when the slice runs; `main` always runs the demo. DEMs, masks and tokens never in git. [Inference]

## 11. Checkpoints

| When | Check | Pass | If failing |
|---|---|---|---|
| Sat 16:30 | Spike K | Kernel az/el within tolerance of Horizons | Cached Horizons tables for the demo site (`D-4ffe` fallback); record why |
| Sat 18:00 | Phase 0 exit | One site end-to-end on real data; P4, P13 decided | Keep mocks in the views; S9 and S10 wait |
| Sat 23:30 | Phase 1 exit | Score + local search on one site; cap computing; P14 set | S7 drops to cut item 2 |
| Sun 13:00 | Midpoint | S5 in the score; S7 and S10 over the hill | Apply cut items 1–3 for whatever is uphill |
| Sun 18:00 | Freeze | Everything integrated | Cut in the order below; cut items go to Mon–Thu |
| Sun 23:00 | Submit | Pack submitted | Submit the integrated slice as is |

Hill: Spike K, S2, S5, S7 and S10 start uphill. Sync is exception-driven: say so when a scope crosses the hill, blocks another lane, or threatens a P-lock.

## 12. Cut order (only at failed checkpoints or the freeze; `D-a3b3`)

1. `~` S13 far-field experiment.
2. S7 deep search → a fixed range over the demo region with a brute-force grid.
3. S10 first-person view → a static panorama rendered from the mask.
4. S11 public URL → local demo in the video; 100 m run starts Monday.
5. S5 layer B → temperature only, then a stated "not modelled" with the seam in place.
6. S9 region map → a list of PGDA 78 sites with scores.
7. S6 neighbours on the grid → nearest feasible time only.
8. Do not cut: kernels + mask + timeline, the score with its rule shown, the horizon chart, provenance, SI disclosure.

## 13. Risks

- Review load: ~60 lane hours against ~17 h of pj attention → slices stay small; pj reviews contracts and test outputs; the freeze is not moved.
- The score or layer-B sessions run long → each is time-boxed; unresolved parts become explicit deferred values with a working default pj approves.
- PGDA downloads are slow or fail → the 240 m and 80 m grids and four 5 m site DEMs are already local.
- Frame mismatch (DE421 LOLA vs DE440 kernels) → patched in Spike K; residuals in provenance.
- Cesium ion free plan excludes funded research and commercial use (`docs/resources.md`) → P11 decides with that in view.
- The 100 m run outlasts the window → not a deliverable; S13 may shorten it later.
- Space Apps rules: SI disclosure; no NASA branding in AI-generated media; awards not sought (`D-d7d9`).
- `docs/records/project.md` still lists rules & eligibility as `out` and no hackathon milestone; `D-d7d9` requires that edit on the default branch or in its own PR.

## 14. Book vs inference

- **[Book]** Fixed time, variable scope; circuit breaker; vertical scopes with one owner; get one piece done (one site end-to-end first); unknowns first; `~` cut first; hill, not status theatre; QA for the edges in the final window.
- **[Inference]** Agent lanes as the N-person split; hour-level capacity with pj attention as the constraint; full-scope target with a pre-agreed fallback cut (`D-a3b3`); trunk-based branches; file ownership as the collision map; long-running compute treated as free capacity.

### Approval gate

| Person / lane | Owned scopes | Load | First independent slice | OK? |
|---|---|---|---|---|
| pj | decisions, S14, S15 | ~17 h | score session 15:00 | pending |
| Sky | Spike K, S1 | 5 h | fixtures + SpiceyPy az/el | pending |
| Terrain | S2, S12, `~` S13 | 7 h | ported mask passes the 28-point test | pending |
| Engine | S3, S4 | 5 h | visibility on synthetic inputs | pending |
| Hazards | S5 | 6 h | constant hazard provider behind P4 | pending |
| Search | S6, S7 | 9 h | nearest feasible hour | pending |
| Viz | S8, S9 | 7 h | horizon chart on mock | pending |
| Viz-3D | S10 | 4 h | viewer scaffold | pending |
| Ops | skeleton, downloads, S11 | 4.5 h | `pyproject.toml` + CI + downloads | pending |

Decider sign-off: pending (pj).
