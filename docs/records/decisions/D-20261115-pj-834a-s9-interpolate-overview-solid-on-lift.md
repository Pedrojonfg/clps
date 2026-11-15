---
id: D-20261115-pj-834a
title: "Overview map interpolates; hover or select lifts cell to solid sample color"
date: 2026-11-15T10:50:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: presentation
task: T-20261115-pj-33ca
concepts: [cell fill / nearest-sample paint]
supersedes: []
relates: [D-20261115-pj-85bf, D-20261115-pj-4126]
ai: options+critique
---
# Overview map interpolates; hover or select lifts cell to solid sample color

## Context

S9 paints sparse evaluated (and sometimes induced) samples on a region view (`D-85bf`) over a 3D Moon canvas (`D-4126`). pj wanted a smooth large-map look without losing an honest per-cell readout on interaction.

## Framing

Overview = atmospheric continuous field; selection = truth of the sample under the cursor.

## Options considered

1. **A — Nearest-sample solid cells only**: assumes honesty over smoothness; consequence: blocky map.
2. **B — Always interpolate, including selection**: assumes selection need not show the raw sample; consequence: selected color may be invented.
3. **C — Interpolate on the large/generic map; on hover or click, lift the cell and show the solid color of the center sample**: pj's proposal.

## Decision

**C.**

## Rationale

On the large/generic map, interpolate colors between points. On hover or select, lift that cell (3D) and show the solid color of the sample at its center.

## Checks raised

- Interpolated overview can feel dishonest → accepted risk for now (same batch falsification). Lift + solid is the honest read of the cell.

## Values

| Name | Value | Notes |
|------|-------|-------|
| region_map_overview_fill | interpolate | Between known samples |
| region_map_focus_fill | solid_center_sample | On hover or select |
| region_map_focus_motion | lift_cell_in_3d | Tied to 3D canvas |

## Expected behavior and validation

Wrong if users feel the interpolated overview is misleading (accepted risk for now); lift+solid is the honest read of the cell.

## Consequences

- UI must distinguish overview vs focused cell styling.
- Induced samples (`D-85bf`) remain visually softer than evaluated even when interpolated.
