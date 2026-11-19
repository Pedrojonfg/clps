---
id: D-20261118-pj-9413
title: "Window endpoints and durations: closed sample grid, pessimistic interval bounds"
date: 2026-11-18T16:45:11Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261118-pj-a670
concepts: [sample vs interval, pessimistic bound]
supersedes: []
relates: [D-20261114-pj-9cc5, D-20261117-pj-91c6, D-20261114-pj-7af3]
ai: options+critique
---
# Window endpoints and durations: closed sample grid, pessimistic interval bounds

## Context

An external audit (items 3, 14, 15) found that durations are computed as `number of samples x step` (`moonpark/visibility.py`: `longest_night_h`, `hours_sun_above_threshold`). A 24 h window sampled hourly counts 25 h; sampled every 10 min it counts 24 h 10 min. So the same requested window gives different totals depending on resolution, and a site can pass or fail a limit only because of the step (`D-20261117-pj-91c6` lets the user pick 10 min or 1 h). Local search window length was already fixed to elapsed time (`D-20261114-pj-9cc5`, PR #34).

## Framing

Samples are instants; durations are intervals between instants. A run of consecutive samples only bounds the true duration: it lasts at least from its first to its last sample and at most from the last opposite-state sample before it to the first opposite-state sample after it. Optimize for not accepting sites that cannot meet their requirements.

## Options considered

1. **A, count samples x step (current)**: assumes each sample stands for a whole step; consequence: window of 24 h counts 25 h (hourly) or 24 h 10 min (10 min).
2. **B, last minus first within the run**: assumes the run lasts from its first to its last sample; consequence: 3 dark hourly samples = 2 h.
3. **C, hole to hole**: assumes the run may fill the gap to the neighbouring samples; consequence: 3 dark hourly samples = 4 h.
4. **D, midpoint of B and C**: assumes position inside the gap is unknown; consequence: 3 h.

## Decision

**A closed grid with pessimistic interval bounds.**

- A requested day is evaluated at hours 0..23 of that day plus hour 0 of the next day. There is no separate "hour 24" point; it is the same instant as the next day's hour 0. The window length is last instant minus first instant (24 h), not a sample count.
- Every duration is measured by the bound that makes its requirement harder to meet.
  - Maximum limits (longest night, longest no-Earth period): upper bound, from the last lit instant before to the first lit instant after the run (option C).
  - Minimum limits (continuous lit time, total lit time): lower bound, last lit sample minus first lit sample of the run (option B).
- Runs touching a window edge are clipped to the window.

## Rationale

(Translated from pj's Spanish.) I would drop the 24 mark; if someone asks for a specific day, I would check from 0 to 23 of that day and 0 of the next. Interval maxima are not computed by counting but by subtracting the last index from the first, which should give 24 h even though 25 points are checked. For nights, I think it is best to subtract: be conservative and consider that the night lasts 4 h, since it is only known to last between 2 and 4 h. A false negative is better than a false positive. Every quantity is measured on the side that makes it harder to meet, so for light it is the last light index minus the first. This uncertainty, resolved by being pessimistic, can feed the probabilistic risk model. Clipping at the window edge: if you land on the 22nd, it does not matter whether the night started on the 21st at 15:00 or at 23:00; what matters is the time you are there.

## Checks raised

- "Conservative" flips for minimum limits (less light is the safe side) → pj: always measure on the side that makes the requirement harder; lit durations use last lit index minus first.
- Run touching a window edge would use an instant outside the window → pj: clip to the window edge.
- Error grows with step (up to 2 h at 1 h resolution, 20 min at 10 min) → pj confirmed.
- Criterion fixes only the safe side, not how much error is acceptable → pj confirmed.

## Values

| Name | Value | Notes |
|------|-------|-------|
| window_grid | closed: first and last instant both sampled; duration = last - first | |
| max_limit_duration_bound | upper (hole to hole) | night, no-Earth |
| min_limit_duration_bound | lower (last - first lit sample) | continuous lit, total lit |
| edge_runs | clipped to window | |
| single_sample_lit_run | 0 h | confirmed by pj |
| total_lit_aggregation | sum of the per-run lower bounds | confirmed by pj ("the most pessimistic indicator") |
| battery_interval_convention | pessimistic bound, as for the other durations | pj: "once again use pessimism" |
| threshold_equality_semantics | a minimum is met when equal (need at least N, have N: passes); a maximum is not met when equal (limit N, value N: fails) | pj, final answer: "minimum meets, maximum does not meet" |
| uncertainty_to_risk_model | the width between the two bounds feeds the risk model | pj; how it enters the formula is open |

## Later answers (pj, translated)

On equality: if I need at least 5 hours of Sun and there are 5, it is met; but if with 5 hours of night in a row the battery dies, then it dies. It depends on the case: a goal to reach is met on equality; a case to avoid fails. On the battery interval: use pessimism again. On a lit run of one sample: 0 hours is fine. On total light: the pessimistic sum of lower bounds. The width between the two bounds is used to feed the risk.

Equality, typed message: 72 hours equal to 72 hours is literally equal; if the limit is 72 hours it is a yes, and if what has to be obtained is 72 hours it is also a yes. Dictated message: if I need 72 hours of Sun and I have 72, it complies; and if I need less than 5 hours of night and I have 5, it does not comply, because n equals n; hitting the nail is hitting the nail; the probabilistic model will punish it as it sees fit, but the cut is where it is, and if you reach the cut you reach the cut.

Final answer, when asked which applies to a maximum: minimum meets, maximum does not meet.

## Expected behavior and validation

(pj, translated.) I cannot think of a clear falsifiability criterion. The criterion that prefers this choice over the previous one is that a false negative is better than a false positive. Implied check, not stated by pj: the same requested window must give the same total at 1 h and at 10 min, and the 1 h result must never be less strict than the 10 min one.

## Consequences

- `visibility.py` durations and the battery integration must follow this convention; regression test: same window at 10 min and 1 h gives window length 24 h and 1 h verdicts no more permissive than 10 min verdicts.
- Pessimism makes sites fail more often at coarse resolution; documented in README limitations.
- Not decided here: how threshold equality and the battery interval are handled.
- Equality rule changes the comparators: a maximum now fails at equality (night, no-Earth, maximum temperature use a strict "less than"; today they fail only when greater). Minimums are unchanged (they already pass at equality). The interface labels for maximum limits should read as "less than" rather than "up to".
