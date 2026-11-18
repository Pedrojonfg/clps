---
id: D-20261118-pj-d7a5
title: "First-use download shows a flat Blueprint progress bar, per file"
date: 2026-11-18T12:00:00Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: presentation
task: T-20261115-pj-5200
concepts: [progressive disclosure, design-system authority]
supersedes: []
relates: [D-20261117-pj-c4e8, D-20261117-pj-f19a, D-20261117-pj-6d1e]
ai: options+critique
---
# First-use download shows a flat Blueprint progress bar, per file

## Context

The first real evaluation downloads up to ~0.7 GB (`D-c4e8`). The planner only showed one line of text with MB, so a long download looked like a hung app. This was the open point before the first release.

## Decision

A Blueprint `ProgressBar` inside the planner status callout while the engine reports an active download: flat (no stripes, no animation, no intent colour), percentage and sizes in Blueprint's monospace with tabular figures, and a note that the data is kept locally. It fills with the progress of the current file; the session total is in the text.

## Rationale

Follows `D-f19a` (colour carries state, not decoration) and `D-6d1e` (monospace readouts). Uses the existing `/progress` endpoint, so the engine does not change.

## Consequences

The bar returns to 0 on each new file. A global bar needs the engine to estimate the pending total per request; left for after v0.1.0.

## Expected behavior and validation

Wrong if the bar looks stuck or empty during a real first-use download, or if any colour on it is decorative. Check with an empty cache once the store is published.
