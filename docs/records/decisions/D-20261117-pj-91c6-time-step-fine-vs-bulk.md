---
id: D-20261117-pj-91c6
title: "Time step is a user option (10 min or 1 h) in every mode; defaults differ by mode"
date: 2026-11-17T18:05:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: none
concepts: [time step, schedule, compute cost, ranking stability]
supersedes: []
relates: [D-20261117-pj-7b2d, D-20261114-pj-f369]
ai: options+critique
---
# Time step is a user option (10 min or 1 h) in every mode; defaults differ by mode

## Context

The energy balance (`D-7b2d`) needs steps short enough to see a short lit interval. The series is sampled
hourly today and the first-person view interpolates linearly between those samples. `SpiceEphemeris.sky` calls
SPICE twice per sample in a Python loop, so cost grows linearly with the number of samples; the search tries
many windows and sites. Cost has not been measured and depends on each user's machine, so no fixed time
budget can be written as a falsification criterion.

## Decision

1. **The step is a user option in every mode** (single-site evaluation, local search, deep/mass search):
   fine = 10 min, coarse = 1 h. The user decides what to spend; nobody is forced to either.
2. **Defaults:** 10 min for single-site evaluation, local search and the first-person / time-strip visuals;
   1 h for mass search and optimization. Both can be switched either way.
3. **Fine step on top of a coarse search:** when a search ran at 1 h, the candidates it returns are
   re-evaluated at 10 min before the score is shown, unless the user picked 1 h for the final score too.
4. **Beyond 10 min** (finer) may be offered later on request; not in this decision.
5. The step is a property of the schedule (`SCHEDULE_VERSION`) and travels in the payload.

## Criteria for change

- **Compute cost: no numeric criterion** (hardware-dependent). The user-selectable step is the answer; if the
  10 min default is too slow on a typical machine, vectorize `sky` before touching the default.
- **Ranking stability (proposed thresholds, to be confirmed by pj).** Take a fixed set of N real sites/windows
  (e.g. the 28-point suite of `D-f369`). For each, run the search at 1 h, keep the top-K, re-score at 10 min.
  Report: (a) how often the 10 min best candidate is inside the 1 h top-K (hit rate), and (b) how often the
  pass/fail verdict flips between steps. Proposed: reopen this decision if hit rate (K = 5) < 90 % or verdict
  flips > 5 %; then raise K, or make 10 min the default for deep search.
- **Does 10 min add information at all?** The Sun moves ~0.5°/h in azimuth and its disc is ~0.53° wide, and the
  mask has 0.5° bins, so light↔shadow transitions already span ~1 h. If the 10 min and 1 h results differ by
  less than the output error of the mask schedule itself (`D-f369`: longest night off by up to 1 h), the fine
  step brings smoothness but not information; document it and make 1 h the default everywhere.

## Consequences

- `visibility`, the payload and the frontend interpolation handle a variable step; hourly-only assumptions
  (`longest_night_h` counting samples as hours) must convert samples to hours.
- The interface exposes the step as a simple choice (fine / coarse) in each mode.
