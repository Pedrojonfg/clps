---
id: D-20261115-pj-1a9e
title: "S12 done bar: scripts/tests exist; heavy run overnight"
date: 2026-11-15T12:06:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261115-pj-98c4
concepts: [success X/Y/Z, short-night regime, PGDA 69 averages]
supersedes: []
relates: [D-20261115-pj-39f3, D-20261115-pj-9ab3, D-20261115-pj-fe17]
ai: options+critique
---
# S12 done bar: scripts/tests exist; heavy run overnight

## Context

S12 covers short-night re-check (`D-39f3`) and PGDA 69 comparison (`D-9ab3`). Need a recorded “scope done” bar for this decide pass vs waiting for green overnight compute.

## Framing

Separate “spec + harness ready” from “numbers already in hand”.

## Options considered

1. **Done only when all validation numbers are green in CI.**
2. **Done when scripts/tests exist; heavy runs overnight** (chosen).
3. **Done when validation.md has final tables.**

## Decision

**Scripts/tests ready; overnight run.** S12 is done for this tranche when the scripts and tests to perform the short-night re-check and PGDA 69 comparison exist so they can be run overnight. Filling final numbers can follow that run; failing overnight tests are fixed before the final product.

## Rationale

The bar for S12 being done is that all the scripts and so on for the tests exist; we will run them at night. I think that is enough. Agreed with the checks; tests may fail and such, but we will fix that before the final product.

## Checks raised

- Claiming completed validation in README before results → agreed not to (`D-fe17`).
- Overnight red tests → accepted until final product; must be fixed by then.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s12_done_bar | scripts_and_tests_exist_for_short_night_and_pgda69 | Spec/harness gate |
| s12_heavy_run | overnight | Not required green at decide time |
| s12_final_product_gate | validation_tests_fixed_before_final | Failures OK interim only |
| s12_artifacts | docs/validation.md; tests/ or scripts/ for both checks | Paths may be adjusted as hygiene |

## Expected behavior and validation

Wrong if the final product ships with failing S12 validation tests or with README claims that need numbers that were never produced.

## Consequences

- Build stage implements harness first; overnight job fills `docs/validation.md`.
- S14/S15 copy stays provisional on PGDA 69 until results land.
