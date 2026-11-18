---
id: D-20261118-pj-c3a9
title: "S10 own-relief surface is procedural and labelled; ion logo replaced by a plain credit"
date: 2026-11-18T10:30:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-2b7a
concepts: [photo-real look vs geometry-true placement]
supersedes: []
relates: [D-20261118-pj-b17e, D-20261115-pj-671e, D-20261116-pj-7304]
ai: recommended
---
# S10 own-relief surface is procedural and labelled; ion logo replaced by a plain credit

## Context

Our relief has no imagery: the repo holds only hillshades of our own DEMs, no albedo. pj asked to fix the "Cesium ion" logo that still showed in own-relief mode and to improve the texture if possible.

## Options considered

1. **Procedural tone and grain, labelled as such** (chosen): consequence: no new data; reads as regolith but shows no real surface features.
2. **Keep plain grey**: consequence: flat and lifeless.
3. **Real albedo imagery**: consequence: better look, needs data and carries a baked-shadow risk; moved to `D-e5d2` as a time-boxed test.

For the logo: **replace it with a text credit** "Rendered with CesiumJS · relief: NASA LRO / LOLA" in own-relief mode only (the ion logo stays in ion mode). This is a choice, not a licence requirement; revert if Cesium's attribution guidance is preferred.

## Decision

Option 1 plus the text credit. Provenance says "procedural surface" and that colour and grain are not imagery.

## Rationale

`D-671e` needs honest provenance: synthetic detail is acceptable only when it is named. Brightness still follows our Sun-disc fraction (`D-7304`).

## Expected behavior and validation

Wrong if any user could take the grain or tone for real lunar surface features, or if the ion logo shows while no ion data is in view.

## Consequences

- Grain is a screen-space bump faded with distance; no shadows are cast (unchanged).
- Replaced later if `D-e5d2` finds usable imagery.
