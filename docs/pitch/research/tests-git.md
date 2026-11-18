# CLPS: tests and git history (branch scope/s12-s14-s15-validation-claims, 2026-11-15)

## A) Test run
- There is no `.venv`, so I ran `python3 -m pytest -q` with miniforge Python and pytest 9.0.3.
- **Result: 110 collected, 109 passed, 0 failed, 1 skipped.** Total time is about 10.3 s.
- The skip is `test_api_site.py:79` (`test_site_without_mock_and_no_data_returns_503`). The test skips itself when real data is present. Real DEM and SPICE data are installed locally, so every real-data test ran.
- On a clean clone without `data/`, about 12 more tests would skip:
  - the `skipif(not real_data_available())` tests in `test_planner_week`, `test_api_site` (2), `test_search_site01_e2e`, `test_site01_week_aggregates` and `test_dem_site`
  - the ephemeris tests (they need `de440s.bsp` and spiceypy)
- The working tree has uncommitted changes: `api/app.py` +12, `tests/test_api_site.py` +11. The run included them.
- The quiet summary line did not print, so I read the counts from a junit XML file.

Slowest tests: `test_dem_site::test_site01_5m_mask_is_not_flat` 10.2 s, `schedule_mask_plausible` 3.6 s, `sky_mask_series_score_end_to_end` 1.3 s, `search_site01_e2e` 0.96 s, `api real_mask_not_mock_ridge` 0.70 s, `api local_search_flag` 0.59 s, and Horizons az/el cases at about 0.1 s each. Real-DEM tests take more than 90% of the run time.

### Test density per area (test cases run / test functions / test-file lines → module size)
| Area | Test files | Cases (defs) | Test LOC | Module LOC | Kind |
|---|---|---|---|---|---|
| Score (S3/S4, layer-1 tune) | test_score | 23 (23) | 483 | score.py 159 | synthetic unit tests, the densest area |
| Horizon / DEM masks | test_horizon, test_dem_site | 19+3 (10+3) | 250 | horizon/* ~350 | synthetic grids plus real 5 m Site01 DEM |
| Search (S6 local) | test_search, test_search_site01_e2e | 12+1 | 260 | search/local 127 | synthetic, plus 1 real e2e |
| Deep search (S7) | test_deep_search | 8 (7) | 269 | search/deep 221 | synthetic / stubbed |
| Hazards (layer B, PCP, Metzger) | test_hazards | 8 | 104 | hazards/* ~490 | synthetic tables, thin per LOC |
| Visibility / series | test_visibility, test_series | 6+6 | 251 | visibility 94 | synthetic sky samples |
| Ephemeris | test_ephemeris | 7 (2, parametrized) | 183 | spice 87 | **JPL Horizons fixtures** (12 files, Site01/04/07 in Jan and Jul 2027) |
| API / planner | test_api_site, test_planner_week | 8+1 | 166 | app.py 394, planner_payload 179 | FastAPI TestClient e2e, real or mock |
| Golden aggregates | test_site01_week_aggregates | 2 | 66 | planner_payload | **golden JSON** (`site01_week_aggregates.json`, `site01_20270101_07_aggregates.json`) |
| S12 validation | test_s12_validation_harness | 3 | 49 | scripts/s12_* 135 | script dry-run / smoke only |
| Package | test_package | 3 | 17 | — | import/constants |

- **Heavy:** score (23 tests over a 159-line module, retuned twice), horizon geometry, local search, and ephemeris. Ephemeris is checked against independent JPL Horizons truth.
- **Thin:**
  - hazards: 8 tests for about 490 LOC across 7 modules, including PCP climatology, raster fill and the new Metzger slope factor
  - `api/app.py`: 394 LOC, the most-churned file in the repo
  - S12 validation: only dry-runs. There is no assertion on PGDA69 agreement numbers.
  - `planner_templates.py`, `mask_store.py`, `cap_index.py` and `scripts/precompute.py`: no direct tests
  - web/JS: no tests apart from a page-served check
- **Missing from this branch:** the S9 region map (`4a8c8ab`, branch `scope/s9-region-map`) adds `test_region_map.py` (412 lines) and `test_api_region_map.py` (86 lines). That branch is not merged into main or into this branch, so those tests did not run.
- Fixture tests make up about 4,750 of the roughly 7,570 test lines in git history (Horizons text files plus golden JSON).

## B) Git history
- 32 commits, single author, 10 merged PRs (#1 to #10).
- Local `main` (e8a32d0) is 7 merges behind `origin/main` (738c66e).
- **Unmerged branches:**
  - `scope/s9-region-map`, which branches off main on its own
  - `scope/s5-hazards-wire` → `scope/s12-s14-s15-validation-claims`, which are stacked (s5 is an ancestor of HEAD)

### Timeline
| Date | Commit / PR | Milestone |
|---|---|---|
| 11-11 | 1ffd426 to 5bc6979 | Project definition, decisions, README. A geometry LaTeX primer was added, then removed (−438). |
| 11-14 midday | PR #1 to #3 (docs branch) | Product ledger, weekend plan. The plan was **rejected and replaced** by a two-cycle plan (c62a3d3, +241/−251), then a "full scope + fallback cut order" plan (c8da862, +199/−147). |
| 11-14 15:50 | aad6086 (PR #4) | Phase 0: site×time engine, mock horizon chart, contracts (S1/S2; +7,216, mostly fixtures and docs) |
| 11-14 17:50 | 0ec8d82 (PR #4) | Layer-B hazards, fail-close surface scoring (S5) |
| 11-14 18:37 | 44ce469 (PR #5) | S8 interactive horizon planner, cached masks, mission templates |
| 11-14 19:47 | 4aba828 (PR #6) | S3/S4 risk×bonus score, lit gate, Site01 golden aggregates |
| 11-14 20:49 | bcb3f9a (PR #7) | S6 local search, companion score, leaderboard (+1,168/−145) |
| 11-15 08:24 | 36f2eed (PR #8) | Overnight resume-safe 1 km mask-cap script |
| 11-15 09:28 | 3760277 (PR #9) | Layer-1 tune locked at β=0.25 with a 40% cap (tune script, 3 decision records) |
| 11-15 11:41 | 3ce17b6 (PR #10) | S7 deep search, dual modes, POST /deep-search |
| 11-15 12:01 | 4a8c8ab (unmerged) | S9 region score map on a 3D Moon |
| 11-15 12:23 | 0004b96 (unmerged) | Hazard rasters wired, Diviner PCP climatology |
| 11-15 13:19 | d158e3e (HEAD) | S12 validation harness, S14 claims honesty, S15 docs, Metzger slope |
| Uncommitted | — | S10/S11: first-person view, desktop/Tauri, deploy, about 20 decision records |

S1 to S15 were built in roughly 22 working hours (11-14 15:50 to 11-15 13:19), at about one scope per hour.

### Lines added / deleted per area (all non-merge commits)
- tests: +7,571/−155 (mostly fixtures)
- docs: +7,326/−876
- web: +1,373/−20
- scripts: +1,058
- moonpark misc (planner, providers, visibility, site01, region_map): +769
- hazards: +511/−16
- api: +455/−43
- search: +379/−5
- horizon: +350
- score: +204/−44
- ephemeris: +90

Docs and decision records are about half of all non-fixture lines.

### Churn and rework
- Most-touched files outside records:
  - `web/index.html` (7 commits)
  - `api/app.py` (6, and modified again in the working tree)
  - `score.py` and `test_score.py` (5 each: aad6086 → 0ec8d82 → 4aba828 → bcb3f9a → 3760277)
  - `hazards/moon.py`, `planner_payload.py`, `search/__init__.py`, `test_hazards.py`, `test_api_site.py` (3 each)
- There are no `git revert` commits. Rework shows up as:
  - planning churn: the rejected weekend plan, the cut-order rewrite, "Set the submission cut in one record only"
  - score retunes: S3/S4 formula, S6 companion score (−145), then the β/cap tune
  - the hazard soil model reworked for Metzger (`soil.py`, 29 lines changed in d158e3e)
  - the README rewritten in d158e3e (134 lines changed) for claims honesty
- Engine geometry (ephemeris, horizon) was written once and never changed: it is stable and well tested.
