# lunar-eval: landing site × time evaluator for the lunar south pole

lunar-eval answers one question for a lunar south-pole mission: **if I land
here, on these dates, will I have enough sunlight and enough line of sight to
Earth?**

You pick a site and a time window and describe what the mission needs, for
example "no night longer than 72 h" or "never more than 48 h without seeing
Earth". The tool then computes how the Sun and Earth move against that spot's
local horizon. It checks the mission's hard limits and scores how well the
site fits. It can also search nearby terrain, or a whole region, for better
spots and windows.

It is a solo portfolio project. The NASA Space Apps Challenge 2026 brief
[CLPS Lunar Mission Browser](https://www.spaceappschallenge.org/2026/challenges/clps-lunar-mission-browser/)
inspired the problem. It is not a contest submission, and it is not
affiliated with or endorsed by NASA.

**Browser demo:** [pedrojonfg.github.io/clps](https://pedrojonfg.github.io/clps/).
It runs the desktop interface in the browser with **mocked data only**: one
sample result, whatever the inputs. See [Limitations](#limitations).

## What it does

- **Local horizon, not a flat Moon.** Near the pole the Sun stays just above
  or below the horizon, so a nearby ridge decides whether you are lit. Each
  site gets a horizon mask built from NASA LOLA elevation models. A mask is the
  elevation of the skyline in every direction, seen from 2 m above the ground.
- **Sun and Earth geometry.** Sun and Earth positions come from NAIF SPICE
  kernels. They are checked against saved JPL Horizons tables. They are
  compared with the mask hour by hour to get the visible fraction of the solar
  disc and of Earth.
- **Mission-aware scoring.** The score works in two layers. First, a hard
  check: if a site breaks any of the mission's limits (longest night, longest
  Earth blackout, minimum continuous light) it scores 0. Feasible sites are
  then ranked by how comfortably they meet those limits. Ten built-in presets
  set typical thresholds, for example VIPER-style hibernation, an Artemis III
  surface stay, Blue Ghost-class or direct-to-Earth priority. You can also set
  every threshold by hand.
- **Surface hazards.** Optional hazard checks add surface temperature, from
  Diviner polar climatology by local solar time and season, and a slope-based
  soil-resistance ("dust") proxy.
- **Search.** A local search tries nearby points around the chosen site. A deep
  search covers a lat/lon rectangle and time range and returns a ranked
  leaderboard. You can export it as JSON or CSV.

### The desktop app

The desktop app is the main way to use the tool. It is built with Tauri,
React and Blueprint, and has four screens:

| Screen | What you get |
|--------|--------------|
| **New analysis** | Site, time window, mission preset or custom needs. Result: score, pass/fail per limit, Sun/Earth visibility over time, polar chart of the horizon with the Sun and Earth tracks. |
| **Past analyses** | Saved runs; reopen one or jump to its 3D view. |
| **3D first-person** | Look around from the landing site 2 m above the ground, with the mask and Sun/Earth tracks overlaid on a 3D Moon (Cesium). If the 3D view is not available, it shows a 2D horizon panorama instead. |
| **Region map** | Scores of a search run, drawn on a textured, orbitable Moon. |

Every result shows where its horizon mask came from: **computed** from terrain
data, or **mocked** (a stand-in curve). That way a demo is never mistaken for
real terrain analysis.

## How it is built

```
LOLA DEMs ──► horizon masks (per site, cached as tiles) ─┐
SPICE kernels ──► Sun / Earth az-el ─────────────────────┼─► visibility series ──► score ──► search
Diviner climatology + slope ──► hazards ─────────────────┘
```

- **Engine:** Python package `lunar_eval/` (NumPy, SciPy, rasterio, SpiceyPy).
- **API:** FastAPI (`api/`). The desktop app and the browser pages call it
  over HTTP.
- **Precomputed masks:** `scripts/precompute.py` builds masks over the polar
  cap and stores them as memory-mapped tiles with a parquet index. One overnight
  run at **1 km spacing** produced about 290,000 masks (~840 MB). Deep search
  runs on top of that set.
- **Desktop:** `desktop/` (Tauri 2 + React + Blueprint).
- **Browser pages:** `web/` (standalone planner, region map and first-person
  pages, also served by the API).

## Validation

The project only claims what has been checked:

| Check | Status |
|-------|--------|
| SPICE Sun/Earth azimuth and elevation match saved JPL Horizons tables | Automated test (`pytest`) |
| Longest night and longest lit period within 5 h of a 5 m-resolution reference, on a 28-point set | Automated test (`pytest`) |
| Score is 0 when a mission limit is missed, and above 0 when all are met | Automated test (`pytest`) |
| Short-night re-check on long-night sites | Script ready, not run yet |
| Comparison with NASA PGDA average-illumination maps | Script ready, not run yet |

Details and how to run each check: [`docs/validation.md`](docs/validation.md).

## Limitations

- **The browser demo is mocked.** It has no server, so it always shows the
  same sample result. Inputs and mission presets do not change it.
- **You need local data for real results.** Computed results need about 14 GB
  of local data: elevation models (~11 GB), hazard rasters (~2 GB), SPICE
  kernels and the precomputed masks. None of it is in the repo. Without that
  data the app runs in **mock mode**: the full interface and score logic work,
  but the horizon is a stand-in curve, and the app labels it as mocked.
- **Masks are not downloadable yet.** The 1 km mask set exists, but it is not
  published anywhere. To run deep search you have to generate it yourself
  (overnight run).
- **1 km mask spacing.** The precomputed set has one mask every 1 km. Single
  sites outside it are computed on demand. Small-scale terrain between grid
  points can be missed.
- **The desktop app needs the Python API running.** It talks to a local
  FastAPI server, so for now it runs in development mode next to that server.
  There is no packaged installer yet.
- **The 3D view needs a Cesium ion token** (free account) whose account has
  *Cesium Moon Terrain* (asset 2684829) added from the ion Asset Depot.
  Without both you get the 2D panorama.
- **Mission presets are approximations.** Preset thresholds are planning
  values based on public mission profiles. They are not official requirements.
- **Hazards are simple proxies.** Temperature comes from climatology, not a
  thermal model of your lander. The "dust" layer is a soil-resistance proxy
  from slope. It does not model dust lofted by the plume.
- **Not every check has been run yet.** The two independent comparisons above
  have their scripts ready but no results yet. Until they run, there is no
  claim of agreement with PGDA maps.
- **South pole only, Moon only.** The code leaves room for other bodies, but
  only the lunar south polar cap is built and tested.

## Try it

**In the browser (no install):** [pedrojonfg.github.io/clps](https://pedrojonfg.github.io/clps/).
There is no server behind it. Every run returns the same mocked sample result,
so it shows the interface and the flow, not real terrain analysis.

**Locally.** Requirements: Python 3.12+, Node.js, and Rust if you want the native window.

**1. Engine and API**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn api.app:app --reload   # serves on http://127.0.0.1:8000
```

**2. Desktop app** (in another terminal, with the API running)

```bash
cd desktop
npm install
npm run tauri dev
```

The native window needs the
[Tauri system prerequisites](https://tauri.app/start/prerequisites/). Without
them, run `npm run dev` and open http://localhost:1420 in a browser. You get the
same screens.

With no local data, keep **Mock** turned on in *New analysis*. You can still
try the whole flow: run an analysis, read the score and charts, save it, open
the region map.

**3. Real data (optional, large)**

```bash
scripts/fetch_kernels.sh      # SPICE kernels
scripts/fetch_dems.sh         # LOLA polar DEMs (~11 GB)
scripts/fetch_hazards.sh      # hazard rasters
python scripts/fetch_pcp_bins.py
python scripts/precompute.py  # 1 km mask cap (overnight)
```

Then turn **Mock** off to get computed masks for any south-polar site. Deep
search becomes available once the mask cap is on disk.

**3D view token:** create a free token at
[cesium.com/ion](https://cesium.com/ion/tokens), then in the app's dev console
run `localStorage.setItem('cesium_ion_token', '<token>')` and reload.

## What's next

- **Desktop release:** installable builds with the Python engine bundled, so
  you don't need to start a server by hand.
- **Finer masks over the whole cap:** move from 1 km to 100 m spacing over
  the full south polar cap.
- **Hosted masks:** publish the precomputed masks and serve them through an
  API. Then the app, and the browser demo, give computed results without the
  14 GB of local data.
- **Run the remaining validation:** the short-night re-check and the PGDA
  illumination comparison, with results published in
  [`docs/validation.md`](docs/validation.md).
- **Demo video** once the interface is final.

## Repo layout

```
lunar_eval/   engine: ephemeris, horizon masks, visibility, score, search, hazards
api/          FastAPI server
desktop/      desktop app (Tauri + React + Blueprint)
web/          standalone browser pages (planner, region map, first-person)
scripts/      data fetchers, mask precompute, validation scripts
tests/        pytest suite
docs/         validation notes, demo data notes, design records
```

The design history and the reasons behind each choice are in
[`docs/records/`](docs/records/).
