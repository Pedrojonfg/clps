---
id: D-20261115-pj-50a5
title: "Blueprint via React in the Tauri webview"
date: 2026-11-15T12:35:46Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: architecture
task: T-20261115-pj-7b5c
concepts: [embedding a data-dense toolkit inside a desktop shell, design-system authority vs ad-hoc styling]
supersedes: []
relates: [D-20261115-pj-01b0, D-20261115-pj-bdaf, D-20261115-pj-b6fe]
ai: recommended
---
# Blueprint via React in the Tauri webview

## Context

`D-01b0` requires Blueprint as the strict UI authority. `D-bdaf` hosts the UI in a Tauri webview. The adoption path must match how Blueprint is meant to be used.

## Framing

Prefer the path most compatible with the library and with a dense planner UI, over a thinner CSS-only subset.

## Options considered

1. **A — React + `@blueprintjs/*` in the Tauri webview**: full kit as documented.
2. **B — CSS API only**: less stack; incomplete components; more fragile markup.
3. **C — Another UI kit**: conflicts with `D-01b0`.

## Decision

**A — React “by the book” with official Blueprint packages inside the Tauri webview.**

## Rationale

Accepted the recommendation: most compatible with the library and with what he wants to do; reliable; fine; simple/clean enough.

## Checks raised

- Would not look right or would not work well → "Not the end either. These decisions are fairly hard to falsify."

## Values

| Name | Value | Notes |
|------|-------|-------|
| ui_toolkit_stack | react_blueprintjs_in_tauri_webview | `@blueprintjs/core` (+ icons; other packages as needed) |
| ui_toolkit_css_only | false | Not the product path |
| ui_front_location | deferred — repo folder/layout at build | Hygiene / advise at implement time |

## Expected behavior and validation

Wrong if the React+Blueprint-in-Tauri path looked bad or worked poorly in practice — pj: not catastrophic; little further falsification.

## Consequences

- Build introduces a JS/TS front for the desktop app; Python remains the evaluator (`D-8c03`).
- Tokens/theme follow `D-b6fe`.
- Static `web/` HTML is not this stack (`D-c973`).
---
