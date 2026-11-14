---
id: D-20261111-pj-60ab
title: "Product question: scored site-time evaluation under planner constraints"
date: 2026-11-11T15:39:38Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: problem framing
task: T-20261111-pj-c84f
concepts: [user job, four visibility cases]
supersedes: []
relates: [D-20261111-pj-ea51, D-20261114-pj-3c91, D-20261114-pj-9f04, D-20261114-pj-b8d3]
ai: options+critique
---
# Product question: scored site-time evaluation under planner constraints

## Context

Challenge statement asks for rapid comparison of landing sites and dates via Sun/Earth vs local horizon (power and DTE). Owner positioning (`D-20261111-pj-ea51`) targets planner-depth backend. This decision fixes what *question* the product answers for that planner.

## Framing

Optimize for decision support under explicit feasibility constraints and preferences, not visualization alone. Score definition and search details remain for later method decisions.

## Options considered

1. **A — Compare only**: assumes value is in visual site/date comparison; consequence: no automatic score/search.
2. **B — Score + constrained search**: assumes a reliable score from thresholds/weights and useful local/global search; consequence: more method/validation work; 48 h risk.
3. **C — Hybrid: compare first, search later**: assumes comparator ships first; score/search when defendable; consequence: closer to statement wording for early cut.

## Decision

**B — Score + constrained search** (including a “deep research” mode over time–space ranges). Visualizations accompany the workflow; usefulness over polish.

## Rationale

The planner gives date and time plus how flexible they are on each output (for example a maximum time without light, a maximum without radio, a need for both at once, and other conditions such as generally valuing x or y more with certain thresholds). They get a score (which can be zero if minima are not met, in which case an optimization over the input parameters — time and date — looks for the nearest case where the minima are met), and nearby values are inspected to see whether any yields a substantial improvement. On top of that there is a deep-research mode (name TBD) in which they specify one or more time–space ranges and a global maximum is sought (all of these score pieces must be defined carefully, and should relate to staying as far as possible from the thresholds, plus general score goals such as maximizing sun, radio, and the both-at-once case). All of this comes with visualizations that look good but above all are very useful (which ones are useful must be chosen carefully).

## Checks raised

- Local search never conclusive, or no way to build a reliable score from needs → then this product question would be wrong (fall back toward compare-only / hybrid).
- Statement does not require a recommender → claim and 48 h scope must separate core comparison capability from search layers.

## Values

| Name | Value | Notes |
|------|-------|-------|
| product_question | scored_evaluation_under_constraints | Planner inputs site/time + flexibility/thresholds; output score + alternatives |
| score_on_minima_fail | zero_then_search_nearest_feasible | When minima fail, optimize date/time inputs toward nearest feasible |
| local_neighborhood_scan | required | Inspect nearby values for substantial score gains |
| deep_search_mode | required_intent | Global max over user-specified time–space range(s); name TBD |
| score_formula | deferred — method decision (metrics + recommender) | Must encode distance-to-thresholds + sun/radio/both objectives |
| visualization_set | deferred — scope / presentation | Prefer usefulness over aesthetics |

## Expected behavior and validation

This choice would be wrong if local search were never conclusive, or if there were no way to generate a reliable score grounded in the planner’s needs.

## Consequences

- Metrics decision must define the score and minima.
- Recommender decision must define neighborhood, deep-search ranges, and stopping rules.
- Scope decision must say what ships in 48 h vs stretch (score vs deep search vs viz set).
- Claims must not present search quality as ops-certified without matching validation level.
