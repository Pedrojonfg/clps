---
id: D-20261115-pj-01b0
title: "UI look follows Blueprint strictly for now"
date: 2026-11-15T12:33:37Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: presentation
task: T-20261115-pj-7b5c
concepts: [design-system authority vs ad-hoc styling, silent AI-slop drift from half-following a kit]
supersedes: []
relates: [D-20261115-pj-cc6f, D-20261115-pj-bdaf]
ai: options+critique
---
# UI look follows Blueprint strictly for now

## Context

Portfolio UI had been ad-hoc CSS in `web/`. pj wants an industrial / ops look and named Palantir Blueprint as the authority so the interface does not drift into generic “AI” styling. Product surface is desktop-primary (`D-cc6f`).

## Framing

Pick a single visual authority for the near term; allow a later reopen if pj wants changes.

## Options considered

1. **A — Blueprint strict rule-of-thumb for now**: assumes the kit’s look matches the sector story; consequence: no parallel custom aesthetic until an explicit reopen.
2. **B — Custom industrial rules without adopting Blueprint**: assumes we can hold the look by hand; consequence: higher drift risk.
3. **C — Mix Blueprint with custom “premium” styling**: assumes selective deviation is fine; consequence: classic half-kit AI-slop hazard.

## Decision

**A — For now Blueprint is in charge and is the strict rule of thumb; pj may change later if he wants.**

## Rationale

"For the moment Blueprint is in charge, and later if I want to make changes I will. But for now Blueprint is in charge and it is the rule of thumb strictly."

## Checks raised

- Might not like how it looks → "That I would not like how it turns out — not a big deal."

## Values

| Name | Value | Notes |
|------|-------|-------|
| ui_design_authority | blueprintjs_strict | `@blueprintjs/*` principles and components as default |
| ui_design_deviation | not_until_explicit_reopen | No half-following / parallel aesthetic |
| ui_forbid_glassmorphism | true | From session brief; aligns with Blueprint ops look |
| ui_forbid_decorative_gradients | true | From session brief |
| ui_forbid_serif_display | true | From session brief |

## Expected behavior and validation

Wrong if pj disliked the resulting look — recorded as not a big deal / reopen later. Wrong if the build invents a second visual language beside Blueprint without a superseding decision.

## Consequences

- Desktop UI work (Tauri shell, `D-bdaf`) treats Blueprint as the chrome source of truth.
- Ad-hoc `web/` CSS is not the product look (`D-c973`).
- Exact colors / radius / dark theme tokens: `D-b6fe`.
---
