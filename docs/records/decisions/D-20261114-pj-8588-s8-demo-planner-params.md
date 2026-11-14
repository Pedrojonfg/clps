---
id: D-20261114-pj-8588
title: "S8 planner UI defaults: ten mission templates, percent lit thresholds, hazards toggle, error on failure"
date: 2026-11-14T17:34:22Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261114-pj-9e03
concepts: [needs-adapted score, scope]
supersedes: []
relates: [D-20261114-pj-aa58, D-20261114-pj-f369, D-20261114-pj-de42, D-20261114-pj-5cfa]
ai: options+critique
---
# S8 planner UI defaults: ten mission templates, percent lit thresholds, hazards toggle, error on failure

## Context

`D-aa58` requires live sky, cached masks, and user-chosen site, time, and needs. pj closed the remaining S8 parameter choices on 2026-11-14 before `/implementa`.

## Decision

pj's choices (synthesis):

1. **Mission templates:** about ten; numeric content researched from project sources (`D-f369` mission notes, CLPS/VIPER/Artemis references) and stored as named presets the UI can load.
2. **Light definition in UI:** percentage fields for now (not a slider yet).
3. **Shadow bridge:** default **5 h**, user-changeable (`D-f369` default).
4. **Layer-B in chart score:** **yes**, with a **disable** toggle.
5. **Pipeline failure in demo path:** return an **error with a visible warning**, not silent mock; mock remains only for explicit CI (`mock=1`).

## Values

| Name | Value | Notes |
|------|-------|-------|
| mission_needs_templates | ten named presets in `lunar_eval/planner_templates.py` | IDs and numbers in code; cite heritage in template description fields |
| demo_light_threshold_ui | percent_input | 0–100 maps to series fraction threshold |
| demo_bridge_h_default | 5 | Hours; user-editable |
| demo_hazards_default | enabled with toggle | `MoonHazards` when on; empty aggregate when off |
| demo_pipeline_failure | http_error_with_message | No silent fallback when real path requested; `mock=1` for CI only |

## Rationale

pj (2026-11-14 chat): templates (~10, agent researches); percentage for lit; bridge 5 h default changeable; hazards yes but disable; on failure error-warning for now.

## Expected behavior and validation

Too much demo latency would falsify `D-aa58`; unchanged.

## Consequences

- Implement planner API query params and UI form per `D-aa58`.
- Tests use `production_test_time_window` from `D-aa58` where a longer window is needed.