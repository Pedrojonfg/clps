---
id: D-20261115-pj-1264
title: "S15 pack: Remotion demo video after UI; pitch deck owned by pj"
date: 2026-11-15T12:15:23Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261115-pj-98c4
concepts: [portfolio pack vs contest, claims honesty]
supersedes: []
relates: [D-20261114-pj-7e2a, D-20261115-pj-cacb, D-20261115-pj-8fd2]
ai: options+critique
---
# S15 pack: Remotion demo video after UI; pitch deck owned by pj

## Context

Old plan S15 was a Space Apps submission (≤7 slides or 30 s) by 23:00. Frame is solo portfolio (`D-7e2a`). UI polish is underway in another conversation (viz scopes S8–S10 exist; no separate “whole UI” scope ID).

## Framing

Separate the demo artifact (video) from the live pitch slides.

## Options considered

1. **Slides-only pack.**
2. **Remotion demo video after UI + pj-owned pitch deck** (chosen).
3. **Docs-only, no video.**

## Decision

**Remotion demo video + self-made pitch.** After the UI is in good shape, produce a **Remotion** demo video. The **pitch presentation** for the in-person/local pitch is created by pj (may ask for help later; ownership stays with pj). No Space Apps 23:00 submission requirement.

## Rationale

When the UI is done — I am doing that in another conversation — I will make a Remotion video; for the particular pitch I will create the presentation myself. So: a Remotion demo video once the UI is properly finished.

## Checks raised

- No dedicated “UI polish” scope → noted: remaining UI is finishing/integrating S8/S9/S10 (+ S14 provenance chrome), not a missing Sn.
- Video blocked on UI → accepted (`D-8fd2`).

## Values

| Name | Value | Notes |
|------|-------|-------|
| s15_demo_medium | remotion_video | After UI ready |
| s15_pitch_deck | pj_owned | Help on request; not AI-owned deliverable |
| s15_contest_submit | out | `D-7e2a` |
| s15_video_gate | ui_finished | Explicit dependency |

## Expected behavior and validation

Wrong if the pack claims a finished demo video while the UI gate is unmet, or if a contest submission deadline is treated as binding.

## Consequences

- Remotion work starts only after UI gate (`D-8fd2`).
- Docs quality is separate (`D-3c4a`).
