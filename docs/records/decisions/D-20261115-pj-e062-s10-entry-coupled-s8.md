---
id: D-20261115-pj-e062
title: "S10 entry is coupled to S8 site and time"
date: 2026-11-15T11:36:15Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: architecture
task: T-20261115-pj-2b7a
concepts: [site×time sky geometry, first-person viewer vs orbit globe]
supersedes: []
relates: [D-20261115-pj-f2d3, D-20261114-pj-aa58]
ai: none
---
# S10 entry is coupled to S8 site and time

## Context

S10 needs a way in from the demo (S8 chart / S9 map). `D-f2d3` already requires S8 as the site/time source for the camera.

## Framing

Keep the first-person view tied to the same planner state as the horizon chart.

## Options considered

1. Coupled to S8 site and time (chosen).
2. Standalone page with independent site/time.
3. Entry only from S9.

## Decision

**Everything coupled: share site and time with S8.**

## Rationale

pj had little preference on mechanism; chose coupling so site and hour stay with S8.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_entry | coupled_s8_site_time | Query/link from S8; S9 may deep-link into the same params |
| s10_entry_decoupled | false | |

## Expected behavior and validation

Opening first-person uses the same site and time as the S8 view. Wrong if the two pages silently diverge.

## Consequences

- `web/firstperson.*` reads shared query/UI state with S8.
- S9 lift→site should pass the same parameters when linking to S10.
