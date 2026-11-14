---
id: D-20261114-pj-5cfa
title: "Planner temperature and dust limits fail-close; core score view in UI"
date: 2026-11-14T15:49:47Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-d4ce
concepts: [minima and feasibility, layer-B in the score, provenance]
supersedes: []
relates: [D-20261114-pj-de42, D-20261114-pj-050d, D-20261114-pj-41a2, D-20261114-pj-3c91]
ai: options+critique
---
# Planner temperature and dust limits fail-close; core score view in UI

## Context

The two-layer score (`D-20261114-pj-de42`) left `score_surface_as_minima` open at P13. Temperature is the polar climatology (`D-20261114-pj-41a2`). The dust slot is soil resistance with PGDA slope (`D-20261114-pj-050d`). The planner sets limits on both in the use case (`D-9f04`).

## Framing

Surface limits behave like Sun and Earth minima: fail-closed zero. The UI still explains which surface minimum failed and offers a view of the score without those limits as layer-0 gates.

## Options considered

1. **A — Layer 2 only**: assumes temperature and dust limits rank but never zero; consequence: a site can fail thermal or soil limits and still show a positive score if sky minima pass.
2. **B — Layer 0 fail-close**: assumes violating a planner temperature or dust/resistance limit sets score to zero; consequence: same gate as visibility minima, with a breakdown naming the failing term.
3. **C — Temperature layer 0, dust layer 2**: assumes thermal survival is mandatory but soil resistance only ranks; consequence: asymmetric rules the planner must learn.

## Decision

**B.** Layer 0 fail-close for planner temperature and dust/resistance limits. UI names the failing minimum. A core score view is required when a surface minimum fails.

## Rationale

Yes, zero. In the UI, some signal of what failed — temperature or dust — and a button to see the core score.

## Checks raised

- Definition of “core score” not stated → kept B; deferred value with proposed display-only recomputation without surface layer-0 gates.
- Dust limit units must match soil resistance, not an atmospheric dust scale → kept B; `dust_planner_limit_units` deferred to planner input design.
- Regional map may lose contrast if many cells zero on surface limits → kept B; pj falsification accepts later bulk testing.
- Core view when sky minima already fail may confuse → kept B; show core primarily when surface limits are the layer that failed (implementation detail for S5/UI).

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_surface_as_minima | temperature_and_dust_fail_close_layer_0 | Settles deferral in `D-20261114-pj-de42` |
| score_surface_fail_ui | name failing minimum explicitly | Values include `temperature` and `dust` (soil resistance label in provenance) |
| score_core_view | required when a surface minimum fails | User-facing control, not a second persisted product metric by default |
| score_core_definition | deferred — same formula with temperature and dust evaluated only in layer 2 for this view; lock when S5/UI is specified | Proposal accepted pending implementation |
| dust_planner_limit_units | deferred — lock when planner input form is specified | No unified dust scale yet; must match `D-050d` resistance units |
| surface_limit_bulk_test | deferred — many-case test once dust scaling and planner inputs exist | Falsification: too many zeros would be problematic |

## Expected behavior and validation

The choice would be wrong if dust or temperature knocked down many decisions and became problematic. We can test with many cases later; first we need to see how dust scales and how the client inputs needs, because I do not know if a unified scale exists.

## Consequences

- S4/S5 apply layer-0 checks on climatology kelvin and soil resistance against planner limits before layer 1 and 2.
- Provenance on a zero score names whether `temperature` or `dust` failed (`D-3c91`).
- Slope, rock abundance and PGDA roughness are not separate layer-0 limits unless a later decision adds them.