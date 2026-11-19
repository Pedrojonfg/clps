# Usage limits: measurements and chosen values

Decision: `D-20261118-pj-cd33` (only the strictly necessary limits; values taken from tests; the time budget is a
target, not a limit). This page records how the limits were measured, the raw results, and the values set in
`moonpark/api/app.py`.

Measured 2026-11-19 on one machine (below), about 3.5 hours of runs. Raw numbers: one JSON object per run, written
by the script (`--out`), kept outside the repo in the session scratchpad (`site.jsonl`, `site_rep.jsonl`,
`site_local.jsonl`, `deep.jsonl`); the tables below are generated from them.

## Chosen limits

Rule from the decision: each limit is the **largest tested size that finished without error under the memory
ceiling** (3.5 GB peak RSS, half the RAM). No time cap. Requests above a limit get **422** with
`{"error": "limit_exceeded", "field": ..., "message": ...}`; the message names the field and the limit. Values
live in `moonpark/api/app.py` (`SITE_MAX_*`, `LOCAL_SEARCH_MAX_WINDOW_H`, `HAZARD_MAX_SPAN_H`, `DEEP_MAX_*`).

| Limit | Value | Field in the 422 | Applies to | Why this value (measured) | What breaks first above it |
|---|---|---|---|---|---|
| `SITE_MAX_WINDOW_H` | 70127 h end - start (70128 hourly steps, 2922 days) | `start/end` | /site | 2922 days worked at step 60 and 10 (hazards off): 22 s / 92 s, 312 / 632 MB | nothing seen: the largest size tried. Beyond: response size (57 MB at step 10) |
| `SITE_MAX_SAMPLES` | 420763 samples | `step_min` | /site | 2922 days at step 10; 292 days at step 1 (420421 samples) used the same 632 MB: memory follows samples, not the step | nothing seen; ~0.9 KB per sample, so ~3.5 GB near 3.5 M samples (extrapolated) |
| `HAZARD_MAX_SPAN_H` | 360 h of lunar local time | `start/end` | /site and /deep-search with hazards on | /site 15 days (359 h): 3457 MB; deep 3 cells x 14 days (359 h + 1.3 deg of longitude = 361.5 h): 3505 MB | memory: /site 16 days (383 h) passed 3.5 GB; deep 10000 cells x 14 days optimized (508 h) passed 3.5 GB |
| `LOCAL_SEARCH_MAX_WINDOW_H` | 744 h (31 days) | `local_search` | /site local_search=1 | largest window tried with hazards off: 31 days at step 10 took 1343 s (22 min) and 256 MB; 7 days 73 s; hazards on: 1 day 16 s / 814 MB, 5 days 157 s / 3139 MB (inside `HAZARD_MAX_SPAN_H`) | time (quadratic: it builds 2h+1 full payloads of h hours); time is not a limit by decision, so 744 h is the largest size measured, not a time cap |
| `DEEP_MAX_CELLS` | 145431 cells | `lat_min/lat_max/lon_min/lon_max` | /deep-search | optimized, 14 days of starts: 11 s, 527 MB; the largest rectangle tried (lat -89.9..-80, lon 0..180, about half the cap) | nothing seen |
| `DEEP_MAX_EVALUATIONS` | 1,680,000 cells x window starts | `start/end` | /deep-search total_coverage (and an explicit `start_n` in optimized) | 10000 cells x 168 starts: 19 min, 3178 MB, 384 MB response | memory (~1.7 KB per row kept and serialized) and the response size |
| `DEEP_MAX_SKY_SAMPLES` | 1,920,000 cells x samples from start to end | `step_min` | /deep-search total_coverage | 10000 cells x 192 h at step 60 (same run) | memory: the sky of every cell is kept for the whole span (~0.33 KB per sample); at step 1 a 1-day search of 10000 cells would be 28.8 M samples (~9.5 GB, extrapolated) |

Optimized mode is not limited by evaluations or sky samples: it evaluates only from its start points
(~60 by default) and their hill climbs, a few hundred rows (529-834 measured) at any region size tried.

The old cap (744 hourly steps, ~31 days, for every /site request and every deep-search span) was both too narrow
and too wide: with hazards off 2922 days work; with hazards on, 31 days fail (more than 3.5 GB) on this machine.

### Findings worth acting on (outside this change)

1. **Hazards memory is the binding constraint, and it is a cache that never shrinks.** Peak RSS with hazards on
   grows ~65-70 MB per Diviner PCP local-time bin touched: each bin (`data/hazards/pcp/<season>/ltimNN.npz`) holds
   3.6 M pixels stored as float32 but loaded with `x` and `y` converted to float64
   (`moonpark/hazards/pcp.py` `_load_bin`), 72 MB per bin. A bin covers 0.25 lunar hours = ~7.4 Earth hours, so
   memory grows ~230 MB per day of window (+ bins added by longitude width in a deep search). The bins stay in
   the process-wide `default_moon_hazards()` cache: in the desktop engine (one process for all requests) a few
   requests at different dates or longitudes accumulate up to 96 bins per season (~6.9 GB, ~13.8 GB for both
   seasons) whatever the per-request limit. These measurements are per fresh process, so the per-request limit
   does not protect a long session. Keeping `x`/`y` float32 would cut ~40%; an LRU bound on the bin cache would
   bound the session. Not changed here (not in this task's files).
2. **Hazards on is slow in total_coverage**: 1000 cells x 24 starts (24000 evaluations, step 60) did not finish
   in 20 min (1067 MB when stopped); 3 cells x 336 starts at step 10 took 197 s. Time is not a limit per the
   decision, so no limit was set from it; an overnight run can measure where it ends.
3. **A rectangle that contains the pole or spans all longitudes selects almost nothing**:
   `sites_in_latlon_rect(-90, -80, 0, 360)` returns 609 cells of 290289 (the corner-based stereo bounding box
   collapses). This also caps the largest region a user can ask for at roughly half the cap (lon width 180).
   Not changed here.
4. **Response size** grows to hundreds of MB in total_coverage (230 MB for 1.0 M rows, 384 MB for 1.68 M); the
   engine survives it, the desktop UI was not measured with such responses.
5. **Memory per /site request with hazards off is flat** (~250 MB up to a year; 632 MB at 420 k samples), so
   hazards-off windows are limited only by what was tested.

## How it was measured

- Script: `scripts/bench_limits.py` (run from the repo root). Each measurement is one request in its own Python
  subprocess (fresh interpreter, cold caches, like the first request after the engine starts) through FastAPI's
  `TestClient`, with all usage limits lifted so sizes beyond them can be measured.
- Client conditions: no own-DEM masks (`moonpark.horizon.mask_store.load_cached_mask` and
  `mask_schedule_for_site` patched to return None), so `/site` snaps to the 1 km cap mask, as `/deep-search` does
  (same setup as `tests/test_deep_search_decisions.py`). Real data otherwise: SPICE kernels, the 1 km cap index,
  Diviner PCP temperature bins, slope, PSR.
- Peak RSS: `resource.getrusage(RUSAGE_SELF).ru_maxrss` of the child at the end of the request (includes the
  interpreter and imports, ~245 MB). The parent also polls `/proc/<pid>/status` every 0.2 s and kills the child
  above **3.5 GB** (half the RAM) or after **20 min**; a killed run is reported with the RSS polled at the kill.
- One measurement at a time. Times are wall-clock for the request only (not the imports).
- Machine: one machine, 12 cores, 7 GB RAM, 2 GB swap, WSL2 Linux. Other agents ran light jobs at the same time
  (builds), so times are approximate; three early deep runs (optimized 1000 and 10000 cells, total_coverage
  1000 cells at step 10) overlapped with a leftover benchmark process using one core: their times may be
  inflated a little; their RSS is per-process and not affected.
- Variance: the fast `/site` cases were repeated (4 runs: 1 from the matrix + 3 repeats); the table shows median
  and min-max. Wall times vary 2-5x between runs when hazards are on (reading the PCP bins from disk competes
  with other I/O); peak RSS varies by less than 3%.
- Window convention: "N days" = `start` 2027-01-01T00:00Z to `end` N x 24 - 1 hours later (N x 24 hourly
  samples at step 60). Energy mode = `battery_wh=1000, array_w=100, dark_w=20`.
- Deep-search regions: lat/lon boxes centred on (-87.5, 222) sized by bisection to hold exactly the target number
  of 1 km cap cells (`sites_in_latlon_rect`); above 20,000 cells a sector lat -89.9..-80, lon 0..W. "span" =
  number of window starts / 24 (one start per hour); `end` = start + starts + window_hours - 1 h.

## GET /site

<!-- SITE_TABLE -->
| local_search | hazards | step_min | window (days / h) | energy | samples | outcome | wall s (n; min-max) | peak RSS MB | response MB |
|---|---|---|---|---|---|---|---|---|---|
| no | off | 60 | 1 / 24 | off | 24 | ok | 2.2 (4; 1.2-6.0) | 253 | 0.02 |
| no | off | 60 | 7 / 168 | off | 168 | ok | 1.6 (4; 1.2-2.3) | 249 | 0.04 |
| no | off | 60 | 31 / 744 | off | 744 | ok | 1.2 (4; 1.1-1.7) | 249 | 0.11 |
| no | off | 60 | 62 / 1488 | off | 1488 | ok | 1.2 | 246 | 0.21 |
| no | off | 60 | 124 / 2976 | off | 2976 | ok | 1.4 | 252 | 0.40 |
| no | off | 60 | 1 / 24 | on | 24 | ok | 1.1 | 245 | 0.02 |
| no | off | 60 | 7 / 168 | on | 168 | ok | 1.1 | 247 | 0.04 |
| no | off | 60 | 31 / 744 | on | 744 | ok | 1.1 | 248 | 0.12 |
| no | off | 60 | 62 / 1488 | on | 1488 | ok | 1.3 | 248 | 0.22 |
| no | off | 60 | 124 / 2976 | on | 2976 | ok | 1.6 | 251 | 0.42 |
| no | off | 60 | 365 / 8760 | on | 8760 | ok | 9.9 | 256 | 1.20 |
| no | off | 60 | 730 / 17520 | on | 17520 | ok | 13.9 | 265 | 2.39 |
| no | off | 60 | 1461 / 35064 | on | 35064 | ok | 16.8 | 281 | 4.76 |
| no | off | 60 | 2922 / 70128 | on | 70128 | ok | 22.4 | 312 | 9.49 |
| no | off | 1 | 292 / 7008 | on | 420421 | ok | 110.1 | 632 | 56.94 |
| no | off | 10 | 1 / 24 | off | 139 | ok | 1.2 (4; 1.0-4.5) | 245 | 0.03 |
| no | off | 10 | 7 / 168 | off | 1003 | ok | 1.5 (4; 1.5-2.1) | 250 | 0.15 |
| no | off | 10 | 31 / 744 | off | 4459 | ok | 2.3 (4; 2.2-2.5) | 253 | 0.60 |
| no | off | 10 | 62 / 1488 | off | 8923 | ok | 3.0 | 253 | 1.17 |
| no | off | 10 | 124 / 2976 | off | 17851 | ok | 7.8 | 272 | 2.33 |
| no | off | 10 | 1 / 24 | on | 139 | ok | 1.1 | 245 | 0.04 |
| no | off | 10 | 7 / 168 | on | 1003 | ok | 1.3 | 245 | 0.16 |
| no | off | 10 | 31 / 744 | on | 4459 | ok | 2.6 | 254 | 0.63 |
| no | off | 10 | 62 / 1488 | on | 8923 | ok | 5.9 | 254 | 1.23 |
| no | off | 10 | 124 / 2976 | on | 17851 | ok | 12.6 | 265 | 2.44 |
| no | off | 10 | 365 / 8760 | on | 52555 | ok | 13.9 | 294 | 7.13 |
| no | off | 10 | 730 / 17520 | on | 105115 | ok | 24.4 | 344 | 14.24 |
| no | off | 10 | 1461 / 35064 | on | 210379 | ok | 62.9 | 439 | 28.45 |
| no | off | 10 | 2922 / 70128 | on | 420763 | ok | 92.4 | 632 | 56.89 |
| no | on | 60 | 1 / 24 | off | 24 | ok | 2.7 (4; 1.6-4.7) | 548 | 0.04 |
| no | on | 60 | 7 / 168 | off | 168 | ok | 17.0 (4; 6.0-22.8) | 1746 | 0.19 |
| no | on | 60 | 10 / 240 | off | 240 | ok | 75.0 | 2381 | 0.27 |
| no | on | 60 | 12 / 288 | off | 288 | ok | 75.2 | 2843 | 0.32 |
| no | on | 60 | 14 / 336 | off | 336 | ok | 57.9 | 3251 | 0.37 |
| no | on | 60 | 15 / 360 | off | 360 | ok | 144.0 | 3457 | 0.39 |
| no | on | 60 | 16 / 384 | off | 384 | killed: RSS > 3.5 GB | - | >3586 | - |
| no | on | 60 | 17 / 408 | off | 408 | killed: RSS > 3.5 GB | - | >3611 | - |
| no | on | 60 | 31 / 744 | off | 744 | killed: RSS > 3.5 GB | - | >3592 | - |
| no | on | 60 | 1 / 24 | on | 24 | ok | 7.8 | 546 | 0.04 |
| no | on | 60 | 7 / 168 | on | 168 | ok | 15.0 | 1735 | 0.20 |
| no | on | 60 | 31 / 744 | on | 744 | killed: RSS > 3.5 GB | - | >3585 | - |
| no | on | 1 | 14 / 336 | on | 20101 | ok | 86.7 | 3277 | 21.19 |
| no | on | 10 | 1 / 24 | off | 139 | ok | 2.8 (4; 2.0-8.3) | 552 | 0.17 |
| no | on | 10 | 7 / 168 | off | 1003 | ok | 21.8 (4; 13.0-36.1) | 1777 | 1.08 |
| no | on | 10 | 10 / 240 | off | 1435 | ok | 43.1 | 2396 | 1.52 |
| no | on | 10 | 12 / 288 | off | 1723 | ok | 37.8 | 2845 | 1.82 |
| no | on | 10 | 14 / 336 | off | 2011 | ok | 26.3 | 3256 | 2.12 |
| no | on | 10 | 17 / 408 | off | 2443 | killed: RSS > 3.5 GB | - | >3615 | - |
| no | on | 10 | 31 / 744 | off | 4459 | killed: RSS > 3.5 GB | - | >3589 | - |
| no | on | 10 | 1 / 24 | on | 139 | ok | 13.4 | 548 | 0.17 |
| no | on | 10 | 7 / 168 | on | 1003 | ok | 18.8 | 1736 | 1.09 |
| no | on | 10 | 31 / 744 | on | 4459 | killed: RSS > 3.5 GB | - | >3594 | - |
| yes | off | 10 | 1 / 24 | off | 139 | ok | 6.0 | 254 | 0.05 |
<!-- /SITE_TABLE -->

## POST /deep-search

<!-- DEEP_TABLE -->
| mode | cells | window_h | span (days / starts) | step_min | hazards | evaluations (cells x starts) | sky samples (cells x span samples) | outcome | wall s | peak RSS MB | response MB | rows evaluated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| total_coverage | 3 | 24 | 1 / 24 | 60 | off | 72 | 144 | ok | 1.211 | 246 | 0.02 | 72 |
| total_coverage | 100 | 24 | 1 / 24 | 60 | off | 2400 | 4800 | ok | 3.608 | 251 | 0.55 | 2400 |
| total_coverage | 1000 | 24 | 1 / 24 | 60 | off | 24000 | 48000 | ok | 22.253 | 296 | 5.48 | 24000 |
| total_coverage | 10000 | 24 | 1 / 24 | 60 | off | 240000 | 480000 | ok | 200.749 | 801 | 54.82 | 240000 |
| total_coverage | 3 | 24 | 14 / 336 | 60 | off | 1008 | 1080 | ok | 1.482 | 247 | 0.24 | 1008 |
| total_coverage | 100 | 24 | 14 / 336 | 60 | off | 33600 | 36000 | ok | 21.227 | 302 | 7.65 | 33600 |
| total_coverage | 1000 | 24 | 14 / 336 | 60 | off | 336000 | 360000 | ok | 212.791 | 815 | 76.69 | 336000 |
| optimized | 1000 | 24 | 14 / 336 | 60 | off | 336000 | 360000 | ok | 6.737 | 255 | 0.13 | 529 |
| optimized | 10000 | 24 | 14 / 336 | 60 | off | 3360000 | 3600000 | ok | 8.354 | 299 | 0.18 | 770 |
| total_coverage | 1000 | 24 | 1 / 24 | 10 | off | 24000 | 283000 | ok | 100.359 | 376 | 5.48 | 24000 |
| total_coverage | 1000 | 24 | 1 / 24 | 60 | on | 24000 | 48000 | killed: timeout | 1200.35 | 1067 (at kill) | - | - |
| optimized | 29999 | 24 | 14 / 336 | 60 | off | 10079664 | 10799640 | ok | 9.169 | 386 | 0.10 | 408 |
| optimized | 100000 | 24 | 14 / 336 | 60 | off | 33600000 | 36000000 | ok | 11.359 | 438 | 0.19 | 834 |
| optimized | 145431 | 24 | 14 / 336 | 60 | off | 48864816 | 52355160 | ok | 11.334 | 527 | 0.15 | 656 |
| optimized | 10000 | 24 | 14 / 336 | 10 | on | 3360000 | 21550000 | killed: RSS > 3.5 GB | 218.12 | >3629 | - | - |
| total_coverage | 1000 | 168 | 1 / 24 | 60 | off | 24000 | 192000 | ok | 63.627 | 343 | 4.81 | 24000 |
| total_coverage | 10 | 168 | 1 / 24 | 10 | on | 240 | 11470 | ok | 73.374 | 2033 | 0.05 | 240 |
| total_coverage | 3 | 24 | 14 / 336 | 10 | on | 1008 | 6465 | ok | 197.396 | 3505 | 0.24 | 1008 |
| total_coverage | 3000 | 24 | 14 / 336 | 60 | off | 1008000 | 1080000 | ok | 641.428 | 1948 | 230.15 | 1008000 |
| total_coverage | 10000 | 24 | 7 / 168 | 60 | off | 1680000 | 1920000 | ok | 1149.237 | 3178 | 383.69 | 1680000 |
<!-- /DEEP_TABLE -->

Not measured (left for the overnight run): hazards-on total_coverage beyond 240 evaluations at 10 cells (time,
not memory, is what grows: see finding 2); window 168 at more than 1000 cells; step 10 with more than 1000 cells
in total_coverage; regions above 145431 cells (no single rectangle selects more, finding 3).

## Commands

```bash
# GET /site matrix (window 1..124 days, step 60/10, hazards off/on, energy off/on), growing until a failure
python scripts/bench_limits.py site --out RESULTS/site.jsonl
# the edges: hazards on 10..21 days; hazards off 1..8 years; step 1; local search
python scripts/bench_limits.py site --out RESULTS/site.jsonl --days 10,12,14,15,16,17,21 --steps 60,10 --hazards 1 --energy 0
python scripts/bench_limits.py site --out RESULTS/site.jsonl --days 365,730,1461,2922 --steps 60,10 --hazards 0 --energy 1
python scripts/bench_limits.py site --out RESULTS/site.jsonl --days 292 --steps 1 --hazards 0 --energy 1
python scripts/bench_limits.py site --out RESULTS/site_local.jsonl --local 1 --energy 0 --steps 10 --days 1,7,31 --hazards 0 --timeout-s 1800
python scripts/bench_limits.py site --out RESULTS/site_local.jsonl --local 1 --energy 0 --steps 10 --days 1,5 --hazards 1
# repeats of the fast cases (variance)
python scripts/bench_limits.py site --out RESULTS/site_rep.jsonl --days 1,7,31 --steps 60,10 --hazards 0 --energy 0 --repeat 3
python scripts/bench_limits.py site --out RESULTS/site_rep.jsonl --days 1,7 --steps 60,10 --hazards 1 --energy 0 --repeat 3
# POST /deep-search: grid (stops growing cells at the first failure) and explicit runs
python scripts/bench_limits.py deep --out RESULTS/deep.jsonl --modes total_coverage --steps 60 --hazards 0 --windows 24 --spans 1,14 --cells 3,100,1000,10000
python scripts/bench_limits.py deep --out RESULTS/deep.jsonl --plan "30000:24:14:optimized:60:0 100000:24:14:optimized:60:0 145431:24:14:optimized:60:0 10000:24:14:optimized:10:1 1000:168:1:total_coverage:60:0 10:168:1:total_coverage:10:1 3:24:14:total_coverage:10:1 3000:24:14:total_coverage:60:0 10000:24:7:total_coverage:60:0"
# plan items: cells:window_h:span_days:mode:step_min:hazards[:start_n]; defaults --timeout-s 1200 --rss-cap-mb 3584
```

To re-measure on another machine (or overnight with larger sizes), run the commands with larger `--days`,
`--cells` or plan items, then set the constants in `moonpark/api/app.py` to the largest sizes that finished;
`tests/test_usage_limits.py` reads the constants, so it needs no edits.
