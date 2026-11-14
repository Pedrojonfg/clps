# CLPS site×time evaluator — Implementation Plan (Sat 14 → Thu 20 Nov 2026)

Window: Sat 2026-11-14 14:30 → Thu 2026-11-20 (UTC+1), in two cycles. Cycle 1 ends at the Space Apps submission (Sun 15 Nov, 23:59 local; target 23:00). Cycle 2 runs Mon 16 → Thu 20 Nov.
People: pj (builder, decider, merger) with parallel agent lanes. Challenger: n/a (solo). Project type: software/git, greenfield (no application code yet).
Cycle position: bet / kick-off.
Approval: **pending pj nod** (approval gate at the end).

Governing records: frame `D-20261114-pj-d7d9` (portfolio scope through 20 Nov, a defined cut submitted on 15 Nov), scope `D-20261114-pj-9f04`, product question `D-20261111-pj-60ab`, layer B / seams `D-20261114-pj-b8d3`, ephemeris `D-20261114-pj-4ffe`, horizon mask `D-20261114-pj-f369`, hosting `D-20261114-pj-5994`. Resource facts: `docs/resources.md`. This plan replaces the rejected `2026-11-14-hackathon-lite-plan.md`.

## 1. Assumptions

- **(Recommended confirm)** pj has ~8 focused hours left on Saturday (14:30–23:30) and ~12 on Sunday (09:00–21:00), then 21:00–23:00 for the submission. At focus 0.85: ~17 h of pj attention before the freeze. Cycle 2 availability is unknown; assumed ~5 h/day (Mon–Thu, ~20 h).
- **(Recommended confirm)** "Several people" means agent lanes. pj is the only decider and the only merger. Lanes never take own-mode decisions; they stop and ask.
- **(Recommended confirm)** The Space Apps entry is a **video ≤ 30 s or ≤ 7 slides** plus the repo link. A public URL is nice to have, not a must.
- **(Safe default)** Stack: Python 3.12, numpy/scipy/rasterio for terrain, FastAPI for the API, one static web page (TypeScript-free, plain ES modules) with a chart library and a 2D map. Advise-mode proposal; pj can swap at the gate.
- **(Safe default)** Chat in Spanish; code, records and docs in English (`docs/records/project.md`).

## 2. Appetite and capacity

- Fixed: Sunday 23:00 for the cut; Thursday 20 Nov for the portfolio. Variable: scope. No extension of either date (circuit breaker): if a must-have is still uphill at a checkpoint, it moves to Cycle 2 or is cut. [Book ch02, ch07]
- Capacity [Inference]: pj attention is the bottleneck, not typing. Lanes run in parallel; each scope still costs pj review and integration time (~30% of the lane hours). Cycle 1: ~17 h pj attention, of which the last ~3 h (Sun 18:00–21:00) are reserved for integration, edge QA and cuts.
- Long-running compute is free capacity: the demo precompute (1 km over 80–90°S, ~4 h on pj's PC) runs overnight Saturday; the 100 m cap on the CX43 (~26–52 days) starts in Cycle 2 and finishes after the window. Neither blocks a scope.

## 3. Outcome, problem, no-gos

**Use case.** A mission planner picks a south-pole site and a time window, sets survival needs (maximum hours without Sun, without Earth, whether both are needed at once, what fraction of the solar disc counts as light, how long a shadow the battery can bridge). They see when the Sun and Earth clear the real terrain horizon, a score that is zero when the minima fail, the nearest time that meets them, and how nearby sites compare. (`D-60ab`, `D-f369`)

**Must-have outcomes for the Space Apps cut (`hack_submission_cut`, proposed — pj decides at the gate):**

1. Real Sun/Earth geometry from local kernels, passing a tolerance test against saved Horizons fixtures (`D-4ffe`).
2. Real horizon masks from LOLA DEMs with the `D-f369` schedule, for the demo site (refined) and the 80–90°S cap at 1 km.
3. An hourly visibility timeline per site: Sun fraction, Earth fraction, four cases, longest night, longest lit period with bridged shadows.
4. A needs-adapted score with explained thresholds and provenance; zero when minima fail (`D-60ab`).
5. Local search: nearest feasible time on the same site, plus neighbouring sites on the 1 km grid.
6. Two views: a horizon chart (mask with Sun and Earth tracks) and a region map of the score over the precomputed grid.
7. The submission pack: ≤ 7 slides or a 30 s video, SI disclosure, V0 claims.

**Cycle 2 outcomes (portfolio, by Thu 20 Nov):** deep search over time–space ranges (`D-60ab`); layer-B surface factors (temperature, dust) in the score (`D-9f04`, `D-b8d3`); the server running the 100 m precompute and serving the app (`D-5994`); a first-person view if the viewer decision lands; the PGDA 69 comparison as the validation check named in `D-f369`; portfolio README.

**No-gos (whole window):** trajectory optimization and the approach-corridor filter (`D-b8d3`); Mars or a second body pack (seam only); native mobile; QuickMap at runtime; Horizons in the request path or from the browser; DEMs in the browser; any claim beyond V0 (no ops certification); NASA logos or branding in any AI-generated material.

**Scope confirm**

| IN for the Sunday cut | Cycle 2 | OUT |
|---|---|---|
| Kernels + Horizons tolerance test | Deep search over ranges | Trajectories, approach filter |
| Mask engine + demo-site and 1 km cap precompute | Layer B (temperature, dust) | Mars / second body |
| Visibility timeline, bridged lit periods | Server + 100 m precompute | Native mobile |
| Score + local search (time and nearby sites) | `~` First-person view | QuickMap / Horizons at runtime |
| Horizon chart + region score map | PGDA 69 validation, portfolio README | Claims above V0 |
| Submission pack | | |

## 4. Rabbit holes and spikes

| Unknown | Why risky | Resolution | Owner | Timebox |
|---|---|---|---|---|
| Ephemeris library, kernel set and lunar frame (agenda item 5) | Frame or aberration mismatch gives plausible wrong angles near a 1° Sun | **Spike K**: SpiceyPy with the current NAIF DE440 lunar orientation (PA) and frame kernels and the DE440 planetary ephemeris; compare to saved Horizons fixtures at 3 PGDA 78 sites × 2 months. pj decides the library and kernels on the result. Fallback (`D-4ffe`): Horizons tables cached for the demo site through the same provider. | Lane Sky | 2 h (Sat 14:30–16:30) |
| DE421 vs DE440 frames between LOLA (MOON_ME DE421) and kernels | Site coordinates shift by tens of metres between frames | Patch: convert site coordinates once with the frame kernel; document the offset in provenance | Lane Sky | inside Spike K |
| Large DEMs on a 7 GB machine | 10 m and 20 m mosaics do not fit in RAM | Patch: tiled windowed reads; masks computed tile by tile with a halo of 5 km for the fine bands; 240 m and 80 m grids fully in RAM | Lane Terrain | — |
| DEM downloads (5 m 3.3 GB, 10 m 4.8 GB, 20 m 2.6 GB, 40 m, 80 m, 120 m, 240 m) | ~1–2 MB/s from PGDA; ~2 h total | Start now in the background; no scope waits on them before 18:00 | Lane Ops | start 14:30 |
| Score formula and success X/Y/Z are deferred (`D-60ab`, `D-9f04`) | Score, search and map all consume it | **pj decision session** (own, method & validation) Sat 15:00–16:00; locks contract C4 | pj | 60 min |
| Error near short nights (~50 h) not measured (`D-f369`, checks) | The 5 h tolerance was tested only on long nights | Re-run the tolerance test on the demo site and on PGDA 78 sites with short nights | Lane Terrain | 1 h, Sunday |
| Region map projection | Polar stereographic in a web map | Patch: draw the score grid as a canvas image in polar stereographic metres, with a Moon Trek south-polar layer as `~` backdrop (basemap decision, advise) | Lane Viz | — |

## 5. Decision log

Planning round: ran inside this document (solo; complexity gate fired on unclear contracts and novel geometry). Decider: pj. [Inference]

| # | Decision | Class | Locked by | Constrains |
|---|---|---|---|---|
| P1 | **Ephemeris contract** `EphemerisProvider.sky(site, times) → {time_utc, sun_az_deg, sun_el_deg, sun_radius_deg, earth_az_deg, earth_el_deg, earth_radius_deg}`; azimuth from north through east, elevation above the smooth horizon at the site | Team-lock | pj (gate) | Sky, Visibility, Score |
| P2 | **Mask contract** `HorizonProvider.mask(site) → float32[720]` (0.5° from north through east) + metadata `{x_m, y_m, lat, lon, h0_m, observer_height_m, schedule_version, dem_ids}`; store = memory-mapped `.npy` per 100 km tile + a parquet index | Team-lock | pj (gate) | Terrain, Visibility, Map, Search |
| P3 | **Visibility series** per hour: `sun_fraction`, `earth_fraction` in [0, 1] from disc vs mask; lit / radio flags derived with the user's fraction thresholds; longest night, longest lit period with bridged shadows (`D-f369`) | Team-lock | pj (gate) | Visibility, Score, Charts |
| P4 | **Score contract** `score(series, needs) → {score, feasible, breakdown, provenance}`; formula from the pj session | Team-lock, own content | pj (15:00 session) | Score, Search, Map |
| P5 | **Provider seam** (`D-b8d3`): `Body`, `EphemerisProvider`, `HorizonProvider`, `SurfaceHazardProvider`; Moon only | Team-lock | pj (gate) | all engine code |
| P6 | **Stack**: Python package `lunar_eval`, FastAPI, static web page; one `pyproject.toml` owned by lane Ops | Team-lock (advise) | pj (gate) | all lanes |
| P7 | **Fixtures**: Horizons tables saved once with an app User-Agent under `tests/fixtures/horizons/`; DEMs never in git (`data/` in `.gitignore`) | Team-lock | pj (gate) | Sky, Terrain, Ops |
| P8 | **Hack cut** = the seven must-have outcomes in §3 | own, pj decides | pj (gate) | everything before Sunday |
| P9 | **Demo site** and its refinement (spacing, resolution) | own (`D-f369` deferred value) | pj, Sat ~20:00 | Terrain precompute, slides |
| P10 | **Basemap** (agenda item 7): Moon Trek south-polar WMTS as a `~` backdrop, or none | advise | pj, Sunday | Viz |
| P11 | **First-person viewer** (agenda item 6) | advise | pj, Cycle 2 | Viz |
| P12 | **PGDA 69 role** (agenda item 4) | own | pj, after the validation check | claims, Viz |
| P13 | **Layer-B models** (temperature, dust) | own | pj, Mon 16 | Score v2 |

## 6. Scopes

Cycle 1 (Sunday cut). Hours are lane hours; pj review is ~30% on top.

| ID | Scope | Lane | Hours | Confidence | Critical path | Reads / writes | Depends on | Must / ~ | Done looks like |
|---|---|---|---|---|---|---|---|---|---|
| S1 | Sky at a site | Sky | 3 | partial | yes | `lunar_eval/ephemeris/`, `tests/test_ephemeris.py`, fixtures | P1, P7, Spike K | must | Hourly Sun/Earth az/el for any site; Horizons fixture test passes at the tolerance pj sets |
| S2 | Horizon masks | Terrain | 4 | partial | yes | `lunar_eval/horizon/`, `scripts/precompute.py`, `tests/test_horizon.py` | P2, downloads | must | `D-f369` schedule; tolerance test (schedule vs 5 m/80 m reference, 28 points, 2027) passes ≤ 5 h; demo cap at 1 km stored |
| S3 | Visibility timeline | Engine | 2 | known | yes | `lunar_eval/visibility.py`, tests | P1–P3, S1, S2 | must | For a site and range: fractions, four cases, longest night, bridged lit periods; matches the /tmp prototype numbers |
| S4 | Needs-adapted score | Engine | 3 | partial | yes | `lunar_eval/score.py`, tests | P4, S3 | must | pj's hand scenarios pass; infeasible → 0 with the failing minimum named |
| S5 | Local search | Search | 3 | unknown | no | `lunar_eval/search.py` (imports `score`) | S4 | must (hammer first) | From an infeasible start: nearest feasible time on the site, best neighbours within ±N km on the grid, or an honest "none" |
| S6 | Horizon chart | Viz | 3 | partial | yes | `web/horizon.*`, `api/routes/site.py` | P1–P3 (mock first) | must | Mask silhouette, Sun and Earth tracks for the range, case strip, thresholds shown |
| S7 | Region score map | Viz | 4 | partial | no | `web/map.*`, `api/routes/region.py` | S2 cap, S4 | must (hammer to a site list) | Score heatmap over 80–90°S at 1 km; click a cell → horizon chart |
| S8 | Claims and provenance | pj | 1.5 | known | last | footer, `README.md` demo section | all | must | Every number names ephemeris, kernels, DEMs, schedule version, V0 limit |
| S9 | Submission pack | pj | 2.5 | known | last | `docs/submission/` | S6–S8 | must | ≤ 7 slides or 30 s video, SI disclosure, repo link; submitted by 23:00 |
| S10 | `~` Short-night tolerance re-check | Terrain | 1 | known | no | tests | S2 | ~ | Error on sites with nights near 50 h reported |
| S11 | `~` Public URL on the CX43 | Ops | 1.5 | known | no | deploy scripts | S6, `D-5994` | ~ | App reachable over HTTPS with the 1 km dataset |

Cycle 2 (Mon 16 → Thu 20):

| ID | Scope | Lane | Hours | Confidence | Must / ~ | Done looks like |
|---|---|---|---|---|---|---|
| S12 | Server + 100 m precompute | Ops | 3 | known | must | CX43 benchmarked for an hour; 100 m run started with resume support; app served |
| S13 | Deep search over ranges | Search | 6 | unknown | must | Global best over user time–space ranges with stated stopping rules (`D-60ab`) |
| S14 | Layer-B surface factors | Engine | 8 | unknown | must | Temperature and dust terms from the pj model decisions in the score, with provenance |
| S15 | Validation vs PGDA 69 | Terrain | 2 | partial | must | Average illumination at PGDA 78 sites vs published averages; result recorded; informs P12 |
| S16 | Far-field sharing experiment | Terrain | 3 | unknown | ~ | Error and speed-up of reusing 5–250 km rays between neighbours; may cut the 100 m run to days |
| S17 | `~` First-person view | Viz | 4 | partial | ~ | Terrain view from the site with the Sun and Earth placed from our geometry (after P11) |
| S18 | Portfolio README and demo | pj | 2 | known | must | A stranger runs one command and reads what is computed and its limits |

## 7. Dependencies and critical path

| Pair | Class | Handling |
|---|---|---|
| S1 / S2 vs S3 | contract-coupled | P1–P3 locked at the gate; S3 builds on synthetic sky and a stub mask from hour 0 |
| S3 → S4 → S5 | strictly sequential | S4 tests use synthetic series until S3 lands; S5 starts when S4 tests are green |
| S6 vs S1–S3 | contract-coupled | Mock JSON in P1–P3 shape; swap to real data at the Sat 18:00 checkpoint |
| S7 vs S2 cap | sequential | Map uses a synthetic grid until the overnight precompute lands |
| S2 precompute vs P9 demo site | sequential | Cap at 1 km starts at 20:00 regardless; the refined demo neighbourhood starts when pj picks the site |
| `pyproject.toml`, `api/app.py` route list | hotspot | Ops owns `pyproject.toml`; Viz owns the route list; others add entries through small merges |

**Critical path:** gate nod → Spike K + S2 port (parallel) → S3 on real data (Sat 18:00) → S4 with pj's formula → S6 on real data → S8 → S9. Calendar floor ≈ 11 h of clock time if Spike K passes. The map (S7) and search (S5) sit beside it and are the first to hammer.

## 8. Phases and timeline

**Phase 0 — Sat 14:30–18:00, parallel. Exit: one site end-to-end on real data (kernels sky + mask + timeline on the chart) and P1–P5 honoured.**

- Lane Ops: start all DEM downloads; repo skeleton (`pyproject.toml`, `lunar_eval/`, `api/`, `web/`, `tests/`, `.gitignore` for `data/`), CI running `pytest`.
- Lane Sky: Spike K (2 h), then S1.
- Lane Terrain: port `/tmp/masktest.py`, `/tmp/restest2.py`, `/tmp/illum*.py` into `lunar_eval/horizon/` with the tolerance test; tiled reader.
- Lane Viz: S6 on a mock in P1–P3 shape.
- pj: 15:00–16:00 score decision session (P4, success X/Y/Z); 16:30 decide the ephemeris library from Spike K (agenda item 5); review merges.

**Phase 1 — Sat 18:00–23:30. Exit: score and local search on one site; demo precompute running.**

- Engine: S3 on real data, then S4 with pj's scenarios.
- Search: S5 once S4 is green.
- Terrain: start the 1 km cap precompute at ~20:00 (runs overnight); refined demo neighbourhood once pj picks the site (P9).
- Viz: S6 on real data; start S7 on a synthetic grid.
- pj: choose the demo site (~20:00) with S6 open on candidates; write hand scenarios for S4.

**Phase 2 — Sun 09:00–18:00. Exit: two views on real data, score and search integrated, claims drafted.**

- Viz: S7 on the overnight 1 km cap; click-through to the horizon chart.
- Search: neighbours on the grid; hammer to time-only search if uphill at 14:00.
- Terrain: `~` S10; check the cap for gaps.
- pj: P10 basemap call; S8 claims; outline S9.

**Final window — Sun 18:00–21:00.** Edge QA only: empty range, all-dark site, PSR cell, threshold 0, fraction 100%, bridging 0 h, site at 80°S (DEM coverage edge). Cut remaining `~`. Freeze copy. No new scope.

**Submission — Sun 21:00–23:00.** S9: slides or video, SI disclosure, NASA-branding check, repo link; submit by 23:00 (59 min buffer).

**Cycle 2 — Mon 16 → Thu 20.**

- Mon: pj layer-B model decisions (P13); S12 server and 100 m run; restore any hack shortcuts flagged in the final window.
- Tue–Wed: S13 deep search, S14 layer B, S15 validation; `~` S16.
- Thu: `~` S17 if P11 landed; S18 README; scope freeze at 18:00; close the task records.

## 9. Assignments (draft)

| Person / lane | Owned scopes | Load (must-have lane hours, Cycle 1) | Buddy | First independent slice |
|---|---|---|---|---|
| pj | P4, P8–P10 decisions, S8, S9, reviews, merges | ~6 h own work + ~7 h review | — | Score decision session at 15:00 |
| Sky | Spike K, S1 | 5 h | pj (decides library) | Horizons fixture download + SpiceyPy az/el for one site |
| Terrain | S2, `~` S10 | 4 h + overnight compute | — | Ported mask function passing the 28-point test |
| Engine | S3, S4 | 5 h | pj (scenarios) | `visibility.py` on synthetic sky + stub mask |
| Search | S5 | 3 h, after S4 green | Engine (consult) | Nearest feasible hour on a failing synthetic series |
| Viz | S6, S7 | 7 h | — | Horizon chart on the P1–P3 mock |
| Ops | skeleton, downloads, `~` S11 | 1.5 h | — | `pyproject.toml`, CI, background downloads |

Imbalance check: Viz is the heaviest lane; S7 is the first to hammer (to a list of PGDA 78 sites with scores) if it is uphill at Sunday 14:00. pj's review load is the real constraint; lanes integrate one scope at a time.

## 10. Ownership and collision rules

| Area | Owner | Others may |
|---|---|---|
| `lunar_eval/ephemeris/` | Sky | import |
| `lunar_eval/horizon/`, `scripts/precompute.py` | Terrain | import |
| `lunar_eval/visibility.py`, `score.py` | Engine | import |
| `lunar_eval/search.py` | Search | — |
| `api/`, route list, `web/` | Viz | Engine adds fields only through P1–P4 |
| `pyproject.toml`, CI, `.gitignore`, deploy | Ops | request changes in one small merge |
| `tests/fixtures/` | Sky (Horizons), Terrain (reference masks) | read |
| `README.md`, claims, `docs/submission/` | pj | — |
| `docs/records/` | pj (decision-flow) | lanes never edit records |

Branches: trunk-based; `scope/<id>-<name>`, under a day; merge when the slice runs; `main` always runs the demo. DEMs and precomputed masks live in `data/` (ignored) and on the server, never in git. [Inference]

## 11. Checkpoints

| When | Check | Pass | If failing |
|---|---|---|---|
| Sat 16:30 | Spike K | Kernel az/el within tolerance of Horizons fixtures | Horizons cached tables for the demo site via the provider (`D-4ffe` fallback); record why |
| Sat 18:00 | Phase 0 exit | One site end-to-end on real data | Keep the mock in the chart; do not start S7 until it passes |
| Sat 23:30 | Phase 1 exit | Score + nearest feasible time on one site; 1 km precompute running | Search becomes time-only; precompute starts from a smaller box around the demo site |
| Sun 14:00 | Midpoint | S5 and S7 over the hill | S7 → site list; S5 → time-only |
| Sun 18:00 | Freeze | Musts integrated | Cut in the order below |
| Sun 23:00 | Submit | Pack submitted | Submit the integrated slice as is |
| Thu 20, 18:00 | Portfolio freeze | Cycle 2 musts integrated | Cut `~`, then S16, then trim S14 to one factor |

Hill: Spike K, S2 and S5 start uphill. S5 is the scope allowed to die uphill in Cycle 1. Sync is exception-driven: say so when a scope crosses the hill, blocks another lane, or threatens a P-lock.

## 12. Cut order (Cycle 1)

1. `~` S11 public URL, `~` S10 short-night re-check.
2. S7 region map → a list of PGDA 78 sites with scores.
3. S5 neighbours on the grid → nearest feasible time only.
4. Refined demo neighbourhood → demo site at the 1 km grid point.
5. Do not cut: kernels + mask + timeline, the score with its rule shown, the horizon chart, provenance, SI disclosure.

## 13. Risks

- The score session (P4) runs long and stalls S4–S7 → time-box at 60 min; unresolved parts become explicit deferred values with a working default pj approves.
- PGDA downloads are slow or fail → the 240 m and 80 m files are already on pj's machine (`/tmp`); the cap can run on those plus the 5 m site DEMs for the demo.
- Frame mismatch (DE421 LOLA vs DE440 kernels) → patched in Spike K; residuals reported in provenance.
- The 100 m run outlasts the window (26–52 days) → it is not a Cycle 2 deliverable; S16 may shorten it.
- Space Apps rules: SI disclosure and no NASA branding in AI-generated media; pj is not seeking awards (`D-d7d9`).
- `docs/records/project.md` still lists rules & eligibility as `out` and no hackathon milestone; `D-d7d9` requires that edit on the default branch or in its own PR.

## 14. Book vs inference

- **[Book]** Fixed time, variable scope; circuit breaker; vertical scopes with one owner; get one piece done (one site end-to-end first); unknowns first; `~` cut first; hill, not status theatre; QA for the edges in the final window.
- **[Inference]** Agent lanes as the N-person split; hour-level capacity with pj attention as the constraint; two cycles inside one week; trunk-based branches; file ownership as the collision map; long-running compute treated as free capacity.

### Approval gate

| Person / lane | Owned scopes | Load | First independent slice | OK? |
|---|---|---|---|---|
| pj | decisions P4, P8–P10, S8, S9 | ~13 h | score session 15:00 | pending |
| Sky | Spike K, S1 | 5 h | fixtures + SpiceyPy az/el | pending |
| Terrain | S2, `~` S10 | 4 h | ported mask passes the 28-point test | pending |
| Engine | S3, S4 | 5 h | visibility on synthetic inputs | pending |
| Search | S5 | 3 h | nearest feasible hour | pending |
| Viz | S6, S7 | 7 h | horizon chart on mock | pending |
| Ops | skeleton, downloads, `~` S11 | 1.5 h | `pyproject.toml` + CI + downloads | pending |

Decider sign-off: pending (pj). P8 (`hack_submission_cut`) is recorded as a decision once pj approves it.
