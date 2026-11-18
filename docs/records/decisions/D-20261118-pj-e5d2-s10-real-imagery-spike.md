---
id: D-20261118-pj-e5d2
title: "S10 real surface imagery: one-hour spike before committing"
date: 2026-11-18T11:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-2b7a
concepts: [photo-real look vs geometry-true placement]
supersedes: []
relates: [D-20261118-pj-c3a9, D-20261118-pj-b17e, D-20261115-pj-ce2e]
ai: options+critique
---
# S10 real surface imagery: one-hour spike before committing

## Context

pj: real imagery would improve the experience a lot, and matters for recording video to share with coworkers. Candidate: LROC WAC south-polar mosaic at 100 m/px (public domain, about 1.3 GB as the global south tile, 10 to 25 MB once cropped to 80°S–90°S). Cost estimate: negligible compute (colour sampled per mesh vertex on the server, about 170 KB extra), about a day of work, mostly tuning. Main risk: polar images carry baked shadows from grazing light, which contradict our simulated Sun.

## Options considered

1. **Commit to imagery now**: consequence: a day spent that may end in a dark, blotchy result.
2. **One-hour spike, then decide** (chosen): consequence: cheap evidence first.
3. **Stay procedural**: consequence: no cost, less appealing for video.
4. **Use ion for recordings**: consequence: best quality now, token needed only on the recording machine.

## Decision

**2.** Download the WAC south mosaic (prefer the summer ROI product), crop to 80°S–90°S, look at it, and drape it on our mesh in a test render. Go if tone is usable without baked-shadow artefacts; otherwise stop and keep `D-c3a9`.

## Checks raised

- 100 m/px is blocky inside about 300 m of the observer: blend with the procedural grain there.
- Attribution NASA/GSFC/Arizona State University; file distribution via the data store, optional.

## Expected behavior and validation

Go criteria: no obvious baked shadows at the site, brightness controllable by `D-7304`. Wrong to adopt if the imagery makes the lit/dark state contradict our Sun series.

## Consequences

- If go: per-vertex albedo in `/terrain`, an imagery file in the store, provenance and credit updated.
- If no-go: this record closes the question until better imagery is available.
