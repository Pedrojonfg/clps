# Engine code brief: lunar south-pole site×time evaluator

## 1. Pipeline end to end

1. **Ephemeris.** `SpiceEphemeris.sky` (`moonpark/ephemeris/spice.py:52`) loads DE440s and the Moon kernels (:14). Each hour it calls `spkcpo` (:68-69, LT+S correction, `MOON_ME` frame) and converts to local ENU (`_azel` :42). Output: Sun/Earth az/el and disk radius. Tests check it against JPL Horizons fixtures (0.05° working bound, `tests/test_ephemeris.py:28`).
2. **Horizon masks.** `mask()` (`horizon/mask.py:20`) casts 720 rays over LOLA DEM bands picked by `mask_schedule_for_site` (`horizon/dem_schedule.py:14`). `mask_for_site` (`mask_store.py:70`) caches them. `scripts/precompute.py:main` (:143) builds the 1 km cap offline; `cap_index.py` serves it (:31, :88).
3. **Visibility.** `series()` (`visibility.py:57`) maps azimuth into the mask frame (`_mask_el_at_geo_az` :22), computes visible disk fractions (`sun_fraction` :9), and derives longest night, longest no-Earth gap and longest lit stretch with gap bridging (:31, :40, :86).
4. **Hazards.** `MoonHazards.hazards` (`hazards/moon.py:68`) combines a PSR flag (`LPSR_80S_20MPP`), slope (`LDSM_80S_80MPP`) feeding Metzger soil resistance (`soil.py:15`), and Diviner PCP temperature (`pcp.py:80`). `aggregate_hazards` (:95) keeps the worst case.
5. **Score.** `score()` (`score.py:116`) runs fail-closed hard checks first (`_schedule_layer0` :55, `_surface_layer0` :42), then a soft score (`_layer1_score` :75).
6. **Search.** `local_search` (`search/local.py:40`) slides the window ±h hours. `deep_search` (`search/deep.py:108`) runs either an exhaustive grid (`grid_optimum`) or a multi-start hill climb (`best_seen`).
7. **API.** `build_planner_payload` (`planner_payload.py:50`) joins everything. Routes: `GET /site` (`api/app.py:123`), `POST /deep-search` (:229, JSON or CSV), `GET /mission-templates` (:116); `/site?mock=1` is CI only (:17).

## 2. Most impressive pieces

1. **Multi-resolution horizon ray casting** (`mask.py:49-60`, schedule in `precompute.py:67-74`).
   - Each of 720 azimuths (0.5° apart) is sampled at a step of half the DEM pixel. Resolution falls with distance: 20 m out to 1 km, 40 m (coarsened) at 1–2 km, 80 m at 2–25 km, and 240 m at 25–250 km.
   - Elevation angles include the Moon's curvature drop, `d²/2R`. The whole ray fan is a single NumPy broadcast feeding bilinear `map_coordinates`.
   - That is about 2,600 samples per ray, or about 1.9 M DEM samples per mask, and it reaches 250 km of terrain.
2. **Overnight precompute with fork-COW sharing** (`precompute.py:181-201`).
   - The parent loads the 80 m and 240 m DEMs once (about 0.47 GB). Forked workers share them copy-on-write, and each worker reads only a 6 km window of the 20 m DEM.
   - Output is 100 km tiles plus a Parquet index, and the run can resume via `progress.json`.
3. **Fractional disk occlusion** (`visibility.py:9-19`). The Sun and Earth are treated as disks, not points. The visible fraction is the area of a circular segment, `1 − (acos x − x√(1−x²))/π`, where x = (el − horizon)/radius. Grazing light at the pole is graded instead of on/off, and Earth uses the same function with its own angular radius.
4. **Fail-closed two-layer score** (`score.py:75-159`).
   - **Layer 0:** any violated need (night too long, no-Earth gap too long, require-both, minimum lit stretch, temperature, dust) forces `score = 0` and `feasible = False`. The failing reasons are listed.
   - **Layer 1:** R = Π Φ(slack/σ), a Gaussian CDF of each margin, so a site that barely meets a need scores about 0.5, not 1. It is multiplied by (1 + βB), where B is a weighted bonus for lit and Earth-visible hours.
   - A "companion score" is computed even for infeasible rows, so they can still be ranked as near misses. Provenance (formula, sigmas, decision IDs) is attached to every score.
5. **Multi-start hill climb over site×time** (`deep.py:49-92, 171-193`).
   - Seeds sit on a regular lattice in (site, time) index space. Each climbs by steepest ascent over ±1 km / ±1 h neighbours, ranking feasible rows by score, then infeasible ones by companion score.
   - A `(site, time)` cache prevents repeat evaluations. Seed count comes from the time budget: 300 s / (0.5 s × 10) = 60.
6. **Diviner temperature lookup** (`pcp.py:24-116`). Season comes from SPICE subsolar latitude. Each local-time bin gets a cached cKDTree; gaps are filled with nearest-per-quadrant inverse-distance weighting, up to 100 px.

## 3. Real numbers

| Item | Value | Where |
|---|---|---|
| Mask size | 720 bins × 0.5°, float32, 2.88 KB each | `mask.py:13` |
| Moon radius | 1,737,400 m (spherical) | `providers.py:22` |
| Observer height | 2 m | `precompute.py:33` |
| Cap grid | 1 km polar-stereo spacing, lat ≤ −80° | `precompute.py:145-147` |
| Cap tiles | 100 km | `precompute.py:31` |
| Cap run (`summary.json`) | 290,289 masks, 44 tiles, 16,174 s (4.49 h), 6 workers, 13–19 masks/s, 839 MB on disk | `data/masks/cap_1km/` |
| Time step | hourly; max 744 steps (31 days) per request | `planner_payload.py:21` |
| Deep-search window | 1–168 h | `api/app.py:212` |
| Score sigmas | night 5 h, lit 5 h, no-Earth 1 h | `score.py:9-11` |
| Score β / uplift cap | β = 0.25, max uplift 0.40 | `score.py:12-13` |
| Deep search | tmax 300 s, leaderboard 20, 10 evals per start, cell 1000 m | `deep.py:13-16` |
| Local search radius | 5 km | `local.py:11` |
| Default bridge | 5 h | `api/app.py:138` |
| Default hazard needs | max temperature 320 K, min soil resistance 0 | `planner_payload.py:93-96` |
| Soil constants | ρ = 1500 kg/m³, D = 70 µm, cohesion 500 Pa, g = 1.62, β floor 0.05 → R ≈ 500.13 Pa | `soil.py` |
| PCP | 240 m pixels, 0.25 h local-time bins | `pcp.py:16`, `lst.py` |
| Templates | Blue Ghost 5 h night; VIPER 50/70 h night, 24 h without Earth | `planner_templates.py` |

## 4. Gaps (code vs claims)

- **Uplift cap never binds.** With β = 0.25 and B ≤ 1 the uplift is at most 25%, so the 40% cap (`score.py:109`) can never trigger.
- **Layer 2 is hardcoded to 0.0** (`score.py:148`).
- **PSR does not fail the score.** `psr_precheck` is computed and its message is "landing is not viable", but `score()` never checks `in_psr`.
- **Local solar time is approximate.** `lst.py:9` computes it as UTC hour + lon/15 (marked "ponytail", i.e. a deliberate stopgap, until a subsolar longitude from the ephemeris is wired in).
- **Soil constants** are Apollo averages, not polar maps (`soil.py:8`, also "ponytail"). The README itself frames it as a resistance proxy, not a dust-lofting rate.
- **Local search only slides time.** `neighbour_sites = []` in the production path (`planner_payload.py:136`, decision D-ecc9).
- **Deep search ignores hazards.** It accepts `hazards_enabled` but `evaluate` always returns `hazards: {}` (`app.py:327`). `eta_s` is always None, and the response is flagged `provisional: True` "until megatest".
- **Deep-search scaling.** Finding a site does a linear scan per evaluation (`app.py:307`), and `_neighbour_indices` is O(sites × times) per step. Both will hurt at 290 k sites.
- **5 m site DEM only for Site01.** `mask_store.py:76` hardcodes Site01's coordinates.
- **Validation pending.** The 0.05° ephemeris bound is not locked (D-4ffe), and the S12 validations are planned, not run. The README says both honestly.
- **Mocks.** The README says the public Pages demo often uses mocked masks.

## 5. Lines of code (`wc -l`)

| Module | LOC |
|---|---|
| hazards/ (pcp 154, moon 103, temperature 60, fill 58, raster 50, soil 35, lst 16) | 476 |
| search/ (deep 221, local 127) | 372 |
| horizon/ (cap_index 102, mask_store 82, mask 70, grid 47, dem_schedule 42) | 345 |
| planner_payload + planner_templates | 329 |
| score.py | 159 |
| visibility.py | 94 |
| ephemeris/spice.py | 87 |
| providers.py | 72 |
| site01.py | 29 |
| **moonpark total** | **~1,970** |
| api/app.py | 394 |
| scripts/precompute.py | 229 |
| tests/ | 2,176 (more than the engine) |
| web/ (JS + HTML) | 1,671 |

The core physics (ephemeris + horizon + visibility) is only about 530 lines.
