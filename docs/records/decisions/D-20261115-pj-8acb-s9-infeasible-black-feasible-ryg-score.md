---
id: D-20261115-pj-8acb
title: "Infeasible cells black with in-query badness dots; feasibles use UI score on RYG"
date: 2026-11-15T10:49:59Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-33ca
concepts: [absolute score color scale, infeasible display zero]
supersedes: []
relates: [D-20261114-pj-5577, D-20261115-pj-7227]
ai: options+critique
---
# Infeasible cells black with in-query badness dots; feasibles use UI score on RYG

## Context

The UI score is 0 when infeasible; companion remains for ranking (`D-5577`). S9 must make “cannot land” visually distinct from “poor but feasible.” pj chose the displayed score for the feasible gradient and black for infeasibles.

## Framing

First read of the map = feasible vs impossible; second read = how good among feasibles; optional third = relative badness among infeasibles in this query only.

## Options considered

1. **A — Color companion for everyone (including infeasible)**: assumes continuous badness on one scale; consequence: infeasibles may look merely “dark red.”
2. **B — Infeasible black; feasibles colored by UI score; optional in-query dots on black for relative badness**: pj's proposal.
3. **C — Hide infeasibles**: assumes clutter matters more than geography of impossibility; consequence: holes without explanation.

## Decision

**B.**

## Rationale

Infeasible cells are black so you can tell “do not land here” from “bad but feasible.” On black cells, a dot (or similar) can show relative badness within this query’s infeasibles. Feasibles use the displayed score on a red–yellow–green gradient.

## Checks raised

- Relative dots contradict “never stretch this query” for the main scale → accepted as an explicit exception **only** for infeasible markers; main feasible gradient stays absolute (`D-7227`).

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_infeasible_fill | black | Background must read as impossible |
| region_map_infeasible_marker | in_query_relative_dot | Relative among infeasibles in this response only |
| region_map_feasible_color_source | ui_score | Displayed `score`, not a silent companion swap |

## Expected behavior and validation

Would be wrong if users cannot tell impossible zones from poor-but-feasible ones; black background is the required distinction. Package risk: map feels misleading — accepted for now as in the batch falsification.

## Consequences

- Payload needs `feasible` (or equivalent) per sample for coloring.
- Legend must say infeasible dots are relative to this query.
