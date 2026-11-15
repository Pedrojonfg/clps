---
id: D-20261115-pj-c973
title: "Static web/Pages are not the product; desktop is the priority"
date: 2026-11-15T12:28:40Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261115-pj-7b5c
concepts: [product desktop shell vs portfolio static web]
supersedes: []
relates: [D-20261115-pj-cc6f, D-20261115-pj-2533, D-20261115-pj-4494, D-20261115-pj-8c03]
ai: options+critique
---
# Static web/Pages are not the product; desktop is the priority

## Context

`web/` and GitHub Pages (`D-2533`, `D-4494`) ship a static portfolio demo. `D-cc6f` makes the product desktop-primary. pj needs the role of those pages fixed so work does not treat the website as the product.

## Framing

Separate pitch/demo surfaces from the product runtime the owner wants to defend.

## Options considered

1. **A — Not the product; at most demo/pitch/docs; may change or drop; priority now = desktop works**: assumes static pages are a presentation aid; consequence: claims must not imply the product is the website.
2. **B — Static web is a supported product surface alongside desktop**: assumes two first-class UIs; consequence: sync cost; risk web ≠ desktop.
3. **C — Abandon static pages immediately as this decision**: assumes no browser channel for pitch; consequence: another pitch channel is needed now.

## Decision

**A — Current static pages may serve demo or pitch; they are not the final product. Whether to keep or change them can be decided later. What matters now is that the desktop application works.**

## Rationale

"Maybe we have to remove the pages that are there now — they can be fine for a demo or something, for pitching, but the final product and the product I care about is the desktop application. So the static pages — we will see whether we change them or not and what they can be for. But what matters right now is that the desktop application works. That is what matters right now."

## Checks raised

- The web experience could diverge a lot from the desktop app → "I don't know — that the web would be very different from the desktop application; I cannot think of much more risk, honestly."

## Values

| Name | Value | Notes |
|------|-------|-------|
| static_web_product_role | not_product | `web/` / Pages are not the product runtime |
| static_web_allowed_uses | portfolio_demo_pitch_docs | At most; may be changed or removed later |
| static_web_keep_or_delete | deferred — after desktop path is real | This decide does not delete `web/` |
| near_term_ui_priority | desktop_app_works | Over polishing static pages as product |

## Expected behavior and validation

Wrong if the public story treated the static site as the product users run, or if effort on Pages crowded out making the desktop app work. Secondary risk pj named: web UI drifting far from the desktop UI if both are kept without a clear hierarchy.

## Consequences

- `D-2533` / `D-4494` remain valid as tranche demo/docs hosting; their product reading is demoted by this record + `D-cc6f`.
- README and claims should describe desktop-primary product; static URL is optional pitch/demo.
- Build may later reshape or remove `web/` without reopening `D-cc6f`.
---
