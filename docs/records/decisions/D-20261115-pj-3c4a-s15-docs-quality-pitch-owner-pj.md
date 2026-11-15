---
id: D-20261115-pj-3c4a
title: "S15 docs: install/use must be clear; pitch length owned by pj"
date: 2026-11-15T12:15:24Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: presentation
task: T-20261115-pj-98c4
concepts: [portfolio pack vs contest]
supersedes: []
relates: [D-20261115-pj-cacb, D-20261115-pj-1264]
ai: options+critique
---
# S15 docs: install/use must be clear; pitch length owned by pj

## Context

S15 content/length after choosing Remotion + self pitch (`D-1264`). README outline already in `D-cacb`.

## Framing

Docs are the durable how-to; slide count is not a product constraint for the AI-owned pack.

## Options considered

1. **Force ≤7 slides / 30 s like old Space Apps.**
2. **Strong docs (install/use); pitch structure/length left to pj** (chosen).
3. **Defer all docs until after video.**

## Decision

**Docs must be clear** (especially install and how to try). Pitch deck content and length are **pj’s** for the pitch (help when asked). No mandatory ≤7 slides / 30 s cap for the portfolio pack. Remotion video length left open until storyboard (deferred value).

## Rationale

Docs have to be very well explained — how to install, etc. Content and length for the presentation: I will handle the pitch deck myself and will ask for help; I am not fixing a slide/video second count now.

## Checks raised

- Vague “docs good” → tied to `D-cacb` sections (what/how/try-today/future) plus install path.
- Remotion duration unset → deferred until UI/storyboard.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s15_docs_bar | clear_install_and_try_today | Align README + any `docs/` how-to |
| s15_pitch_length | pj_chooses | No contest cap |
| s15_remotion_duration_s | deferred — set at storyboard after UI | |
| s15_slide_cap | none | Old Space Apps cap out |

## Expected behavior and validation

Wrong if a newcomer cannot install/try from docs while the README claims usability paths.

## Consequences

- Build README/`docs` to `D-cacb` + install clarity before calling docs done.
- Pitch file lives where pj puts it; optional copy under `docs/` later.
