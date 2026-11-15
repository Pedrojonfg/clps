---
id: D-20261115-pj-54f0
title: "Deep search: total_coverage plus default multi-start hill climb"
date: 2026-11-15T09:45:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-2cbd
concepts: [deep search over user ranges, search vs learned model, stopping rule / budget, silent incomplete search]
supersedes: []
relates: [D-20261111-pj-60ab, D-20261114-pj-9f04, D-20261114-pj-72bc, D-20261114-pj-9cc5, D-20261115-pj-48ee]
ai: options+critique
---
# Deep search: total_coverage plus default multi-start hill climb

## Context

S7 / P14 needs a concrete search method on the user-chosen space×time range. Cost probes on this branch (precomputed masks ~0.5 ms; SPICE sky ~0.4–0.5 s per site) show that full 1 km × 1 h enumeration is cheap for small boxes (~10×10 km × 7 d ≈ 1 min) and heavy for large ones (~50×50 km × 7 d ≈ 23 min). Discrete black-box analogues to gradient descent are neighbourhood local search / hill climbing; multi-start addresses multimodality. `D-72bc` left heavy ML/DL/RL as later intent only.

## Framing

Ship a defendable deep-search product mode for lunar-company users who can wait for a full grid pass, while defaulting to a cheaper optimized search that is still explainable.

## Options considered

1. **A — Total grid enumeration only**: assumes a day of compute is always acceptable; consequence: strong “grid optimum” claim, no fast default.
2. **B — Multi-start + hill climb only**: assumes the shortcut is enough; consequence: no built-in oracle mode.
3. **C — Two modes:** `total_coverage` (enumerate + ETA) and default `optimized` (multi-start + hill climb + ETA); start placement still to set.
4. **D — Coarse-to-fine only** as the v1 default.

## Decision

**C.**

## Rationale

pj (2026-11-15): Really, if the product is for lunar companies, they can afford to lose a day while the app evaluates every point brute-force, although I think a multi-start + hill climb should be a good choice (but we have to see where we put the starts, of course). Perhaps in deep-research mode we should offer a total-coverage mode (estimated … h) and a (default) optimized search (est. … h) that uses multi-start hill climb.

## Checks raised

- Hill climb may fail vs true grid optimum → accepted; compare optimized vs total_coverage when time allows; may miss the demo window but is easy to check.
- Start placement unspecified → deferred to the next decision on this task.
- Two modes widen the API → accepted for oracle/batch vs interactive default.

## Values

| Name | Value | Notes |
|------|-------|-------|
| deep_search_domain | user_range_on_1km_1h_grid | Same grid family as the 1 km cap / hourly windows |
| deep_search_modes | total_coverage; optimized | Both exposed in deep-research |
| deep_search_default_mode | optimized | |
| deep_search_total_coverage | enumerate_all_site_time_in_range | Show ETA before / during run |
| deep_search_optimized | multistart_hillclimb_on_grid | Show ETA; not a grid-optimum claim |
| deep_search_hillclimb_validation | deferred — compare optimized vs total_coverage when time allows | pj's falsification check; start placement → `D-e3cf`; neighbourhood → `D-1ebf` |

## Expected behavior and validation

pj (2026-11-15): That the hill climb would not work well; I suppose this can be tested easily by comparing total-coverage mode with the hill climb. Probably there will not be time for the demo, but luckily it is easy to check.

## Consequences

- Claims: `total_coverage` may say best on the enumerated grid; `optimized` must say best seen under the climb rule / budget.
- Next: lock start placement (and neighbourhood / stopping as needed).
- Do not treat Ridge/Lasso or classical GD as the v1 deep-search engine.
- `deep_search_methods_intent` ML/DL/RL later (`D-72bc`) remains future intent, not this v1.
