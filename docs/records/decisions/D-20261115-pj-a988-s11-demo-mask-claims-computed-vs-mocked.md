---
id: D-20261115-pj-a988
title: "Demo claims: overnight masks computed; rest mocked; full cap planned"
date: 2026-11-15T11:38:45Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-5200
concepts: [demo 1 km vs full 100 m spacing, public HTTPS demo honesty]
supersedes: []
relates: [D-20261115-pj-4494, D-20261115-pj-3832, D-20261115-pj-8c03, D-20261114-pj-f369]
ai: none
---
# Demo claims: overnight masks computed; rest mocked; full cap planned

## Context

The 1 km cap exists on disk from an overnight run; the live demo uses mocks (`D-3832`, `D-4494`). Docs and UI need honest wording about what was computed versus mocked and what the full-cap plan is for.

## Framing

Presentation / provisional product story for the portfolio demo, not a certification claim.

## Options considered

1. **Overnight-computed set claimed as computed; remainder mocked; state the full-cap plan and a future publish location** (chosen).
2. Claim the whole demo grid as computed.
3. Claim nothing computed; mocks only.

## Decision

**Say the masks computed overnight were computed; say the rest in the demo are mocked; say the project intends to compute the full set as the basis for the app, to be published at a location still to fix.**

## Rationale

pj: report the overnight-calculated ones as calculated; the rest as mocked; state the plan to compute everything because that would be the basis for the application, findable later where everything is published (“bla” TBD).

## Checks raised

- Falsification weak by design → recorded as provisional presentation; still must not call mocked data “computed”.

## Values

| Name | Value | Notes |
|------|-------|-------|
| demo_mask_claim_computed | overnight_cap_1km_on_disk | Cite `data/masks/cap_1km` / run facts in docs |
| demo_mask_claim_mocked | remainder_shown_in_demo | Per `D-3832` |
| demo_mask_claim_full_cap_intent | planned_as_app_basis | Not done this tranche |
| demo_mask_publish_location | deferred — set when public archive/URL exists | |

## Expected behavior and validation

pj: most of these are provisional / how to present the product, so no strong falsifier is seen. Still wrong if mocked series are labeled as computed, or if the full cap is implied finished.

## Consequences

- Docs and any demo copy must split computed vs mocked.
- Publish URL/path is a later fill-in, not a blocker for this tranche.
