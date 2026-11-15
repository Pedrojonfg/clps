---
id: D-20261115-pj-b6fe
title: "UI tokens: Blueprint dark theme and kit defaults"
date: 2026-11-15T12:35:47Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-7b5c
concepts: [design-system authority vs ad-hoc styling, silent AI-slop drift from half-following a kit]
supersedes: []
relates: [D-20261115-pj-01b0, D-20261115-pj-50a5]
ai: recommended
---
# UI tokens: Blueprint dark theme and kit defaults

## Context

`D-01b0` set Blueprint as strict visual authority and deferred border-radius policy to this item. pj had earlier used “no rounded corners” as an example; he now prefers kit defaults over that override.

## Framing

When taste examples conflict with Blueprint defaults, Blueprint wins for now.

## Options considered

1. **A — Dark theme + Blueprint default radius (~2px) and kit color tokens**: follow the system.
2. **B — Dark theme + radius 0 override**: flatter; small deviation from the kit.
3. **C — Light theme**: less ops/control-room feel.
4. **D — Custom palette on top of Blueprint**: drift risk vs `D-01b0`.

## Decision

**A — Blueprint dark theme and Blueprint kit defaults (including radius); no custom radius override.**

## Rationale

Accepted the recommendation: let Blueprint be in charge. The zero-radius remark earlier was only an example; Blueprint should lead.

## Checks raised

- Would not look right or would not work well → "Not the end either. These decisions are fairly hard to falsify."

## Values

| Name | Value | Notes |
|------|-------|-------|
| ui_theme | blueprint_dark | Official dark theme classes / variables |
| ui_border_radius_policy | blueprint_kit_default | Settles radius; ~2px as shipped by Blueprint (`D-01b0` authority) |
| ui_color_tokens | blueprint_kit_colors | No parallel custom palette; forbid glass/gradients/serif remain in `D-01b0` |

## Expected behavior and validation

Wrong if dark + kit defaults looked bad or behaved badly in the desktop UI — pj: not catastrophic; decisions weakly falsifiable in advance.

## Consequences

- Implementers use Blueprint variables/classes; do not invent gold/frost/radial themes from the old static `web/` CSS.
- Reopening radius or palette needs a new decision (would touch `D-01b0` spirit).
---
