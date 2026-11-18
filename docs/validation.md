# Validation (S12)

Evidence-gated (`D-de70`). Numbers below stay **planned** until the overnight scripts are run and this file is updated.

| Check | Decision | Status | How to run |
|-------|----------|--------|------------|
| Success X/Y/Z | `D-41fa` | Horizons and score tests exist; the 28-point 5 m comparison is **not in the repo** (removed from claims) | `pytest` |
| Short-night re-check | `D-39f3` (S1) | **planned** — harness is a skeleton, comparison not implemented | `python scripts/s12_short_night_recheck.py` |
| PGDA 69 average illumination | `D-9ab3` (P1), role `D-fe17` | **planned** — harness is a skeleton, comparison not implemented | `python scripts/s12_pgda69_compare.py` |

## Short-night re-check (`D-39f3`)

- Mode: separate report; if \|error\| > 5 h → reopen Y (do not silently change `success_y`).
- Defaults: light definition as the Y comparison is (not yet in the repo); bridge 5 h; tolerance 5 h.
- Sites: Site01 + PGDA-78 / 5 m points with longest night ~40–80 h when available.
- Year: pin in script output when first run (`s12_short_night_year` still deferred until then).

### Results

_No overnight run recorded yet._

## PGDA 69 comparison (`D-9ab3`)

- Product: average solar illumination (south), cite exact file in the run log.
- Sites: PGDA 78 / 5 m schedule set (document IDs/coords in the run output).
- Span: ~18.6 y or product label span; light def match product (any disc default).
- Metric: Δ percentage points per site (ours − map). **No pass/fail threshold in v1.**
- README may say planned / point here until a table exists (`D-fe17`).

### Results

_No overnight run recorded yet._
