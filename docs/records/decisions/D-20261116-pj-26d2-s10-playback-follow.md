---
id: D-20261116-pj-26d2
title: "First-person view plays the time window and can follow the Sun or the Earth"
date: 2026-11-16T21:45:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261116-pj-9eee
concepts: [time scrubbing, interpolating between hourly samples]
supersedes: []
relates: [D-20261115-pj-f2d3, D-20261115-pj-e062, D-20261115-pj-ac74]
ai: recommended
---
# First-person view plays the time window and can follow the Sun or the Earth
## Context

The first-person view had a time slider only. pj (2026-11-16): since we have every time frame and it really is the Sun and the Earth moving along computed orbits, add a play button, with options to follow the Sun and the Earth. (pj said "Sun and Moon"; from the lunar surface the second body in this view is the Earth.)

## Framing

Motion is what makes grazing polar light understandable: the Sun skims the horizon and terrain hides and reveals it.

## Options considered

1. **Step through hourly frames**: consequence: bodies jump; at 15° of azimuth per hour the Sun teleports.
2. **Continuous playback, interpolating position and visible fraction between the hourly samples the planner scored**: consequence: in-between positions are interpolated, not computed.
3. **Request a finer ephemeris for playback**: consequence: the view would show times the planner did not score, breaking `D-e062`.

## Decision

**2**, with play/pause, a speed control, loop at the end of the window, and a follow selector (off / Sun / Earth). Dragging the view turns follow off.

## Rationale

pj asked for play and follow. Interpolation keeps the view on the planner's own series (`D-e062`); Sun and Earth move slowly and smoothly enough over one hour that linear interpolation of azimuth (shortest way round), elevation and fraction is visually exact at this scale. The readout shows the interpolated clock time.

## Checks raised

- Interpolated instants are not scored samples → the scored hourly samples stay marked on the time strip; the claim is only about motion between them.
- Follow fights manual look-around → manual drag cancels follow (`D-f2d3` look-around stays intact).

## Values

| Name | Value | Notes |
|------|-------|-------|
| s10_playback | continuous_interpolated | Linear between hourly samples; azimuth by shortest arc |
| s10_playback_speeds_h_per_s | 1; 2; 6; 12 | Default 2 |
| s10_playback_end | loop | |
| s10_follow | off; sun; earth | Manual drag sets off |

## Expected behavior and validation

Wrong if playback shows a body on the opposite side of the mask from what the hourly series says at a sample time.

## Consequences

- The 2D panorama fallback (`D-ac74`) gets the same playback.
