---
id: D-20261114-pj-da5f
title: "Next build scope is the horizon chart on real data for one site"
date: 2026-11-14T16:56:23Z
author: pj
decided-by: ai
status: accepted
mode: own
domain: scope & success criteria
task: T-20261114-pj-e01c
concepts: [scope, appetite]
supersedes: []
relates: [D-20261114-pj-a3b3, D-20261114-pj-9f04, D-20261114-pj-f369, D-20261114-pj-9e53, D-20261114-pj-de42]
ai: delegated-by-pj
---
# Next build scope is the horizon chart on real data for one site

## Context

`D-20261114-pj-a3b3` targets the full portfolio scope for Sunday 15 Nov, with the plan cut order only at a failed checkpoint. It is Saturday 14 Nov, about 18:00 local. Phase 0's exit is one site end to end on real data. The library pieces for that slice are on `scope/ops-skeleton`: kernel sky (`lunar_eval/ephemeris/spice.py`), a Site01 mask (`tests/test_dem_site.py`), the visibility series, and the score. The page a person opens does not use them. `api/app.py` returns a fixed mock and `web/index.html` is titled as a mock. `data/masks/` is empty and there is no `scripts/precompute.py`, so the 1 km cap from `D-f369` has not started. The plan's do-not-cut list keeps the horizon chart; the region map, deep search, and the public URL are earlier in the cut order.

## Framing

One next build scope for the only builder. Wall-clock work that can run overnight stays the following scope.

## Options considered

1. **A — 1 km cap (finish S2)**: assumes Sunday's map is the piece that must start computing tonight; consequence: about four hours of precompute, while the page stays a mock.
2. **B — Horizon chart on real data for one site (S8)**: assumes the do-not-cut demo is one site a person can see; consequence: the API and the existing chart consume sky, mask, series, and score. The cap waits until that slice runs.
3. **C — Deep search, region map, or first-person view**: assumes a later plan scope is next; consequence: those scopes read the cap, a stopping rule, or a viewer decision that is not recorded.

## Decision

**B.** The next build scope is the horizon chart on real data for one site. The site is Site01, the site the current end-to-end test already uses. Demo-site refinement stays deferred (`D-f369`).

## Rationale

Delegated by pj. AI's reason: the sky, the mask, the series, and the score already run for Site01, and the chart is on the plan's do-not-cut list, while the page still serves a mock. The 1 km cap feeds the region map, which the cut order can drop; it also needs a script that does not exist yet. Doing the visible site first still leaves tonight to start that cap.

## Checks raised

- The cap is the overnight job in the plan (~4 h). If the chart runs long, the cap slips past the evening → delegated; not answered by pj. Consequence below: start the cap the same night, after this slice runs.
- `score.py` already uses minimum normalized hour-slack and a layer-2 weight of 0, while `D-de42` still defers `score_layer1_quantity` and `score_layer_combination` → this scope shows the score the code returns and does not lock those values.
- `D-4ffe` still defers `ephemeris_library`, while the code loads SpiceyPy and the DE440 set → this scope calls that provider and does not lock the library.

## Values

| Name | Value | Notes |
|------|-------|-------|
| next_build_scope | horizon_chart_real_one_site | Plan S8, on real sky and mask |
| chart_site | Site01 | lat -89.46316, lon 222.51045; already in `tests/test_dem_site.py`. Refinement stays the deferred value in `D-f369` |
| following_scope | 1km_cap_precompute | Same night, after this chart runs; `D-f369` `precompute_demo` |

## Expected behavior and validation

AI's expectation (not pj's): this choice is wrong if, by Sunday morning, the page still cannot show Site01's mask, Sun and Earth, and score from the local kernels and DEMs, or if the chart work crowds out the 1 km cap so that it never starts on Saturday night.

## Consequences

- Build replaces the mock site payload with Site01's sky, mask, series, and score. The chart already in `web/index.html` is the view.
- The 1 km cap is the next scope after that slice runs, still Saturday night.
- Layer-1 quantity, layer-2 combination, the ephemeris library, the basemap, and the first-person viewer stay open records. This scope does not close them.
