---
id: D-20261115-pj-cacb
title: "README: public portfolio — what/how/try-today; future masks+API"
date: 2026-11-15T12:12:17Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: presentation
task: T-20261115-pj-98c4
concepts: [claims honesty, portfolio pack vs contest]
supersedes: []
relates: [D-20261115-pj-de70, D-20261115-pj-a988, D-20261115-pj-8c03, D-20261114-pj-7e2a]
ai: options+critique
---
# README: public portfolio — what/how/try-today; future masks+API

## Context

S14 includes README audience and honesty structure. Delivery frame is solo portfolio (`D-7e2a`). Public demo today is limited without precomputed masks / mask API (`D-a988`, `D-8c03`, `D-4494`).

## Framing

Anyone should see what was built and how to try it now, without implying a full online evaluator that does not exist yet.

## Options considered

1. **Contest submission README.**
2. **Portfolio README: what / how / try-today / future** (chosen).
3. **README only after full mask hosting exists.**

## Decision

**Portfolio README.** Audience: anyone viewing the portfolio. Structure: what was done; how it was done; how to try it **today** (honest limits — without precomputed masks it is not fully usable as the end product); **future**: add masks (where they will live) and connect via API or the recorded delivery path. Claims follow `D-de70` / `D-358b`.

## Rationale

It is for my portfolio — anyone can see what I did, how I did it, and how it is used; the point is that it can be used. Today, without precomputed masks, it cannot really be used, so the provisional README should be: we built this and this this way; today you can try it like this; in the future we will add the masks, they will be findable here, and it will be connected by an API or whatever.

## Checks raised

- Implying full usability today → rejected by explicit try-today limits.
- Evidence-gated claims → `D-de70`.

## Values

| Name | Value | Notes |
|------|-------|-------|
| readme_audience | public_portfolio | Not Space Apps judges as primary |
| readme_sections | what; how; try_today_limits; future_masks_api | Order flexible; all required |
| readme_try_today | honest_partial_without_full_masks | State concrete steps that work now |
| readme_future | masks_location_plus_api_or_recorded_path | Align with `D-8c03` when masks ship |
| readme_claims | follow_D-de70_D-358b | |

## Expected behavior and validation

Wrong if a reader believes a full mask-backed hosted evaluator is available today when it is not.

## Consequences

- `README.md` rewrite is build work under this outline; S15 pack links to it.
- Updates when mask hosting/API lands (new short decide if the future path changes).
