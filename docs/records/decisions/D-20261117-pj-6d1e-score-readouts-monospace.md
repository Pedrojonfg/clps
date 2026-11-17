---
id: D-20261117-pj-6d1e
title: "Numeric readouts in Blueprint's monospace stack; the score hero shrinks"
date: 2026-11-17T15:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261117-pj-c2d8
concepts: [design-system authority, hero-metric pattern, tabular numerals]
supersedes: []
relates: [D-20261115-pj-01b0, D-20261115-pj-b6fe, D-20261117-pj-f19a]
ai: options+critique
---
# Numeric readouts in Blueprint's monospace stack; the score hero shrinks
## Context

pj (2026-11-17): the typography of the Feasible/Infeasible block "looks AI" and clashes with the rest of Blueprint. Audit: the app declares no font of its own; it inherits Blueprint's system stack (Segoe UI on Windows). What clashed was the 34 px bold score with a green tick badge, a generic hero-metric pattern.

## Framing

Keep Blueprint as the only visual authority (`D-01b0`) and fix the one block that departs from it.

## Options considered

1. **A — Keep the Blueprint stack, shrink the hero**: consequence: minimal change, still proportional text for numbers.
2. **B — A, plus Blueprint's monospace stack for numeric readouts**: consequence: columns of numbers align; reads as an operations panel.
3. **C — Bundle a custom font**: consequence: leaves Blueprint strict; would need a reopen of `D-01b0`.

## Decision

**B.** pj chose B: "it fits the idea of our product best".

## Rationale

Same system, no new font file; monospace is Blueprint's own stack and suits readouts.

## Values

| Name | Value | Notes |
|------|-------|-------|
| ui_text_font | blueprint_system_stack | unchanged |
| ui_numeric_font | blueprint_monospace_stack | score, needs table, leaderboard numbers |
| score_hero_size_px | 22 | was 34 |
| feasibility_tag | uppercase, 11 px, no icon | colour only for the state |

## Expected behavior and validation

Wrong if the score block still reads as a generic dashboard hero, or if monospace numbers look out of place in the leaderboard. Reopen with a new record.
