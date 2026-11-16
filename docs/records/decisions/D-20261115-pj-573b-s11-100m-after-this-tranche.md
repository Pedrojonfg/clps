---
id: D-20261115-pj-573b
title: "100 m precompute and server benchmark start after this tranche"
date: 2026-11-15T11:36:17Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: dependencies & ops
task: T-20261115-pj-5200
concepts: [demo 1 km vs full 100 m spacing, calling the job done after start, resume-safe precompute]
supersedes: []
relates: [D-20261115-pj-8c03, D-20261115-pj-4494, D-20261114-pj-a3b3, D-20261114-pj-f369]
ai: none
---
# 100 m precompute and server benchmark start after this tranche

## Context

Plan S11 included a CX43 one-hour benchmark and starting the 100 m run. `D-4494` already left those out of this tranche’s done. Process hosts remain in `D-8c03`. pj states work on 100 m starts from tomorrow, not in this scope.

## Framing

Do not treat 100 m / benchmark as demo-tranche deliverables.

## Options considered

1. After this tranche / from tomorrow (chosen).
2. Start 100 m on pj’s PC in this tranche.
3. Order VPS and benchmark in this tranche.

## Decision

**100 m precompute and server benchmark are not part of this scope; pj starts that work from tomorrow onward.**

## Rationale

pj: 100 m + benchmark do not belong to now; will start from tomorrow; not needed for this tranche / this scope.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s11_100m_start | out_for_this_tranche | Same meaning as `D-4494`; timing = after tranche |
| s11_100m_start_when | after_this_tranche_from_tomorrow | Process calendar, not demo done |
| s11_server_benchmark_hour | out_for_this_tranche | When a host exists, still use first-hour masks/s before full commit (`D-8c03`) |

## Expected behavior and validation

This tranche can close without a running 100 m job or benchmark hour. Wrong if “S10/S11 demo scope done” is blocked on those.

## Consequences

- Tomorrow’s process work cites `D-8c03` / `D-f369`; new task if needed.
- Cut order in `D-a3b3` remains compatible (public URL / 100 m not Sunday-critical).
