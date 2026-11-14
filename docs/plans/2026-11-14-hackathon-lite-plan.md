# CLPS site×time evaluator — Lite Plan (Day 1..2)

Window: Sat 2026-11-14 ~12:00 → Sun 2026-11-15 23:00 (UTC+1). People: pj (decider) + up to 3 agent lanes. Decider: pj. Challenger: n/a (solo). Project type: software/git, greenfield. Cycle position: bet / kick-off under a hackathon appetite.

Approval: **pending pj nod**. This file does not rewrite `D-20261114-pj-7e2a` or `D-20261114-pj-9f04`. It is a two-day bet. Portfolio ambition returns if the cycle ends with time left or after Sunday.

Data recommendation used: `docs/research/briefs/research-brief-data-viz-sources.md` (2026-11-14). That brief is engine-ledger input, not a Sunday must-have. This plan takes its **geometry rule** (visible iff body elevation clears the horizon at that azimuth) and its **honesty rules** (Horizons is not the loop; averages are not the date; no Horizons from the browser). It does not take SPICE + full PGDA masks + Cesium as the 48 h bar.

## Assumptions (material ones need a nod)

- **(Recommended confirm)** Deadline is end of Sunday 15 Nov 2026, local. No extension [Book ch07]. If the real submission clock is earlier, cut from the list below; do not add hours.
- **(Recommended confirm)** “Several people” means agent lanes, not teammates. pj is the only decider and the only merger. Agents do not reopen Team-locks.
- **(Recommended confirm)** Hackathon appetite overrides portfolio scope *for this window only*. Layer B (temperature, dust), deep search, trajectories, Mars, native mobile, and Cesium first-person are `~` or out. The product question in `D-20261111-pj-60ab` stays: scored evaluation under planner constraints, plus a local search if it is downhill in time.
- **(Recommended confirm)** The only allowed product flex is the **data fork** in D8. Resource availability changes the horizon model and the honesty of claims. It does not reopen “what question we answer” unless every real data path fails.
- **(Safe default)** Greenfield. No application code in the repo (verified 2026-11-14).
- **(Safe default)** Stack locked in D3. Demo must run from one command on a laptop. Public deploy is `~`.
- **(Safe default)** Chat language Spanish; this plan and code stay English (`docs/records/project.md`).

## Appetite and capacity

Fixed: Sunday 23:00. Variable: scope. Circuit breaker: reshape, do not extend [Book ch02, ch07].

Capacity [Inference]: one human across ~20 focused hours, focus factor 0.85 → ~17 h of pj attention. Agent lanes overlap that attention; they do not multiply the calendar. Critical path is clock time, not person-days. Reserve the last ~4 h (about 20% of the window) for integration, edge QA, and cuts. No new scope in that window.

## Outcome, no-gos

**Use case.** A technical viewer picks one of three south-pole presets and a time range, sets a few thresholds (max hours without sun, without Earth, optional “need both”), and sees (1) Sun and Earth elevation against the horizon used for the score, (2) the four visibility cases, (3) a score that is 0 when minima fail, with the rule written next to the number.

**Must-have outcomes**

- One real ephemeris fixture for at least one site (or an explicit non-claim if D8-D fires).
- Needs-adapted score + provenance (source, horizon model, step, kernel/DEM ids if present).
- One useful viz: the horizon / elevation timeline (custom chart). This is the picture that makes the score legible. Cesium is not this viz.
- At least two preset sites on the same contract, so “compare” is real.
- Local neighborhood on time (nearest feasible + nearby hours) if it is downhill by the midpoint checkpoint. If it is still uphill then, it is the first must-have to hammer — not deep search, which is already `~`.

**No-gos (this bet)**

- Loading a regional DEM in the browser, ray-tracing a grid at demo time, scraping QuickMap, calling Horizons from the browser (NASA CORS / fair use).
- Temperature, dust, PSR science claims, approach-corridor lighting, ΔV / trajectory optimization.
- Mars or a second body pack. A provider function signature is enough “body-agnostic”; no plugin framework.
- Custom lat/lon UI, auth, accounts, native mobile, educator skin, Cesium as the primary screen.
- Any sentence that sounds like ops certification or V2/V3 validation. Ceiling is V0.

**Scope confirm**

| IN (must) | OUT or `~` |
|---|---|
| Fixture + four-case timeline | `~` live network at demo time |
| Score + explained thresholds | `~` deep search over ranges |
| Custom elevation / horizon chart | `~` Cesium first-person, Trek basemap, public URL |
| Two preset sites (third is `~`) | `~` layer B; out: trajectories, Mars, regional DEM in the loop |
| Neighborhood **if downhill by midpoint** | Custom coordinates |
| Horizon **mask for named sites if the spike gets one** | Building masks over 80–90°S this weekend |

## Decision log [Inference]

Planning round: **ran inside this document** (solo, no meeting). Complexity gate fired: contracts unclear, novel geometry, portfolio-vs-hackathon conflict, spike territory [Inference]. Decider is pj. Co-creation here is this plan; consensus is not required.

| # | Decision | Class | Locked by | Constrains | Rationale |
|---|---|---|---|---|---|
| D1 | `SkySample`: `time_utc`, `site_id`, `sun_az_deg`, `sun_el_deg`, `earth_az_deg`, `earth_el_deg`, `sun_horizon_el_deg`, `earth_horizon_el_deg`. Visible iff `body_el > horizon_el` at that azimuth. Spherical fallback sets both horizon fields to `0`. | Team-lock | pj (pending nod) | engine, viz, fixtures, search | Same score code for mask and spherical; matches the data-viz brief |
| D2 | Score: input = samples + `{max_hours_without_sun, max_hours_without_earth, require_both, w_sun, w_earth, w_both}`. Infeasible → `score = 0`, `feasible = false`. If feasible, score = weighted fraction of hours in sun / earth / both, clamped 0..1, plus a breakdown. Gaps = longest run not visible. Step = 1 h. | Team-lock | pj (pending nod) | score, tests, UI copy | Shape is locked; weights inside the object are Autonomous |
| D3 | Python 3, package `lunar_eval`, FastAPI JSON, one static page. SpiceyPy allowed as the ephemeris library. No React, no Streamlit, no notebook as the demo. Cesium is `~` S9, not the score path. | Team-lock | pj (pending nod) | all code lanes | One stack; brief’s engine vs viewer split |
| D4 | Demo clock is a **committed fixture**. Horizons is a **server-side** `SmoothHorizonOracle` (cache, one request at a time, app `User-Agent`), never a browser call, never the request-path provider. Live flag off by default. | Team-lock | pj (pending nod) | provider, demo script | Brief + NASA fair use |
| D5 | Presets: Shackleton rim, de Gerlache rim, Connecting Ridge (PGDA 78 names). v1 ships two; third is `~`. Coords checked during the spike, not invented in the UI. | Team-lock | pj (pending nod) | sites file, copy | “Compare sites” needs two points on one contract |
| D6 | True score uses a **local horizon mask**. This bet does not ray-trace a region. A tiny per-site azimuth→max-elevation table is in if the spike produces it; otherwise spherical + D8-B claim. | Team-lock | pj (pending nod) | claims, spike | Brief: at the pole the terrain term dominates; appetite: no GeoTIFF in the loop |
| D7 | Validation ceiling V0. Claims name the fixture, horizon model, and (if present) kernel set / DEM id. Do not call a long-term average “illumination on this date”. | Team-lock | pj (pending nod) | README, UI footer | Brief + domain brief |
| D8 | Data fork (only legal product flex). See table below. pj picks the row when the spike ends; agents do not pick. | Team-lock | pj at spike exit | provider, claims, whether hourly score exists | Resources still unknown; the question is not |
| D9 | File owners in the ownership map. Search imports `score.py` and does not edit it. | Team-lock | pj (pending nod) | agents | Hotspot control |
| D10 | Neighborhood: time only, ±1 h to ±6 h on the same site. Site moves are a different scope and stay `~`. | Team-lock | pj (pending nod) | search | Small moves are the cheap flexibility from the challenge heritage |

### D8 fork (lock the row, do not improvise)

Order is the brief’s preference, then honesty, then “still a demo”.

| Row | Spike result (≤3 h) | What ships | Claim |
|---|---|---|---|
| A | SpiceyPy (or equivalent offline kernels) gives Sun/Earth az/el **and** a per-site horizon mask exists for ≥1 preset (even a coarse azimuth table, not a live DEM) | Hourly D2 score vs local horizon. Horizons used only as a handful of smooth-horizon checks, cached | “SPICE directions vs a precomputed LOLA/PGDA mask; V0 vs Horizons on the smooth case. Terrain in the score.” |
| B | Directions exist (SpiceyPy **or** one cached Horizons observer table) but no mask in time | Hourly D2 score with `horizon_el = 0` | “Smooth / spherical horizon. At the south pole the terrain term is missing; not an ops number.” |
| C | Only a coarse map (PGDA 69 / Trek illumination % or average Earth visibility), no hourly series | **Cut hourly score.** Ship a site comparator of published **averages**, labeled with the ~18.6 y span | Do not pretend it is the D2 score or “this date” |
| D | Nothing usable in 3 h | UI + D2 score on a **synthetic** series with a banner | “Not lunar ephemeris” |

Row C is the one that changes the product. It is allowed only because a time series does not exist. It is not a vote to drop `D-60ab` in general.

Horizons as the **engine** is not a winning row. If the spike only got Horizons, that is D8-B, not A.

## Spike

**Unknown:** in 3 h, can we produce hourly Sun/Earth az/el for one south-pole geodetic point **and**, if luck holds, a tiny horizon mask for that point?

**Owner:** agent lane Spike. **Timebox:** 3 h. **pj decides the D8 row at the end.**

**Try in this order, stop when the timebox ends:**

1. SpiceyPy + pinned generic kernels → az/el for one PGDA 78 named site.
2. A **small** mask: reuse or sketch azimuth→horizon elevation for that site (from a clipped DEM sample, a published profile, or an explicit stub file). Do not download a multi-GB mosaic into the app.
3. One Horizons observer request (`CENTER='coord@301'`, geodetic, `QUANTITIES='4'`) as SmoothHorizonOracle, cached, with contact `User-Agent`. Compare a few epochs to (1) if (1) exists.
4. 20-minute look at whether PGDA 69 / Trek layers are only averages (expected yes).

**Fallback:** D8-B, then C, then D. Do not start Cesium, QuickMap scraping, or a regional ray-tracer inside the timebox.

While the spike runs, engine and viz start on a checked-in synthetic `SkySample` file (D1). Nobody waits on NASA.

## Scopes

| ID | Scope | Owner lane | Hours (appetite) | Confidence | Critical path? | Reads / writes | Depends on | Must / ~ | Done looks like |
|---|---|---|---|---|---|---|---|---|---|
| S0 | Data menu spike | Spike | 3 | unknown | yes | writes `fixtures/spike-notes.md` + kernels/mask/table if any | — | must | D8 row chosen by pj |
| S1 | Four-case timeline for one site | Engine | 4 | partial | yes | writes `lunar_eval/timeline.py`, reads samples | D1 | must | Given samples, hours labeled both / sun / earth / neither using D1 visibility |
| S2 | Needs-adapted score | Engine | 3 | partial | yes | writes `lunar_eval/score.py`, `tests/test_score.py` | D2, S1 | must | Three hand scenarios from pj pass; infeasible → 0 |
| S3 | Horizon / elevation timeline | Viz | 4 | partial | yes | writes `web/` , reads `GET /timeline` | D1 mock from hour 0; real fixture after S0 | must | Chart of sun + earth elevation, horizon line if mask exists, case strip |
| S4 | Two preset sites | Engine | 2 | partial | yes | writes `fixtures/sites.json` entries; hotspot with pj | D5, S0 | must | Same UI, switch site, both use D1 |
| S5 | Nearest feasible + neighborhood | Search | 4 | unknown | no | writes `lunar_eval/search.py` only | D10, S2 | must **if downhill by midpoint**; else first hammer | From an infeasible hour, a nearby feasible hour or an honest “none in ±6 h” |
| S6 | ~ Third preset | Engine | 1 | known | no | appends one site | S4 | ~ | Third name on the switcher |
| S7 | ~ Deep search over a time range | Search | 6 | unknown | no | would extend search | S5 | ~ | Global max on one site — cut first among search extras |
| S8 | ~ Live SmoothHorizonOracle | Spike | 2 | unknown | no | server-side provider only | D4, D8-A or B | ~ | Demo still defaults to fixture; no browser call |
| S9 | ~ Cesium first-person or public URL | Viz | 3 | known | no | web or host; not `score.py` | S3 | ~ | Backdrop only; Sun direction from our state if present |
| S10 | Claims and demo script | pj | 2 | known | yes (last) | README demo section | D7, integrated slice | must | A stranger can run one command and read the V0 limit |

`~` items are outside load. They are not a way to rebalance.

### Risky bundle (S0–S2 are one product risk, split so lanes can move)

- **Problem:** planners cannot see, in one place, whether a south-pole hour fails their sun/radio minima.
- **Appetite:** ~10 h of lane work on the critical path, inside the Sunday clock.
- **Solution:** Places: site switcher, threshold form, timeline, score with breakdown. Affordances: pick preset, edit three numbers, read score and why. Connection: form → `POST /score` → D2; chart reads D1 samples. Horizon line on the chart when `horizon_el` is not zero.
- **Rabbit holes:** regional DEM in the loop (out), Horizons in the browser (out), Cesium as the score (out), layer B (out).
- **No-gos:** D4 browser rule, D6 regional ray-trace, D7, trajectories.
- **Depends on:** D1, D2, D8.

## Dependencies and critical path

| Pair | Class | Handling |
|---|---|---|
| S1–S2 vs S3 | contract-coupled | D1/D2 locked first; viz uses a mock fixture from hour 0 |
| S0 vs S1–S3 | sequential only for **real** numbers | Synthetic samples unblock code; spike unblocks claims |
| S5 vs S2 | sequential | Search imports score; does not edit it (D9) |
| S4 vs S3 | contract-coupled | Same JSON shape; sites file has one writer (Engine) |
| S10 vs all musts | sequential | pj writes the script on the integrated slice |
| S6–S9 | independent | Only after musts are downhill |

**Critical path:** D1/D2 nod → synthetic score tests (S2) in parallel with spike (S0) → D8 row → real fixture on the chart (S3) → second site (S4) → demo script (S10).

**Calendar floor:** ~14 h if D8 is A or B. Neighborhood (S5) sits beside S4, not on the floor. Row C shortens the path (no hourly score) and changes the claim. Row D keeps the path but forbids lunar claims.

## Phases

**Phase 0 (hour 0–3), parallel. Exit: D8 chosen, synthetic score test green, chart rendering the mock.**

- Spike lane: order in the Spike section. Stop at 3 h.
- Engine lane: `score.py` + tests from pj’s three scenarios. Visibility uses D1 (`el > horizon_el`). No network.
- Viz lane: static page on `fixtures/mock-timeline.json` matching D1 (include a non-zero horizon on at least one sample so the chart code is not spherical-only).
- pj: write the three scenarios (feasible, fails sun gap, fails “both”). Then read spike notes. Do not open a second research thread.

**Phase 1 (hour 3–12). Exit: one real site on screen with a true score, or D8-C/D explicitly adopted.**

- Engine: timeline + provider that reads the fixture from S0. Then second preset.
- Viz: swap mock for the real fixture; threshold form calls the API.
- Search: starts only after S2 tests are green. Time neighborhood only.
- pj: while Engine wires the fixture, study D10 on paper (one infeasible timestamp, which hour should win). That note is the acceptance test for S5.

**Phase 2 (hour 12 until T−4 h). Exit: two sites, demo command, S5 merged or cut.**

- Integrate each scope as it works. Main stays runnable.
- If S5 is still uphill here, cut it. Do not spend the evening on S7 or S9.

**Final window (last 4 h of Sunday).** Edge QA only: empty range, all-dark fixture, threshold of 0, site switch does not leak the other site’s samples, horizon line matches the model in the footer. Cut remaining `~`. Freeze copy to D7. No new scope. No extension.

## Assignments (draft)

| Person / lane | Profile | Owned scopes | Load (must-have hours) | Buddy | First independent slice | Notes |
|---|---|---|---|---|---|---|
| pj | decider, claims, score semantics | S10, D8 choice, three scenarios | ~6 h attention, not typed load | — | Three hand scenarios during Phase 0 | While a lane implements, pj prepares the **next** acceptance note, then reviews. Does not code hotspots in parallel with the owner |
| Spike | research | S0, then `~` S8 if A or B | 3 h | pj decides | SpiceyPy az/el for one site, then mask, then one cached Horizons check | Dies or becomes Search help after the timebox. Does not edit `score.py` |
| Engine | Python | S1, S2, S4 | ~9 h | pj on scenarios | `score()` tests on synthetic series | Heaviest lane. S5 is **not** this lane |
| Search | Python | S5 | 4 h, only if S2 is green | Engine (consult, not co-owner) | A failing series → nearest hour, using the public score function | Starts in Phase 1, not Phase 0 |
| Viz | web | S3 | 4 h | — | Chart from `fixtures/mock-timeline.json` | Starts in Phase 0 against D1. Cesium is S9, not this slice |

Imbalance check: Engine is heavy on purpose (one writer of the score). Search is a second Python lane so neighborhood does not land on the same person at the end. pj is not an implementation owner of S1–S5.

`~` not in the loads: S6, S7, S8, S9, layer B, trajectories.

## Ownership and collisions

| Area | Owner | Others may |
|---|---|---|
| `src/lunar_eval/score.py`, `timeline.py` | Engine | import only |
| `src/lunar_eval/search.py` | Search | — |
| `src/lunar_eval/providers/` | Spike, then Engine if S8 is cut | read fixtures |
| `fixtures/sites.json` | Engine | ask for a new id; do not edit in two lanes |
| `fixtures/mock-timeline.json` | Viz until real fixture lands; then Engine replaces samples, Viz keeps the file shape | shape is D1 |
| `web/`, `src/api/app.py` route list | Viz | Engine adds fields only via D1/D2 |
| `tests/test_score.py` | Engine | pj adds a scenario as a test case through Engine |
| `README.md` demo + claims | pj | lanes do not rewrite claims |
| lockfile / `pyproject.toml` | Engine | others request a dependency (SpiceyPy) in one small merge |
| kernels / mask fixtures | Spike | Engine reads; do not commit multi-GB GeoTIFFs |

Contracts to commit before parallel work: D1, D2, D3, D4, D9, D10. D8 is committed as a **procedure** now and as a **row** at hour 3.

Branches [Inference]: trunk-based. `scope/<id>-<name>`, lifetime under a day, merge when the slice runs. Main always serves the demo. One scope merged at a time. Feature flag only for server-side Horizons oracle (default off).

## Checkpoints

| When | Check | Pass | If failing |
|---|---|---|---|
| Hour 3 | Phase 0 | D8 row written by pj; mock chart up; score tests green | Take D8-B/C/D. Do not extend the spike |
| Hour 12 (mid) | Risky scopes over the hill | Real or fallback data on the chart; S5 uphill or downhill is an explicit call | Cut S5. Do not open S7 or S9 |
| T−4 h | Scope freeze | Two sites or a written reason for one; demo command drafted | Drop `~`, then S5, then the third site. Keep one real timeline + score + viz |
| Sunday 23:00 | Ship | A stranger runs one command; footer matches D7 | Ship the integrated slice. No extension |

Hill: S0 starts uphill and must be decided at hour 3. S2 should be downhill as soon as the three tests exist. S5 is the scope allowed to die uphill.

Sync: exception-driven. Speak up when a scope crosses the hill, blocks on another lane, or threatens D1/D2/D8. No status round.

## Cut order

1. `~` trajectories, Mars, regional DEM in the loop, layer B (already out — do not pull them back in).
2. `~` S7 deep search.
3. `~` S9 Cesium / second viz / public deploy.
4. `~` S8 live oracle.
5. `~` S6 third site.
6. **Hammer** S5 neighborhood if still uphill at hour 12.
7. Last resort: one site instead of two. Do this only if the chart is not integrated. Two sites on a fixture beat a search that does not run.
8. Do not cut: D2 score, one horizon/elevation chart, provenance sentence. If D8-C fires, the replacement comparator **is** the product; do not also pretend D2 ran.

## Risks

- SpiceyPy + kernels can eat the spike. The timebox and D8 exist for that. Horizons is the **check**, not the rescue engine to quietly promote to A.
- A spherical score at the pole is physically the wrong horizon (data-viz brief). D8-B is allowed only with that sentence in the UI.
- Portfolio decisions (`D-9f04`, layer B in, Cesium as the truthful camera) will feel “abandoned”. They are deferred, not superseded, unless pj writes a new decision record.
- Two agents editing `app.py` or `sites.json` will lose the evening. D9 is the prevention.
- Friendly UI is what the challenge text emphasizes and what `D-3c91` postponed. This bet keeps technical copy. That is a claims choice, not an accident.
- An ion token must not land in git if S9 is ever picked up.

## Book vs inference

- **[Book]** Appetite is the deadline; scope flexes; circuit breaker; vertical scopes; one owner; get one piece done; unknowns first; `~` cut first; done means the demo runs; no task lists handed to lanes; hill, not status theater.
- **[Inference]** Agent lanes as the N-person split; hour-level capacity; trunk branches; file ownership; D8 fork table; planning round collapsed into this file because there is one decider and no time for a meeting; neighborhood treated as must-have only while it stays downhill; data-viz brief mapped onto a 48 h cut without waiting for the engine ledger.

### Approval gate

| Person | Owned scopes | Load | First independent slice | OK? |
|---|---|---|---|---|
| pj | S10, decisions, scenarios | ~6 h | three hand scenarios | pending |
| Spike | S0 | 3 h | SpiceyPy az/el, then mask, then one Horizons check | pending |
| Engine | S1, S2, S4 | ~9 h | synthetic score tests | pending |
| Search | S5 | 4 h after S2 | nearest hour on a failing series | pending |
| Viz | S3 | 4 h | chart on the mock fixture | pending |

Decider sign-off: pending.
