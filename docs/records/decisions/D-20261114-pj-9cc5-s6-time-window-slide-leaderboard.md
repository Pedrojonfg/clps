---
id: D-20261114-pj-9cc5
title: "Local time search slides the window by ±h with a leaderboard"
date: 2026-11-14T19:19:35Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-03a6
concepts: [nearest feasible time, local neighborhood search]
supersedes: []
relates: [D-20261114-pj-5577, D-20261111-pj-60ab, D-20261114-pj-de42]
ai: options+critique
---
# Local time search slides the window by ±h with a leaderboard

## Context

S6 must define nearest-feasible (or best infeasible) time on the same site (`D-60ab`, `D-5577`). The planner works with a time window of length `h`, not only a single instant. Stub code ranked discrete precomputed windows by `|Δt|` without a recorded slide rule or leaderboard.

## Framing

Prefer a local, subjective preference for which nearby windows to try, with a clear comparison UI, without claiming an objective optimum.

## Options considered

1. **A — Single hours around an instant**: no full-window slide.
2. **B — Slide windows of length `h` from `[a−h, a]` through `[a+h, a+2h]`; prefer minimum distance to the original; ties indifferent; show a leaderboard**: local = about ± one window length in time.
3. **C — Sweep the whole planner date range**: closer to deep search in time.

## Decision

**B.**

## Rationale

Comparing windows should be cheap because much prior compute can be reused, though the exact optimization process is not yet clear. For local search, with initial window `[a, a+h]`, check all windows from `[a−h, a]` to `[a+h, a+2h]`. On a tie at the same distance, either is fine; otherwise the minimum distance to the original. In any case show a leaderboard with different cases, their scores, and what changes. These criteria are arbitrary in the sense of subjective preference rather than something objective, so no value judgment can be issued about them being right or wrong on objective grounds.

## Checks raised

- Subjective criteria do not excuse a broken implementation (wrong step, no reuse, unclear board) → noted; step and deterministic tie fixed below.
- Compute reuse is assumed, not designed → recorded as an implementation goal, not a proven fact.
- Many overlapping windows → hourly step bounds the set for v1.

## Values

| Name | Value | Notes |
|------|-------|-------|
| local_time_search_mode | slide_window_length_h | Initial `[a, a+h]` |
| local_time_slide_start | [a−h, a] | Inclusive start of the slide family |
| local_time_slide_end | [a+h, a+2h] | Inclusive end of the slide family |
| local_time_slide_step | 1 hour | Start time advances by 1 h |
| local_time_rank_primary | min_abs_distance_to_original_window | Distance between window starts (or equivalent stated in provenance) |
| local_time_tie_break | indifferent_earliest_for_stability | Preference indifferent; code picks earliest for stable tests |
| local_time_leaderboard | required | Cases, scores (incl. impossible companion when needed), what changed vs original |
| local_time_compute_reuse | implementation_goal | Prefer shared hourly series across overlapping windows; design in Build |

## Expected behavior and validation

These criteria are arbitrary subjective preferences; no objective value judgment can declare them wrong. Implementation can still fail if the slide, step, ranking, or leaderboard disagree with these values.

## Consequences

- `nearest_feasible_time` (and infeasible ranking via `D-5577`) operates over this slide family, not an ad-hoc list.
- UI shows a time-search leaderboard, not only a single pick.
- Deep search over arbitrary planner ranges stays S7 / P14.
