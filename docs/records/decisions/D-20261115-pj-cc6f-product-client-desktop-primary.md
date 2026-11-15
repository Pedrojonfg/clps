---
id: D-20261115-pj-cc6f
title: "Product client is desktop-primary on user hardware"
date: 2026-11-15T12:28:39Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261115-pj-7b5c
concepts: [client compute vs server compute, product desktop shell vs portfolio static web]
supersedes: []
relates: [D-20261115-pj-8c03, D-20261115-pj-2533, D-20261115-pj-c973]
ai: options+critique
---
# Product client is desktop-primary on user hardware

## Context

`D-8c03` put evaluator compute on the client and limited the remote role to horizon masks, but left `client_packaging` filled as `browser_static_demo` for a portfolio tranche (`D-2533`). pj states the product he cares about is a desktop application on the user's machine.

## Framing

Lock the primary product surface without forbidding a secondary UI that still keeps compute on the user's hardware.

## Options considered

1. **A — Desktop primary; other UI only if compute stays local**: assumes users run the evaluator on their machine; consequence: packaging targets desktop; browser (if any) is secondary and must not move compute to the VPS.
2. **B — Browser-first product (even with client-side compute)**: assumes the main experience is opening a URL; consequence: packaging and UX optimize for web.
3. **C — Fully local, no remote masks**: assumes the user brings or builds all masks; consequence: changes `product_remote_role`.

## Decision

**A — Desktop application on the user's hardware is primary. Another form (e.g. browser) is acceptable only if compute still runs on their hardware.**

## Rationale

"The ideal is a desktop application on their hardware. So if there is another form, like accessing via the browser, but it still runs on their hardware, we can accept that. But the primary is a desktop application on their hardware."

## Checks raised

- Users might lack suitable hardware or be unwilling to use it → "We have talked about that many times — that they would not have the hardware or whatever, or would not be willing to use it. It is something unlikely or little to lament."

## Values

| Name | Value | Notes |
|------|-------|-------|
| product_client_primary | desktop_app_on_user_hardware | Product surface; not the tranche static demo |
| product_client_secondary | allowed_iff_compute_remains_on_user_hardware | e.g. browser UI; must not move evaluator to VPS (`D-8c03`) |
| product_client_packaging | desktop_app_primary | Product packaging target. `client_packaging: browser_static_demo` in `D-8c03` / `D-2533` remains the *tranche demo* fill only; do not read it as the product |

## Expected behavior and validation

Wrong if target users lacked hardware good enough to run it or were unwilling to run local compute — pj: unlikely / little to lament. Wrong if a “browser” path silently moved evaluator load onto the project VPS.

## Consequences

- Later advise items (shell stack, Blueprint embedding) assume a desktop-primary product.
- `browser_static_demo` in `D-8c03` / `D-2533` is not the product packaging target; see `D-c973` for the static web role.
- Cesium/ion token handling inside a packaged desktop binary remains fog.
---
