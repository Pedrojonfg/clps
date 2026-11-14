---
id: D-20261114-pj-b8d3
title: "Layer B surface in; trajectories out; Moon-first body-agnostic seam"
date: 2026-11-14T11:15:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: problem framing
task: T-20261114-pj-a1b2
concepts: [layer B, trajectory, multi-body]
supersedes: []
relates: [D-20261114-pj-9f04, D-20261111-pj-60ab, D-20261114-pj-7e2a]
ai: options+critique
---
# Layer B surface in; trajectories out; Moon-first body-agnostic seam

## Context

Raising portfolio ambition reopens what used to be “decidable / post-hackathon” in `D-5cf6`: temperature, dust, trajectories, and later other landing bodies (e.g. Mars). These are not the same kind of extension.

## Framing

Expand the **same** product question (site×time under planner constraints) with surface hazards. Do not absorb Earth–Moon flight-dynamics design. Keep a body-agnostic core so Mars (or other worlds) can be a later pack, not a v1 promise.

## Options considered

1. **A — Layer A only forever**: weakest portfolio story once solo time is available.
2. **B — Layer B surface + full trajectory engine in one app**: two products (horizon/ops vs Ames-style Lunar Browser); dilutes both.
3. **C — Layer B surface in; full trajectory out; optional approach/accessibility filter; Moon beachhead + body-agnostic seams**: one product, honest boundaries.

## Decision

**C.**

## Rationale

You cannot land “anywhere for free,” but trajectory **optimization** (transfer, LOI, ΔV families) is a different user and toolchain than local sky + surface survivability. Temperature and dust share the site×time axes with power and DTE. Approach-corridor lighting or “reachable under vehicle family X” may appear as **filters** fed by external/precomputed trajectory products — not as an in-app propagator. Mars differs in atmosphere, dust storms, and data stacks; architecture should not hardcode Moon-only types, but v1 ships Moon only.

## Values

| Name | Value | Notes |
|------|-------|-------|
| layer_b_surface | in_scope | Temperature, dust, related site hazards (models in engine ledger) |
| full_trajectory_calc | out_of_product | Earth–Moon transfer / LOI / ΔV optimization elsewhere |
| approach_accessibility_filter | optional_allowed | Consumes trajectory products; does not compute them |
| primary_body | moon | Beachhead |
| multi_body_architecture | body_agnostic_core | Providers: body, ephemeris, horizon, surface hazards |
| mars_and_others_v1 | out | Later pack; no feature-parity promise in v1 marketing |

## Consequences

- Scope (`D-9f04`) lists layer-B surface as core ambition and full trajectories as out.
- Engine/architecture work should introduce body/provider boundaries early even if only Moon is implemented.
- Public copy: “architecture ready for other bodies” only if the code seam exists; never “Moon + Mars” until a second pack exists.
