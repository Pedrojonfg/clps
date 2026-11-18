---
id: D-20261118-pj-d90c
title: "Terrain holes and edges: fill on the unfavorable side and say so in provenance"
date: 2026-11-18T22:09:42Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261118-pj-a670
concepts: [terrain gaps]
supersedes: []
relates: [D-20261118-pj-9413, D-20261118-pj-b3dc, D-20261118-pj-62d3, D-20261115-pj-9ed6, D-20261114-pj-f369]
ai: options+critique
---
# Terrain holes and edges: fill on the unfavorable side and say so in provenance

## Context

External audit item 9. Read from `moonpark/horizon/grid.py` and `moonpark/hazards/raster.py`: when the elevation model has non-finite pixels, `load_tif` replaces them with the mean elevation of the read window without telling anyone, and `Grid.sample` extends the edge pixel outward for directions that leave the covered area. Point readers for slope and PSR already return "no data" for missing or out-of-range values. A hole on a ridge filled with the mean gives a lower, more optimistic horizon. The 1 km mask cap was precomputed with the current mean fill.

## Framing

Consistent with `D-20261118-pj-9413` (pessimistic bounds) and the no-silent-defaults rule; the notice must follow the compact-plus-expandable provenance pattern (`D-20261115-pj-9ed6`), not add disclaimers to the main view.

## Options considered

1. **A, as today (mean fill, edge extension)**: consequence: silent, possibly optimistic horizons.
2. **B, fill and notice**: consequence: still an unfavorable-or-favorable relleno, but declared.
3. **C, fill on the unfavorable side**: consequence: horizons higher than real in doubtful zones; more sites fail.
4. **D, do not generate the horizon**: consequence: no invented result, fewer sites evaluable.
5. **E, D with a threshold**: consequence: needs a measured number.

## Decision

**C plus the notice of B.** Holes in the elevation model are filled on the unfavorable side, using the **maximum elevation of the hole's immediate neighbours**. The result reports the filling in the expandable provenance (compact format), not as extra disclaimers in the main view.

## Rationale

(Translated from pj's Spanish.) The most consistent with our previous ADRs and ideas is to fill on the unfavorable side and also warn about it, in a format similar to the provenance notices and such; it is not a plan to crash the UI with disclaimers. On the reading of "unfavorable": 1a (the maximum of the immediate neighbours). I accept consequences 2 and 3.

## Checks raised

- Two readings of "unfavorable side" (maximum of immediate neighbours, or maximum of the whole window) → pj: the maximum of the immediate neighbours.
- The 1 km masks were computed with the old fill, so they must all be recomputed and republished as a new data version → pj accepted.
- The criterion can be measured at sites with a 5 m mosaic, by punching artificial holes and comparing horizons → pj accepted.

## Values

| Name | Value | Notes |
|------|-------|-------|
| hole_fill_rule | maximum of the hole's immediate neighbours | pj |
| fill_notice | in the expandable provenance, compact format | pj; fields: number of filled pixels |
| out_of_coverage_rule | directions that leave the covered area take the maximum of the nearest valid edge pixels | AI proposal, accepted by pj ("I accept your decision") |
| notice_fields_for_edges | count of directions that left the coverage, in the same provenance panel | accepted together with the rule |
| mask_recompute | all 1 km masks recomputed and published as a new data version | accepted by pj; overnight job |
| validation_with_holes | compare horizons with artificial holes against the originals at 5 m sites | accepted by pj |

## Later answers (pj, translated)

For directions that leave the covered area, I accept your decision.

## Expected behavior and validation

(pj, translated.) It would be a mistake if the "pessimistic" fill gave too many false negatives; I suppose this can be tested, though we will need many more precomputed masks. The comparison at 5 m sites does not need many more masks (AI note, accepted by pj).

## Consequences

- `load_tif` stops using the window mean; the fill count is returned to the caller and reported.
- All 1 km masks recomputed, tied to `D-20261118-pj-62d3` (new versioned path).
- A test with artificial holes at sites that have a 5 m mosaic.
