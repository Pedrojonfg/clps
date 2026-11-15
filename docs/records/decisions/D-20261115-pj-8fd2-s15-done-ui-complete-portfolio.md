---
id: D-20261115-pj-8fd2
title: "Portfolio done when UI is finished (then video/docs/disclosure)"
date: 2026-11-15T12:15:24Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261115-pj-98c4
concepts: [portfolio pack vs contest, claims honesty]
supersedes: []
relates: [D-20261115-pj-1264, D-20261115-pj-3c4a, D-20261115-pj-6663, D-20261114-pj-7e2a]
ai: options+critique
---
# Portfolio done when UI is finished (then video/docs/disclosure)

## Context

Need a “published/done” meaning under solo portfolio (not contest 23:00). Remotion waits on UI (`D-1264`).

## Framing

UI completeness is the project gate; pack artifacts follow.

## Options considered

1. **Done at contest submit time.**
2. **Done when UI is finished (and supporting docs/video/disclosure follow)** (chosen).
3. **Done only when Remotion + pitch + all validation numbers are green.**

## Decision

**UI finished ⇒ project can be considered done** for portfolio purposes, with Remotion video, clear docs, and NASA/heritage disclosure completed as the pack that presents that UI. No contest deadline. Repo + Pages URL remain the public anchors when used (`D-2533` / README).

## Rationale

If the UI is finished and all of that, the project can be considered done.

## Checks raised

- Validation overnight / evidence-gated claims still apply (`D-de70`, `D-1a9e`) — “done” does not license false validation claims.
- UI scope: S8–S10 (+ provenance chrome S14); polish may continue in the other chat without a new Sn.

## Values

| Name | Value | Notes |
|------|-------|-------|
| portfolio_done_gate | ui_finished | Primary |
| portfolio_pack_followthrough | remotion_plus_docs_plus_disclosure | After UI |
| portfolio_contest_deadline | none | |
| portfolio_public_anchors | repo_and_pages_when_used | |

## Expected behavior and validation

Wrong if “done” is claimed while the UI is unfinished, or while public claims violate `D-de70`/`D-6663`.

## Consequences

- Other-chat UI work is on the critical path for S15 video and portfolio close.
- This decide task’s build of Remotion waits on that gate.
