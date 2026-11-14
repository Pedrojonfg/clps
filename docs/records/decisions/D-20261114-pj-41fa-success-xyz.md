---
id: D-20261114-pj-41fa
title: "Success X/Y/Z: Horizons, 5 h mask hours, fail-closed score; PGDA 69 later"
date: 2026-11-14T14:19:58Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-b63a
concepts: [success X/Y/Z, provenance]
supersedes: [D-20261114-pj-9f04]
relates: [D-20261114-pj-de42, D-20261114-pj-4ffe, D-20261114-pj-f369, D-20261114-pj-a3b3]
ai: options+critique
---
# Success X/Y/Z: Horizons, 5 h mask hours, fail-closed score; PGDA 69 later

## Context

`D-20261114-pj-9f04` left `success_xyz` deferred: the demo is defendable when the backend is useful under explicit X, Y, Z. The score shape is now `D-20261114-pj-de42`. Oracles already in the records: Horizons fixtures for smooth-horizon az/el (`D-4ffe`); 28-point mask test with 5 h tolerance on longest night and longest lit period (`D-f369`); fail-closed score (`D-de42`). PGDA 69 long-term illumination averages are an objective check named in `D-f369` and planned as S12 / P12, not yet given a product role.

## Framing

Pick three numbers that can run without a screenshot and that exist as soon as sky, mask and score exist. A 3D view can inspect; it is not a metric.

## Options considered

1. **A — Defer until S12**: assumes no numbers to defend until Sunday validation; consequence: the README cannot cite X/Y/Z yet.
2. **B — Horizons + 5 h on 28 points + score 0/≠0 on hand scenarios**: assumes those three oracles suffice from the first green tests; consequence: does not measure search or PGDA 69.
3. **C — B plus local search finds a feasible neighbour (or honest none)**: assumes the `D-de42` loop is part of “useful”; consequence: S6 must be green to claim it.
4. **D — One of the three is the PGDA 69 average-illumination match**: assumes a long-term mean is a success number; consequence: needs a long engine run; does not validate a specific date.
5. **E — 3D / chart judged by eye**: assumes a picture is the check; consequence: no CI, no 5 h bound.

## Decision

**B.** X/Y/Z are: (X) kernel Sun/Earth az/el against saved Horizons fixtures; (Y) longest night and longest lit period within 5 h of the 5 m reference on the 28-point set; (Z) score is 0 on a hand scenario that misses a minimum and not 0 when minima are met. PGDA 69 stays out of X/Y/Z and may be reopened at S12. Occasional 3D inspection is allowed and is not one of the three numbers.

Scope values from `D-9f04` are restated unchanged except `success_xyz`.

## Rationale

Option B, because it seems the most reliable from minute 1, and I don't see what option C adds. PGDA 69 stays out of X/Y/Z, but we can reopen it when S12 arrives.

## Checks raised

- Horizons ignores terrain → kept B; Y (mask hours) is the terrain check, not a duplicate of X.
- The 28 points had long nights (≥ 392 h); short-night error is unmeasured (`D-f369`) → kept B; short-night re-check stays in S12, not in Y.
- Z does not measure discrimination among feasible scores (`D-de42` falsification) → kept B.
- C (search) is not one of the three → kept B; pj did not see what C adds.
- 3D spot check is not a number → kept as optional inspection, not X/Y/Z.
- PGDA 69 average match (`D-f369`) is outside X/Y/Z → kept out; reopen at S12. Comparing a site over *n* years only matches the published map if *n* is the same ~18.6 y nutation cycle and the light definition matches theirs.

## Values

| Name | Value | Notes |
|------|-------|-------|
| scope_core | needs_adapted_score; explained_thresholds_and_provenance; useful_viz_set; local_neighborhood_search | Restated from `D-9f04` |
| scope_core_deep | deep_search_mode_over_time_space_ranges | Restated from `D-9f04` |
| scope_layer_b_surface | temperature; dust; related_site_hazards_as_modeled | Restated from `D-9f04` |
| scope_out_v1 | full_trajectory_optimization; native_mobile_app; mars_feature_parity | Restated from `D-9f04` |
| definition_of_done | defendable_portfolio_demo | Restated from `D-9f04`; “useful” is now the X/Y/Z below |
| success_xyz | horizons_azel; mask_hours_5h_28pts; score_fail_closed_hand | Settles the deferred value in `D-9f04` |
| success_x | kernel_azel_vs_horizons_fixtures | `D-4ffe`; smooth horizon only |
| success_y | longest_night_and_lit_within_5h_on_28_points | `D-f369` default tolerances |
| success_z | score_zero_on_failing_hand_scenario; nonzero_when_minima_met | `D-de42`; hand scenarios, not a 3D view |
| pgda69_in_xyz | false | Reopen at S12 / P12 |
| success_3d_spotcheck | optional_inspection_not_a_metric | pj's only suggested extra check |

## Expected behavior and validation

I cannot think of a way to falsify this choice, beyond perhaps adding some occasional 3D visual check by eye.

## Consequences

- Spike K / S1, the ported 28-point mask test, and S4 hand scenarios are the evidence for X, Y and Z. S12 may add the PGDA 69 fraction comparison without changing these three until that decision is reopened.
- This supersedes `D-20261114-pj-9f04` so `success_xyz` is not both deferred and set. Portfolio scope is restated, not replaced.
- Claims in S14 cite these three numbers and their provenance; they do not cite a screenshot as validation.
