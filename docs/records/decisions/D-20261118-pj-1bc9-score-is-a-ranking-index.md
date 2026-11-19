---
id: D-20261118-pj-1bc9
title: "The score is a ranking index, not a probability of success; provenance stays expandable"
date: 2026-11-18T17:38:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261118-pj-a670
concepts: [heuristic score vs probability]
supersedes: []
relates: [D-20261115-pj-48ee, D-20261115-pj-9ed6, D-20261115-pj-671e, D-20261115-pj-de70]
ai: options+critique
---
# The score is a ranking index, not a probability of success; provenance stays expandable

## Context

External audit items 16 and 17. `moonpark/score.py` maps each requirement's margin to a number in 0..1 with a normal CDF divided by a fixed sigma (5 h for night and lit time, 1 h for no-Earth, others provisional), multiplies the terms, then adds a capped bonus (scale up to 1.4). The sigmas are hand-chosen provisional values, and the product assumes independent terms; neither is calibrated against outcomes. Neither the README nor the UI currently calls the score a probability (only "score"), but it could be read that way. D-9ed6 already settled provenance: complete in the payload, compact one-line plus an expandable panel in the UI.

## Framing

Say only what the number supports (`D-20261115-pj-de70`): more margin gives a higher score, which orders sites; it does not estimate the chance a mission succeeds.

## Options considered

1. **A, leave the score unlabelled (current)**: assumes users will not read it as a probability; consequence: possible misreading of a calibrated-looking number.
2. **B, present it as a ranking index and say it is not a probability**: consequence: a clear statement near the number, no change to the formula.
3. **C, calibrate the sigmas against real outcomes first**: consequence: needs data the project does not have.

## Decision

**B.** The score is a ranking index to order sites, not a probability of success. The details of how a result was computed are fully available but not shown up front: the main view stays compact and the provenance is expandable, as already done under D-9ed6.

## Rationale

(Translated from pj's Spanish.) It is an index to order sites, not a probability of success. Everything may be visible, but without giving all the information up front, which would spoil the UI and take up space; as we have done on previous occasions.

## Checks raised

- None raised; pj asked to proceed without the options table.

## Values

| Name | Value | Notes |
|------|-------|-------|
| score_meaning | ranking index, not a probability of success | |
| score_label_text | "Ranking index, not a probability of success" | delegated to the AI by pj ("I strongly do not care") |
| provenance_display | compact line plus expandable panel | `D-20261115-pj-9ed6`, unchanged |
| provenance_fields | engine and formula version, effective parameters, step, observer height, data versions, approximations used, requested vs mask coordinates and distance | accepted by pj |
| sigma_calibration | stays provisional; no review date set here | pj: keep provisional, a review time would have been set earlier; none located by the AI |

## Later answers (pj, translated)

I accept your proposed list of provenance fields. The sigmas stay provisional; I suppose we established back then when this criterion would be reviewed, so we stay faithful to that. The exact wording of the ranking-index label: I do not care, very strongly.

## Expected behavior and validation

pj did not state a criterion for what would make this a mistake; the question was not asked a second time because pj asked to move on. Implied check, not stated by pj: no UI or README text presents the score as a percentage or probability.

## Consequences

- A short note at the score ("ranking index, not a probability") in the UI and README limitations.
- The provenance panel gains the fields chosen in `provenance_fields`.
- Sigma values stay marked provisional in code and docs.
