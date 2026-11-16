---
id: T-20261116-pj-9eee
title: "Rework the result visualizations after pj's UI review"
kind: task
owner: pj
branch: fix/visualizations-ui
created: 2026-11-16T21:45:00Z
stage: build
relates: [T-20261115-pj-33ca, T-20261115-pj-2b7a, T-20261114-pj-9e03, T-20261114-pj-03a6]
---
# Rework the result visualizations after pj's UI review

## Goal

pj reviewed the desktop app on 2026-11-16 and asked, in one message before leaving the AI to work unattended: a clearer planner result view; a local-search leaderboard that also shows in mock mode; a first-person view that looks better, plays the window, lights the scene by visible Sun-disc fraction and shows the Earth link without facing it; and a region map whose evaluated cells are visible and easy to reach at any zoom, with gaps interpolated if that is honest. pj asked for the decisions to be recorded first, then built, then a pull request to `main` for review.

## Triage

- Own parts: region-map estimate layer (method) — recorded as **proposed**, awaiting pj; infeasible colour and backdrop brightness rule (claims) — requested by pj, form chosen by the AI under explicit delegation.
- Advise parts: planner view form, playback, link indicator, backdrop quality, mock leaderboard, mask azimuth contract.
- Plumbing: everything else.

## Pending checkpoint

pj to accept or reject `D-20261116-pj-1df2` (estimate layer) and to review the delegated choices on the pull request.

## Decisions

- D-20261116-pj-142f — Planner result view: panorama, timeline, needs versus actual
- D-20261116-pj-4902 — Mock mode ships a local-search leaderboard
- D-20261116-pj-26d2 — First-person playback and follow
- D-20261116-pj-7304 — Backdrop brightness follows our Sun-disc fraction
- D-20261116-pj-08e8 — Earth link indicator
- D-20261116-pj-ce2e — Backdrop at the asset's maximum quality
- D-20261116-pj-2325 — Region map markers, non-black infeasibles, snap to evaluated (supersedes D-8acb)
- D-20261116-pj-1df2 — Region map estimate layer (proposed)
- D-20261116-pj-b43a — Mask azimuth convention in the payload

## Notes

- Decide and build ran in one unattended pass at pj's request; the usual per-decision conversation did not happen. Records marked `ai: delegated-by-pj` were chosen by the AI and have not been defended by pj yet.
- No understanding record was written: there was no exchange to draw evidence from.

## Out of scope

- Own DEM-based terrain for the first-person view; removing API-side induction before pj rules on the estimate layer; changing the red–yellow–green ramp.
