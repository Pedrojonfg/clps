---
id: D-20261115-pj-3832
title: "Mask delivery: mocks in this demo; product API later"
date: 2026-11-15T11:36:16Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: architecture
task: T-20261115-pj-5200
concepts: [client compute vs server compute, public HTTPS demo honesty]
supersedes: []
relates: [D-20261115-pj-8c03, D-20261115-pj-4494]
ai: none
---
# Mask delivery: mocks in this demo; product API later

## Context

`D-8c03` makes product remote a mask store; `D-4494` keeps mask API out of this tranche’s done. Need an explicit near-term vs product path.

## Framing

Do not block the demo on networking masks; keep the product direction as an API.

## Options considered

1. Mocks now; API later (chosen).
2. Ship 1 km mask API in this tranche.
3. Ship offline mask bundle in the release.

## Decision

**This demo uses mocked mask data; in product, masks arrive from a server API (details later).**

## Rationale

pj: in product, an API; for now the demo is mocked; later from the server via an API or similar — define later.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| mask_delivery_this_tranche | mocked_in_demo | |
| mask_delivery_product_intent | server_api | Shape deferred |
| mask_api_contract | deferred — when API is specified | |

## Expected behavior and validation

Demo does not depend on a live mask API. Docs/UI must not claim live mask serving until the API exists. Wrong if the demo requires the future API to run.

## Consequences

- Matches `D-4494` (`s11_mask_api: out_for_this_tranche`).
- Future API work is a new task; cite this intent.
