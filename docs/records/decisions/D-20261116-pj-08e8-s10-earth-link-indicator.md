---
id: D-20261116-pj-08e8
title: "First-person view shows the direct-to-Earth link state without facing the Earth"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261116-pj-9eee
concepts: [status not colour-alone, off-screen body]
supersedes: []
relates: [D-20261115-pj-671e, D-20261116-pj-26d2, D-20261116-pj-7304]
ai: recommended
---
# First-person view shows the direct-to-Earth link state without facing the Earth
## Context

Whether the Earth clears our mask was only in a footer line ("above mask" / "behind mask") and on the Earth marker itself, which is usually off-screen. pj (2026-11-16): find a visual way to mark whether there is a direct connection to Earth that does not require looking at it.

## Framing

Sun and Earth state should be readable at a glance from any heading.

## Options considered

1. **Tint the whole frame**: consequence: conflicts with the Sun-driven brightness (`D-20261116-pj-7304`).
2. **Heads-up status chips (Sunlight %, Earth link) plus a compass strip across the top with Sun and Earth at their azimuths**: consequence: a little persistent chrome over the scene.
3. **Edge arrows only**: consequence: direction but no state.

## Decision

**2.** The Earth chip reads "Earth link · direct" or "Earth link · blocked by terrain", with icon and text as well as colour; the compass strip shows where both bodies are relative to the current heading, with the Earth drawn hollow and struck through when blocked. The time strip under the slider shows, hour by hour, Sun-disc fraction and link state for the whole window.

## Rationale

Chips carry state in words, so it is not colour-alone. The compass strip answers "where is it" in the same glance and makes the Face Sun / Face Earth buttons predictable. The time strip shows when the link comes and goes without playing the window.

## Checks raised

- "Link" could be read as a radio link budget → the details panel says it means line of sight to the Earth above our horizon mask, using the planner's Earth threshold.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_link_definition | earth_fraction > earth_lit_threshold | Same rule as the planner series |
| s10_link_indicator | status_chip_text_icon_colour; compass_strip; time_strip | |

## Expected behavior and validation

Wrong if the chip says "direct" at an hour the planner counts as no-Earth.

## Consequences

- Footer body lines stay as the numeric readout.
