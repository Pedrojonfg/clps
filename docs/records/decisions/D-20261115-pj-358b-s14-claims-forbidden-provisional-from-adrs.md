---
id: D-20261115-pj-358b
title: "S14 forbidden/provisional claims: no lies; ADR-derived list"
date: 2026-11-15T12:12:16Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-98c4
concepts: [claims honesty, hazard proxy, portfolio pack vs contest]
supersedes: []
relates: [D-20261115-pj-de70, D-20261115-pj-a988, D-20261115-pj-671e, D-20261115-pj-0ee7, D-20261115-pj-fe17, D-20261115-pj-06cb]
ai: options+critique
---
# S14 forbidden/provisional claims: no lies; ADR-derived list

## Context

Companion to `D-de70`. pj declined a taste-based show/hide list: honesty is mandatory; concrete bans come from existing ADRs.

## Framing

Do not contradict recorded decisions in public copy or UI.

## Options considered

1. **pj hand-picks every allowed sentence.**
2. **No lying; forbidden/provisional patterns derived from ADRs** (chosen), updated when tests/ADRs change.

## Decision

**No lying.** Forbidden or must-be-provisional patterns are those that contradict ADRs (technical inventory below maintained as Values). ADRs stay the honesty source for what each quantity is and is not.

## Rationale

What is forbidden or provisional is that we must not lie. The ADRs are already honest about what is decided, why, and what is and is not. I do not need to decide what is shown myself — total honesty; base on the ADRs and update as tests are proven.

## Checks raised

None beyond restating ADR conflicts.

## Values

| Name | Value | Notes |
|------|-------|-------|
| claim_forbid_mock_as_computed | true | `D-a988`, `D-3832` |
| claim_forbid_cesium_as_our_model | true | `D-671e`, `D-ac34` |
| claim_forbid_dust_as_lofting_rate | true | `D-050d`, `D-06cb` |
| claim_forbid_pgda69_validated_without_numbers | true | `D-fe17` |
| claim_forbid_s7_global_optimum_without_megatest | true | provisional until megatest (`D-0ee7`) |
| claim_forbid_xyz_closed_if_tests_unrun_or_red | true | `D-de70`, `D-41fa` |
| claim_provisional_prefix | provisional / planned / test exists | Public wording |

## Expected behavior and validation

Wrong if public copy states any forbidden row as a closed fact.

## Consequences

- README, UI one-liners, and S15 pack must pass this checklist.
- New ADRs that change a quantity’s meaning supersede the matching row via a new decision if needed.
