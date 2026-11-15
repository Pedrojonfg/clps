# Lunar site×time evaluator (portfolio)

Solo portfolio project inspired by the NASA Space Apps Challenge 2026 brief
**[CLPS Lunar Mission Browser](https://www.spaceappschallenge.org/2026/challenges/clps-lunar-mission-browser/)**.
The challenge text is **heritage inspiration only** — this is **not** a contest
submission and is **not affiliated with or endorsed by NASA** (`D-7e2a`, `D-6663`).

## What this is

A **needs-adapted site×time landing evaluator** for the lunar south pole:
horizon masks + Sun/Earth geometry → visibility series → score (fail-closed on
planner minima) → local / deep search, with surface hazards (temperature,
soil-resistance “dust” proxy) and a web demo.

Claims are **evidence-gated** (`D-de70`): assert only what tests/ADRs back.
If a validation test exists but has not been run, we say so — we do not pretend
it already passed.

## How it is built (high level)

| Piece | Role | Key decisions |
|-------|------|----------------|
| Ephemeris / sky | Sun & Earth az/el | Horizons fixtures = success **X** (`D-41fa`) |
| Horizon masks | Terrain blocking | LOLA DEM schedule (`D-f369`); success **Y** = 28-pt ≤ 5 h |
| Score | Fail-closed then rank | Two-layer + hazards (`D-de42` lineage); success **Z** |
| Dust slot | Soil resistance, not lofting | Metzger β=cos(θ) on grain term (`D-06cb`) |
| Demo hosting | Static Pages for now | Masks often mocked in the public demo (`D-a988`, `D-2533`) |

Decision records: [`docs/records/`](docs/records/). Validation plan: [`docs/validation.md`](docs/validation.md).

## Try today (honest limits)

**Install**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

**Run the API + chart locally** (needs kernels/masks under `data/` for live mode;
without them the UI may use mocks — that is **not** the same as computed overnight
masks, `D-a988`):

```bash
uvicorn api.app:app --reload
# open the URL printed by uvicorn (typically http://127.0.0.1:8000/)
```

**Static demo docs:** [`deploy/README.md`](deploy/README.md) (GitHub Pages).

Without a published precomputed mask archive / mask API, the **full** planner
loop is not what a stranger gets from Pages alone. Local data + API is the
honest try-today path.

## Validation status

| Check | Status |
|-------|--------|
| X/Y/Z unit tests | run `pytest` (see suite) |
| Short-night re-check | harness: `python scripts/s12_short_night_recheck.py` — results **planned** until overnight |
| PGDA 69 comparison | harness: `python scripts/s12_pgda69_compare.py` — **planned**; not a product feature (`D-fe17`) |

## Future

- Publish precomputed masks (location TBD) and/or a mask API (`D-8c03`).
- Remotion demo video **after** the UI is finished (`D-1264`, `D-8fd2`).
- Pitch deck owned by the author for live presentations.

## Repo layout

```
lunar_eval/     engine (ephemeris, horizon, score, search, hazards)
api/            FastAPI routes
web/            static demo UI
tests/          pytest
scripts/        precompute, tune, S12 validation harnesses
docs/records/   decision-flow records
docs/validation.md
```

Language: **repo English**; chat language per person (`docs/records/project.md`).
