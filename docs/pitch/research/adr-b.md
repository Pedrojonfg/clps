# ADR digest B

Paths: `docs/records/decisions/<id>-*.md`. All records listed are `accepted`.

## 1. One line per ADR

- **a3b3**: aim for full scope by Sunday; cut only at a failed checkpoint or the freeze.
- **aa58**: demo computes Sun/Earth live and reads masks from a disk cache. User picks site, dates and needs (mission templates). Test window: first week of Jan 2027.
- **affb**: missing temperature pixels filled GDAL-style (4-quadrant inverse distance, 100 px, no smoothing).
- **b8d3**: surface hazards in; trajectory optimization out; body-agnostic seams, Moon only for now.
- **beb5**: golden fixture of week-level aggregates for Site01. Supersedes 1a46.
- **bf69**: PSR (permanently shadowed region) is only an early impossible-site check. Roughness, rocks and PGDA 69 stay out.
- **d7d9**: portfolio scope runs to 20 Nov; the Space Apps entry is a cut of it. Supersedes 7e2a.
- **da5f**: next build is the horizon chart on real data for Site01 (AI-decided, delegated by pj).
- **de42**: two-layer score: fail-closed zero, then assurance, then weights. Supersedes 60ab (formula value only).
- **ecc9**: local search returns as a `local_search` block on `GET /site`.
- **f369**: horizon mask from LOLA DEMs, resolution graded by distance to 250 km; 5 h tolerance.
- **f57e**: local search uses the request's hazards. Rows missing temperature or dust are starred; a missing PSR map changes nothing.
- **06cb**: Metzger slope factor β=cos θ on the grain term only. Supersedes 050d.
- **0ee7**: S7 is done when the demo works; a medium (1–2 h) megatest runs tonight.
- **1ebf**: hill climb steps ±1 cell / ±1 h and stops at a local peak.
- **48ee**: β=0.25, cap 0.40, tuning done. Supersedes 6ce5 and 7520.
- **54f0**: deep search modes: `total_coverage` plus a default `optimized` (multistart hill climb).
- **60a3**: deep search gets its own `POST /deep-search` endpoint.
- **7c70**: tuning gate passes if the inversion rate is 2–40%.
- **8a25**: optimized search default budget is 5 min.
- **c159**: search range is a map rectangle snapped to cap cells, with hourly starts.
- **cb6b**: start count follows a wall-clock budget on whichever host runs the search.
- **d37a**: inversion rates measured separately for feasible and infeasible pairs.
- **e3cf**: starts on a regular space-filling grid; user sets N.

## 2. Engine architecture

**Masks (f369).** Horizon angle θ(az) = max over distance d of atan((h(d)−h0−d²/2R)/d). DEM resolution by distance band (`f369:65-70`):

| Distance | Resolution |
|---|---|
| 0–250 m | finest available, 5–20 m |
| 250 m–1 km | 20 m |
| 1–2 km | 40 m |
| 2–5 km | 100 m |
| 5–25 km | 80 m |
| 25–250 km | 240 m |

720 azimuths, observer height 2 m, ~150 ms per mask. The mask doesn't depend on the date, so the 80–90°S cap is precomputed (1 km now, 100 m later). Sky, series and score are computed live per request (`aa58:34`).

**Score.**
- Layer 0: zero if any minimum fails. Temperature and dust limits count as minima (5cfa).
- Layer 1: risk R = ∏Φ(slack/σ). σ = 5 h for night and lit periods, 1 h for no-Earth.
- Bonus B for extra hours: score = R·(1+βB), β=0.25, uplift capped at 0.40 (`48ee:51-68`).
- Infeasible cells also get a companion score, so search has a direction to climb (5577).

**Hazards.**
- Temperature: Diviner climatology, gaps filled per affb.
- Dust: soil resistance ρgD·cosθ+α (`06cb:35`), labelled "not lofting rate".
- PSR: precheck only.

**Search.**
- Local search (S6): runs inside `/site` with the request's hazards; gaps starred.
- Deep search (S7): runs on a rectangle × hourly grid.
  - `total_coverage` enumerates everything and may claim "grid optimum".
  - `optimized` uses a regular start mesh sized to a 5-min budget, then hill climb. It may only claim "best seen" (`54f0:64`).

**Validation.**
- In place: Horizons fixtures, the 28-point tolerance test, and the aggregate golden.
- Not run yet: the short-night re-check and the PGDA 69 comparison (`docs/validation.md:8-9`).
- Deferred: the megatest.

## 3. Key decisions and why

1. **Graded mask schedule** (`f369:24,37,49`). A single 240 m resolution was off by 37 illumination points and 1,289 h of longest night. Reach is measured: the farthest horizon-setting point was 196 km, and cutting at 150 km lost 0.49°. The 5 h tolerance comes from Blue Ghost M1's ~5 h on battery.
2. **No normalization against the best site** (`de42:40,71`). pj called that "cheating, because a mission may have very tough requirements." He prefers to show bad news.
3. **Risk times a capped bonus** (`48ee:66-69`). Extra comfort can't wash out assurance, which was the open risk at `de42:46`.
4. **Two search modes with honest claims** (`54f0:20,39`). Brute force takes ~1 min for 10×10 km × 7 d and ~23 min for 50×50 km. pj: lunar companies "can afford to lose a day." ML/RL and gradient descent were rejected for v1 (`54f0:66`).
5. **Budget tied to the executing host** (`cb6b:39`). pj: agencies have powerful computers, and running there costs pj almost nothing. This seeded the later move to remote masks plus client-side compute.
6. **Metzger as published** (`06cb:20,43,59`). It replaces a placeholder `base/cos θ` that hard-coded 0.5 (a crater-experiment β). β is floored at 0.05.
7. **PSR as a precheck** (`bf69:39`). It overlaps the Sun minima, but tells the planner up front "cannot land here."

## 4. Pivots and the evidence behind them

**Bonus cap 0.10 → 0.30 → 0.40, β 0.15 → 0.25** (7520 → 6ce5 → 48ee).
- 6ce5: a 10% cap made the bonus barely matter (`6ce5:20`).
- pj fixed the 2–40% band before the run (`7c70:38`) and split it by feasible vs infeasible pairs (d37a).
- The run (`docs/records/tasks/T-20261115-pj-d567-s6-green-layer1-tune.md:63`): `scripts/tune_layer1_bonus.py`, Site01 × 10 templates × all of 2027, 75,410 scores in ~12 s.
- At β=0.15: inversion ≈0.94% (feasible) and 0.00% (infeasible), both REOPEN. The β sweep stayed below 2%.
- pj switched metrics to variance and top-k overlap. β=0.25 had a real effect with 0% cap hits; β≥0.35 hit the cap and pulled rankings back toward pure R (`48ee:20`).
- The cap was raised to 0.40 only as a "disaster rail" (`48ee:39,44`).
- Caveat: the pre-registered band was never satisfied. The metric was replaced, and the reopen trigger is "other geography" (`48ee:76`).

**Other reversals.**
- **Mask schedule:** 240 m at 5–25 km gave a 7 h error at 1 of 28 points; that band moved to 80 m (`f369:27,54`).
- **Golden fixture:** "no golden" (1a46) became aggregate-only (beb5).
- **Scope:** portfolio-only (7e2a) and hackathon-lite became full scope by Sunday (`d7d9:36`, `a3b3:29`).
- **Demo:** the precooked `/site` (da5f) became live sky with cached masks (`aa58:20,67`).
- **Dust:** the placeholder became Metzger (06cb).

## 5. Novel ground; strong vs thin validation

**Novel.**
- Terrain horizons turned into per-site, per-hour survival metrics.
- Bridged lit periods.
- An assurance score from slack/σ, with an "inside the impossible" companion that guides search.
- Search output labelled by claim type.
- Error stated in mission hours instead of degrees (`f369:53`).

**Strong.**
- Kernels match Horizons to 0.0013° (`f369:26`).
- 28-point output-error study: max 1 h on longest night (`f369:27`).
- Bonus tuning on a full year, 75k scores.
- Golden regression on aggregates.

**Thin.**
- The 28 points all have long nights (≥392 h). The ~50 h regime is unmeasured and the re-check hasn't run (`f369:56`, `validation.md:20`).
- The reference DEM is ~90% interpolated (`f369:57`).
- The PGDA 69 comparison hasn't run and has no threshold (`validation.md:27`).
- Hill climb vs full coverage, the 5-min default and the step sizes are unvalidated; claims are "provisional" (`0ee7:51`).
- The tuning covers one site and its original gate failed.
- Metzger has no stress test (`06cb:67`).
- The fill radius can mix ridge and crater-floor pixels (`affb:46`).
- σ values and independence are assumed (`48ee:52`).
- Observer height 2 m and 720 azimuths were AI test settings, not pj's choice (`f369:58`).
