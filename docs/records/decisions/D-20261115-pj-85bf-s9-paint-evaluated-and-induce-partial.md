---
id: D-20261115-pj-85bf
title: "Region map paints evaluated search points; induce unevaluated only under partial search"
date: 2026-11-15T10:49:59Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-33ca
concepts: [local-search candidate set, region 1 km grid, silent incomplete search]
supersedes: []
relates: [D-20261114-pj-72bc, D-20261115-pj-54f0, D-20261115-pj-c159]
ai: options+critique
---
# Region map paints evaluated search points; induce unevaluated only under partial search

## Context

S9 needs a region score map after local and/or deep search (`T-20261115-pj-33ca`). Local search evaluates a neighbourhood (`D-72bc`). Deep search has `total_coverage` (enumerate) and default `optimized` multi-start hill climb (`D-54f0`) that does not evaluate every cell. pj rejected painting only a fixed full 80–90°S grid up front in favour of painting what the search actually knows.

## Framing

Show honest coverage of evaluated site×times; when the search was partial, allow a softer induced layer so the map is not only scattered dots — without claiming those cells were scored.

## Options considered

1. **A — Local-search points only, always**: assumes S9 is a neighbourhood viz; consequence: no deep-range map.
2. **B — Full 1 km region grid every time**: assumes precompute or live score of the whole cap; consequence: cost/claims beyond one search.
3. **C — Paint evaluated points; induce unevaluated with higher transparency only when search was partial; paint all evaluated under total coverage**: pj's proposal.

## Decision

**C.**

## Rationale

After local search, paint the local-search points. After deep search, paint what was evaluated. If the search was partial (optimized / not every point), paint evaluated points and induce nearby cells with higher transparency as an indication of where the search moved; if every point was evaluated (total coverage), paint them all. Paint what we have information for; induce only in the partial case.

## Checks raised

- Induction is a method claim, not only UI; “ML” in chat maps to partial/`optimized` search (`D-54f0`), not a trained model → accepted; induce only under partial search, with higher transparency.
- Would be wrong if not viable → pj: it is viable, so no problem for now. Users may later say induced/interpolated map feels dishonest → not treated as a big problem yet.

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_paint_set | evaluated_search_points | From local and/or deep search results |
| region_map_induce_unevaluated | when_search_partial | Partial = not every cell in range evaluated (e.g. `optimized`) |
| region_map_induce_style | higher_transparency_than_evaluated | Exact alpha deferred to implement if needed |
| region_map_total_coverage | paint_all_evaluated | No induction layer required |

## Expected behavior and validation

Would be wrong if this were not viable — but it is, so no problem for now. Maybe users later say the induced/interpolated map feels dishonest; not treated as a big problem yet.

## Consequences

- Map payload must mark evaluated vs induced samples.
- Claims must not call induced cells “scored.”
- Exact induction algorithm (nearest, search-path prior, etc.) left to Build under this intent; if a new own choice appears, back-edge to Decide.
