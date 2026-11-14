---
id: D-20261114-pj-aa58
title: "Interactive demo: live sky, cached DEM mask, user date window and needs templates"
date: 2026-11-14T17:22:24Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261114-pj-9e03
concepts: [scope, presentation]
supersedes: []
relates: [D-20261114-pj-da5f, D-20261114-pj-4ffe, D-20261114-pj-f369, D-20261111-pj-60ab, D-20261114-pj-de42, D-20261114-pj-9f04]
ai: options+critique
---
# Interactive demo: live sky, cached DEM mask, user date window and needs templates

## Context

S8 shipped a fixed `GET /site` payload (Site01, 24 h from 2027-01-01) as a portfolio shortcut (`D-da5f`). pj states that is not the intended product shape: the planner should pick coordinates, dates, and needs in the UI; Sun and Earth must be computed on request from local kernels (`D-4ffe`); the topographic mask should come from cached on-disk data for the demo site so the demo does not spend time recomputing it (`D-f369`). Regional 1 km precompute remains for the map and search, not for precooking sky tracks.

## Framing

Separate **end-user demo** (interactive, live geometry) from **production testing** (a longer fixed window for richer automated tests).

## Options considered

1. **A — Precooked sky and series in the API**: fast first paint; contradicts `D-60ab` and learning value of local kernels.
2. **B — Live sky + cached mask + user-chosen site, time window, and needs in the UI; mission need presets; demo button only presets coordinates**: matches pj's description; mask from disk cache; compute sky/series/score per request.
3. **C — Everything on demand including mask**: no cache; risk of unacceptable latency at new sites.

## Decision

**B.**

## Rationale

"The DEM mask does come cached, so for the demo it comes from data on disk and we do not waste time computing it. But because the rest is computed on the spot, it does not come from disk — it is done live (for example letting demo attendees pick the day and needs; for needs we can create selectable templates, like average CLPS, VIPER, and other famous mission names). If as part of the production process — not the final product — we need a fixed window for testing, I would use a somewhat longer stage so tests have more substance (for example the first week of January 2027)."

## Checks raised

- S8 code hardcodes time and needs → accepted; follow-up build aligns API/UI with this record (`T-9e03` audit note).
- Mission template names and numeric thresholds → deferred until presets are specified.
- Latency at arbitrary south-pole coordinates without a cached mask → falsification below; revisit if demo exceeds acceptable wait.

## Values

| Name | Value | Notes |
|------|-------|-------|
| demo_horizon_mask | cached_on_disk_when_available | No mask recompute in the demo path when the site is already in the dataset |
| demo_sky_and_series | compute_on_request | Local kernels; not precooked for the demo |
| demo_ui_site | user_coordinates_south_pole_plus_demo_preset_button | Preset button sets example coordinates; pj explains precompute in copy |
| demo_ui_time | user_selected_day_and_time_window | Not server-default hardcoded for product |
| demo_ui_needs | editable_plus_mission_templates | Templates include CLPS-average and VIPER-style labels; settled in D-20261114-pj-8588 |
| production_test_time_window | 2027-01-01 through 2027-01-07 UTC | Fixed window for automated tests, not the user-facing default |
| demo_sky_not_preloaded | true | Fixtures in repo remain test oracles only |

## Expected behavior and validation

"That there would be too much latency in the demo."

## Consequences

- Portfolio UI work must add controls for coordinates, date/window, and needs (with templates).
- API must accept planner inputs and compute sky/series/score per request; cached masks only.
- Tests should prefer the first week of January 2027 where a longer window helps coverage.
- The current S8 `/site` shortcut is technical debt until this shape lands.