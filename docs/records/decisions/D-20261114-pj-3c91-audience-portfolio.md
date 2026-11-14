---
id: D-20261114-pj-3c91
title: "Audience: technical portfolio demo with planner-depth backend"
date: 2026-11-14T11:05:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: problem framing
task: T-20261114-pj-a1b2
concepts: [audience, portfolio]
supersedes: [D-20261111-pj-ea51]
relates: [D-20261114-pj-7e2a, D-20261111-pj-60ab]
ai: options+critique
---
# Audience: technical portfolio demo with planner-depth backend

## Context

`D-20261111-pj-ea51` targeted mission planners as primary users and educators/public via a friendly explainable UI, matching the Space Apps statement’s three audiences. Under solo portfolio framing (`D-7e2a`), the person who must be impressed first is a **technical reader of the demo** (hiring manager, peer engineer), not an educator track.

## Framing

Keep planner-grade depth. Default the UI toward a serious tool with strong provenance/explainability, not educator-first friendliness.

## Options considered

1. **A — Keep `D-ea51` dual default (friendly first)**: still optimizes for Space Apps audiences; consequence: polish budget spent on friendliness before depth shows.
2. **B — Portfolio-technical default**: primary audience = technical demo viewer; same backend depth; explainability required; “friendly educator mode” optional later.
3. **C — Planner-only, no explainability**: weaker as a portfolio piece (hard to show judgment).

## Decision

**B — Portfolio-technical default** (supersedes `D-ea51`).

## Rationale

Portfolio readers judge clarity of model, honesty of claims, and usefulness of the score/search loop. Explainability and provenance stay mandatory. Educator/public friendliness is no longer the default UI mode; it may return as an optional skin once the tool is solid.

## Values

| Name | Value | Notes |
|------|-------|-------|
| primary_user | technical_portfolio_viewer | Hiring / peer technical reader of the live demo |
| domain_persona | mission_planner | Depth bar for calculations and metrics (unchanged intent) |
| ui_default_mode | technical_explainable | Tool-first + provenance |
| ui_optional_later | friendly_educator_skin | Not required for v1 done |
| viz_modalities_intent | 2d_and_projective_3d | Intent; cut by scope |

## Consequences

- Friendly UI is no longer implied as Sunday stretch default from the old dual positioning.
- Claims should not present the product as educator-first pedagogy.
