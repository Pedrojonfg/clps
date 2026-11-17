---
id: D-20261117-pj-7b2d
title: "Energy balance (battery state of charge) replaces the night-hours proxy in the score"
date: 2026-11-17T18:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: method & validation
task: none
concepts: [battery state of charge, solar array incidence, layer 0 / layer 1 score]
supersedes: []
relates: [D-20261114-pj-de42, D-20261114-pj-7af3, D-20261114-pj-f369, D-20261116-pj-b43a, D-20261115-pj-06cb, D-20261117-pj-91c6]
ai: options+critique
---
# Energy balance (battery state of charge) replaces the night-hours proxy in the score

## Context

The first-person view should show an approximate battery state, so a user can see why a score is bad. The
existing need `max_night_h` only caps the longest consecutive dark run; it assumes any light fully recharges.
pj's counter-example: 4 h night, 20 min of Sun, 4 h night — the battery most likely runs out, and the proxy
cannot see it. A reliable score needs an energy balance, which needs data the user (mission/company) provides.

## Decision

1. **Model.** Per time step: `SOC(t+1) = clamp(SOC(t) + (P_gen(t)·η_charge − P_load)·Δt, 0, C)`.
   `P_gen = P_peak · sun_fraction · cos(incidence)`; lunar surface has no atmosphere, so `P_peak` is constant.
2. **Inputs, tier 1 (required for the energy mode):** usable battery capacity C (Wh); array power at normal
   incidence (W); and **darkness consumption, given either as W or as survival endurance in hours**
   (`P_dark = C / endurance`). The hours form is offered because it is how missions state it (see Research).
3. **Inputs, tier 2 (optional, with defaults):** panel type (horizontal / fixed vertical + azimuth / vertical
   sun-tracking in azimuth); load when lit (W); minimum reserve (% of C); charge efficiency.
4. **Incidence** in the site's local horizon frame (the same frame as `SkySample` in `ephemeris/spice.py`:
   azimuth from north, elevation from local up): `cos i = max(0, sin(el)·cos(tilt) + cos(el)·sin(tilt)·cos(az − az_panel))`.
   Horizontal: `sin(el)`. Fixed vertical: `cos(el)·cos(az − az_p)`. Vertical tracking: `cos(el)`.
5. **Score, energy mode** (tier 1 filled). Lowest SOC over the window is the one scalar: `soc_min`.
   - Layer 0: `soc_min < reserve` fails with reason `battery` (replaces `night`). The line is the reserve, not 0:
     an empty battery means loss of power and communications and usually no restart (Blue Ghost, Odysseus,
     SLIM cut at 12 % to keep a restart chance). Default reserve 10 % of C (provisional, pj to confirm).
   - Layer 1: the risk product `R` gets a term `Φ((soc_min − reserve) / σ_soc)` in place of the night term, with
     `σ_soc` = 10 % of C (provisional; same figure as the validation tolerance below). `Φ` saturates, so margin
     beyond the uncertainty adds nothing more.
   - Bonus `B`: **battery surplus is not credited** (pj: the bonus already comes through Sun hours, Earth hours
     and temperature; extra battery is a consequence of more Sun). The night-slack term of `B` is dropped in
     energy mode; the Sun/Earth hour terms and the 40 % cap (`D-48ee`) are unchanged.
   - Unchanged: `no_earth` term and layer 0; `min_continuous_lit_h` stays as a requirement, computed without
     bridging. Layer-1 terms are still computed when infeasible (`D-5577`), so search keeps a gradient.
6. **No energy data → current behaviour** (`max_night_h` proxy and `bridge_h`), labelled as a proxy. The
   first-person indicator then shows "autonomy (estimated, relative to your Max night)", never a % of battery.
7. **`bridge_h` (decided by pj): only for users without battery data.** It is a gross substitute for the
   balance, so in energy mode it is not used and its field is hidden; it remains available in proxy mode.
   **Sun is asked as visibility (pj's framing).** The energy model only answers "do not run out of battery"
   and lives in the probabilistic layer; Sun in the planner is presented as *visibility*, not as power:
   - More visibility is always a bonus (the Sun-hours term of `B` stays as is).
   - `min_continuous_lit_h` stays, default 0 (not every mission needs it), and is labelled as a visibility
     requirement in the interface. No other change to its logic (layer 0 tag `lit`, `D-7af3`).
   - **New need `min_total_lit_h` (pj): minimum total hours of light in the window**, default 0 (no requirement),
     in hours (not % of window), next to `min_continuous_lit_h` as the second visibility requirement. Layer 0:
     `hours_sun_above_threshold < min_total_lit_h` fails with tag `lit_total`. Layer 1 (only when > 0): a term
     `Φ((hours − min_total_lit_h) / σ)` in `R`, with σ = 5 h (provisional, same as the continuous-lit σ of
     `D-7520`; tuned in the pre-search pass). It does not use `bridge_h`. Covers fragmented light that the
     continuous minimum would reject.
   - Energy and visibility are therefore not treated as redundant: the first is survival risk, the second is
     visibility value. Correlation between them is expected and is only checked in the pre-search tuning pass.
8. **First-person indicator:** small battery icon, Blueprint style, red/amber/green, next to the time label;
   interface details are decided separately.

## Out of v1 (decided by pj)

- Load that depends on the Earth link (comms power); the load is constant per mode.
- Initial state of charge other than 100 %; no warm-up before the window.
- Terrain slope under the lander: the site is taken as flat in its local horizon frame. Checked sensitivity: a
  vertical panel changes by ~cos(el ± δ) (≈ 0.4 % for δ = 5°, el = 1°), negligible; a horizontal panel goes as
  sin(el ± δ) and is strongly slope-sensitive (δ = 1° at el = 2° is ±50 %). Slope exists (PGDA LDSM, `D-06cb`)
  if the horizontal option needs it later.
- Moving platforms (rovers): the lander/platform is static.
- Panel dust and temperature derating; temperature effects on battery capacity and heater load.

## Research (2026-11-17)

Goal: (a) is there a published battery curve to validate against; (b) can tier 1 be filled from public data.

**(a) Published state-of-charge curves: none found.** Searches for Blue Ghost, Nova-C/IM-1/IM-2, Chang'e-3,
Chandrayaan-3, SLIM and a generic "lander power model validated against flight data" returned no SOC/voltage
telemetry over a night, and no flight-validated south-pole power model (only design studies and a student thesis
on a weather station, not validated). Only coarse events exist, usable as sanity points rather than curves:
- Blue Ghost M1 operated ~5 h after sunset until batteries depleted (not designed for night).
- VIPER: 50 h survival in low-power mode at start of life and 0 °C; 57 h on battery in thermal-vacuum test.
- SLIM: shut down at 12 % battery ~3 h after landing to keep a restart chance.
- IM-1 / IM-2: landed on their sides, batteries depleted for lack of array light (orientation matters).

**(b) Tier 1 availability, from public sources:**

| Mission | Battery | Array | Darkness figure |
|---|---|---|---|
| VIPER | 5,420 Wh (start of life, 0 °C) | 320 W per panel, 450 W corner | 50 h survival ⇒ ~108 W average (derived) |
| Nova-C (IM-1 FCC filing) | 1,554 Wh | 788 W max, 3 fixed body panels | not found |
| Blue Ghost M1 | not found | 400 W (Firefly, LPSC 2026); NSSDCA lists 450 W nominal / 650 W peak (sources differ) | ~5 h after sunset to depletion |
| Chang'e-3, Chandrayaan-3, SLIM | not found | not found | RHU/hibernation only, no figures |

Reading: capacity and array power exist for some missions; the darkness consumption is almost never published
as watts, but as hours of endurance, and the derived average includes heaters. Hence decision 2.

Sources: [VIPER mobility briefing (NTRS)](https://ntrs.nasa.gov/api/citations/20240013903/downloads/LSIC_2024-Tech%20Infusion_Panel-VIPER_Mob-HW.pdf),
[IM-1 FCC filing](https://apps.fcc.gov/els/GetAtt.html?id=266519),
[Blue Ghost M1 retrospective (LPSC 2026)](https://www.hou.usra.edu/meetings/lpsc2026/pdf/1958.pdf),
[Blue Ghost M1 (NSSDCA)](https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=BLUEGHOST),
[SLIM revival (Scientific American)](https://www.scientificamerican.com/article/japans-slim-mission-is-revived-on-the-moon),
[IM-1 lunar night update (Intuitive Machines)](https://intuitivemachines.com/post/im-1-lunar-night-update-farewell-odysseus).
The web searches were summarized by a search tool; the numbers above that are in the VIPER, FCC and Blue Ghost
PDFs were read from the documents themselves. Others are from search summaries and should be re-checked before
being quoted.

## Criteria for change

| Assumption | Wrong if… | Criterion |
|---|---|---|
| Constant load and capacity | The real mission's battery lasts markedly different hours than C / P_dark | Check the model against the coarse points above (VIPER 50 h, Blue Ghost ~5 h). If the model's endurance differs by > 10 % from the published figure with the same inputs, add temperature-dependent capacity/heater load. No published SOC curve exists to do better; if one appears, validate the minimum SOC against it. |
| Tier 1 is enough | Users cannot fill it | If, for the missions in the plan templates, tier 1 cannot be filled from public data for most, accept ranges with a visible warning. |
| Flat site | Horizontal panel on slope > ~1° | Use LDSM slope. |
| Sky azimuth for panels | A test finds the maximum of a fixed vertical panel is not at `az = az_panel` | Fix the convention; panel azimuth is geographic (from north), never the mirrored mask azimuth of `D-b43a`. |
| Layer 0 on SOC (reserve, σ_soc) | Verdicts of validated cases (S3/S4 fixtures, 5/50/70 h templates) flip without a physical reason | Recalibrate before shipping. |

## Open

- Values to confirm by pj: default reserve (10 %) and `σ_soc` (10 % of C); both enter the pre-search tuning
  pass of `D-7520`/`D-6ce5` together with β and the cap.

## Consequences

- `needs` and the planner form gain the tier 1/2 fields; `score.py` gains the SOC series and the two-layer terms.
- The payload carries a `soc` series (when energy data is present) for the first-person indicator and time strip.
- Needs a test with the 4 h / 20 min / 4 h case, which the old proxy passes and the balance must fail, and a
  test that a fixed vertical panel peaks when the Sun azimuth equals the panel azimuth.
