---
id: D-20261115-pj-ac74
title: "S10 fallback is a 2D mask panorama"
date: 2026-11-15T11:36:16Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-2b7a
concepts: [topographic horizon mask, first-person viewer vs orbit globe]
supersedes: []
relates: [D-20261115-pj-ac34, D-20261115-pj-7d58, D-20261115-pj-671e]
ai: none
---
# S10 fallback is a 2D mask panorama

## Context

Cesium / ion may fail on demo day. `D-ac34` already named `mask_panorama_if_hybrid_fails` as cut fallback; this record locks the advise choice.

## Framing

Prefer a defendable degraded view over a broken Cesium page.

## Options considered

1. 2D mask panorama (chosen).
2. No fallback (error only).
3. Always panorama; Cesium optional stretch.

## Decision

**Fallback = 2D mask view and ship that.**

## Rationale

pj: simply a 2D mask and go with that.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_cut_fallback | mask_panorama_2d | Aligns with / replaces soft value on `D-ac34` |
| s10_fallback_trigger | cesium_or_ion_unavailable | |

## Expected behavior and validation

If Cesium or ion is unavailable, the user still sees a 2D mask-based view. Wrong if the page is blank with no alternative.

## Consequences

- Implement panorama path enough to swap in when Cesium fails.
- Provenance copy (`D-671e`) still applies (backdrop may be absent in fallback).
