---
id: D-20261117-pj-9a42
title: "Remove the Sun / Earth-link chips from the first-person view"
date: 2026-11-17T15:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261117-pj-c2d8
concepts: [redundant encoding, state not by colour alone]
supersedes: []
relates: [D-20261116-pj-08e8]
ai: recommended
---
# Remove the Sun / Earth-link chips from the first-person view
## Context

pj (2026-11-17): the two chips ("Night · Sun hidden by terrain", "Earth link · direct") repeat what the time strip under the slider already shows, and pj prefers the strip's bars to the icons and coloured edges. Better icons would still be redundant.

## Options considered

1. **Remove the chips**: consequence: the HUD corner is empty; state lives in the strip, the compass and the Sun/Earth text readouts.
2. **Replace with smaller icons**: consequence: still duplicates the strip.
3. **Keep**: consequence: redundancy and colour clutter remain.

## Decision

**1.** Chosen by pj.

## Rationale

`D-08e8` required state in words and not colour alone; that is still met by the strip, the compass strip and the text readouts ("… · 100 % of disc").

## Checks raised

- `D-08e8` asked for an always-visible state at a glance → the time strip and readouts are always visible; revisit if the strip is hidden in small windows.

## Expected behavior and validation

Wrong if a user cannot tell, in the 3D view, whether the Sun or Earth is visible at the current hour without opening details.

## Consequences

- `D-08e8`'s chip part is superseded in effect; its compass strip, time strip and Earth-link meaning stay.
