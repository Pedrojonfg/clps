---
id: D-20261117-pj-0c5e
title: "Surface-hazard limits are user inputs, checked like the schedule needs"
date: 2026-11-17T15:00:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261117-pj-c2d8
concepts: [hard layer-0 limits, hazard aggregation over the window, defaults versus per-mission figures]
supersedes: []
relates: [D-20261114-pj-5cfa, D-20261114-pj-f57e, D-20261114-pj-8764, D-20261114-pj-41a2, D-20261114-pj-050d, D-20261114-pj-8588]
ai: options+critique
---
# Surface-hazard limits are user inputs, checked like the schedule needs
## Context

The planner had a hard-coded maximum temperature (320 K, applied only when climatology data existed), no minimum, and a hard-coded minimum soil resistance of 0. pj (2026-11-17): hazards that enter the analysis should also be chosen by the user: maximum and minimum temperature and so on.

## Framing

pj understood hazards to behave like the normal needs (hard layer-0 limits), only excludable. That is how `score()` already treats them; what was missing is control and a minimum.

## Options considered (questions put to pj in chat)

1. **Rule**: fail if any hour of the window breaks a limit (strict, same as the schedule needs) versus comparing an aggregate (mean, p95).
2. **Defaults**: none; or 320 K max only; or per-template limits.
3. **Scope**: temperature only, or also minimum soil resistance.
4. **Units**: K, or K with a °C hint.

## Decision

pj's answers, verbatim in substance:
1. Strict, like the normal needs; hazards are the same, only excludable.
2. Default maximum 320 K; any limit can be removed or changed; **each mission template carries its own limits**.
3. Same for soil resistance (default minimum 0).
4. Kelvin, the engine's unit.

Implemented as:
- new limits `max_temperature_k`, `min_temperature_k`, `min_soil_resistance`, resolved as explicit request value > template value > global default; an empty value means no limit;
- the hazard aggregate gains `temperature_min_k` (coldest hour) beside `temperature_k` (hottest hour), so "any hour outside the range" equals "peak above the maximum or trough below the minimum";
- score failing keys: `temperature` (above max), `temperature_min` (below min), `dust`;
- the "Layer-B hazards in score" switch turns all hazard limits off;
- the minimum temperature has no default (no limit).

## Rationale

pj's own reading: hazards are needs with an off switch. Strict any-hour matches how night and no-Earth are judged.

## Checks raised

- Templates have **no sourced per-mission hazard figures yet**: every template currently carries the global defaults (320 K, no minimum, 0). The mechanism is in place; the numbers are a claims question for pj and must not be invented.
- The minimum temperature default was not stated: set to none by the AI.
- A single-value hazard payload counts as its own peak and trough.
- If a limit is set but the climatology has no data, no failure is raised and nothing is shown, as before; the gap-star rule (`D-f57e`) is unchanged.

## Values

| Name | Value | Notes |
|------|-------|-------|
| max_temperature_k_default | 320.0 | applied when data exists; removable |
| min_temperature_k_default | none | AI choice, not stated by pj |
| min_soil_resistance_default | 0.0 | removable |
| hazard_limit_rule | any_hour_outside_fails | via window max / min |
| hazard_limit_precedence | request > template > default | empty request value = off |
| temperature_unit | kelvin | UI and API |

## Expected behavior and validation

Wrong if a window with one hour above the maximum or below the minimum is still feasible, or if clearing a limit in the UI still applies the default. Tests: `tests/test_score.py` (minimum and in-range cases).

## Consequences

- API `/site` accepts the three limits as strings; templates list them; the planner's "Mission needs" fold has three new fields and the needs table gains hazard rows when data exists.
- Not covered: deep search (Region map) ignores hazards by default (`hazards_enabled` false there) and does not take these inputs; extending it is a separate decision.
