---
id: D-20261115-pj-bdaf
title: "Desktop shell is Tauri"
date: 2026-11-15T12:33:38Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: dependencies & ops
task: T-20261115-pj-7b5c
concepts: [embedding a data-dense toolkit inside a desktop shell, product desktop shell vs portfolio static web]
supersedes: []
relates: [D-20261115-pj-cc6f, D-20261115-pj-01b0, D-20261115-pj-8c03]
ai: recommended
---
# Desktop shell is Tauri

## Context

`D-cc6f` makes the product a desktop-primary app on user hardware with local compute (`D-8c03`). The UI look will follow Blueprint (`D-01b0`). A packaging shell is needed so the app is an installed window, not “the website”.

## Framing

Prefer a reasonable binary size and local compute over a maximal web-runtime bundle, without abandoning a Blueprint-capable web UI inside the window.

## Options considered

1. **A — Electron**: Chromium packaged + Node; mature; heavy on disk/RAM.
2. **B — Tauri**: native shell + webview; lighter binary; younger ecosystem.
3. **C — Qt (or similar native)**: classic desktop UI; far from Blueprint React.
4. **D — Python GUI / PyWebview without a product shell**: fast prototype; weaker packaging story.

## Decision

**B — Tauri.**

## Rationale

Accepted the recommendation: reasonable binary and local compute; no need for something more extreme.

## Checks raised

- Could cause problems in use (pj not sure which, not an expert) → recorded as expected-behavior risk; revisit if packaging or webview/Python bridge blocks the demo.

## Values

| Name | Value | Notes |
|------|-------|-------|
| desktop_shell | tauri | Product packaging shell |
| desktop_shell_ui_host | webview | Hosts Blueprint UI |
| desktop_shell_compute | local_with_python_bridge_or_sidecar | Evaluator stays on user machine (`D-8c03`); exact bridge deferred to build/advise |

## Expected behavior and validation

Wrong if Tauri caused practical problems in use (install, bridge to Python, webview limits) that blocked a defendable desktop demo — pj could not name specifics in advance.

## Consequences

- Blueprint adoption path (React vs CSS-only) assumes a webview host inside Tauri.
- Installer / auto-update channel remains fog.
- Electron is not the default; reopening this decision needs a new record.
---
