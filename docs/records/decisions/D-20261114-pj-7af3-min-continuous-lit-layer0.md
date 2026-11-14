---
id: D-20261114-pj-7af3
title: "Layer-0 minimum on longest continuous lit period (min_continuous_lit_h)"
date: 2026-11-14T18:02:27Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-8138
concepts: [minima and feasibility, visibility series]
supersedes: []
relates: [D-20261114-pj-de42, D-20261114-pj-f369, D-20261114-pj-9e53, D-20261114-pj-8588, D-20261114-pj-41fa]
ai: options+critique
---
# Layer-0 minimum on longest continuous lit period (min_continuous_lit_h)

## Context

S4 fail-closed minima already gate on longest night, longest gap without Earth, optional simultaneous Sun+Earth, and surface limits (`D-de42`, `D-5cfa`). S3 computes `longest_lit_h` from Sun fractions with the user light threshold and shadow bridge (`D-f369`, `D-8588`). The horizon chart shows lit periods but the score ignored them until this task.

## Framing

Whether a mission that needs a minimum block of useful sunlight is marked infeasible the same way as night and Earth gaps.

## Options considered

1. **A — Informational only**: assumes lit continuity is for the UI; consequence: score can be feasible while failing a real power-DTE need.
2. **B — Layer-0 gate on `longest_lit_h` with `min_continuous_lit_h` in needs; default 0**: assumes zero means “no requirement”; consequence: planner must raise the minimum when the mission cares; same thresholds and `bridge_h` as the series fed to the score.
3. **C — Mandatory positive default**: assumes every template must state a lit minimum; consequence: stricter out of the box, more UI work on every template.

## Decision

**B.**

## Rationale

“Yes, of course. Default 0, inside needs.”

## Checks raised

- Wrong `longest_lit_h` would make this gate misleading → pj: that would mean the metric or proxy is wrong; the bug would belong to earlier visibility decisions (`D-f369`, S3), not to adding this minimum.
- Default 0 hides missions that need lit unless the user sets it → accepted; explicit opt-in.
- `longest_lit_h` is Sun-only today → accepted; Earth lit stays on `longest_no_earth_h` / `any_both`.

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_min_continuous_lit | layer_0_fail_closed | Infeasible when `longest_lit_h < min_continuous_lit_h` |
| needs_field | min_continuous_lit_h | Alongside `max_night_h`, `max_no_earth_h`, `require_both` |
| min_continuous_lit_h_default | 0 | No lit-period requirement until the planner sets it |
| lit_metric_source | longest_lit_h from same S3 series | Same `sun_threshold`, `bridge_h` as visibility for that request |
| failing_breakdown_tag | lit | Listed in `breakdown.failing` when the minimum fails |

## Expected behavior and validation

If this choice is wrong, it would be because `longest_lit_h` is miscalculated or a bad proxy—but pj treats that as failure of earlier visibility decisions, not of wiring this minimum. With default 0, a mission that needs continuous sun but leaves the field at 0 would still score feasible on lit (user error, not a silent engine bug).

## Consequences

- S4 `score.py`, planner needs/templates, API validation, and tests gain `min_continuous_lit_h`.
- Z scenarios in `D-41fa` should include a hand case that fails on `lit` when the minimum is raised.
- Layer-1 assurance and the full risk model remain open (`D-de42` deferred values).