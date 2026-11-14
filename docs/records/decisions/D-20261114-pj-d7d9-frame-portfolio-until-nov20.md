---
id: D-20261114-pj-d7d9
title: "Portfolio scope governs through 20 Nov; Space Apps submission on 15 Nov as a cut"
date: 2026-11-14T11:30:45Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: problem framing
task: T-20261114-pj-12b7
concepts: [appetite, scope]
supersedes: [D-20261114-pj-7e2a]
relates: [D-20261114-pj-9f04, D-20261114-pj-b8d3, D-20261111-pj-60ab]
ai: options+critique
---
# Portfolio scope governs through 20 Nov; Space Apps submission on 15 Nov as a cut

## Context

`D-20261114-pj-7e2a` framed the project as a solo portfolio, explicitly not a contest submission. An untracked plan (`docs/plans/2026-11-14-hackathon-lite-plan.md`, approval pending) proposed a two-day hackathon bet that excludes SPICE, DEM horizon masks and layer B. pj now states that the project continues until Thursday 20 November 2026 and that something will be submitted to NASA Space Apps on Sunday 15 November. Data and visualization source decisions (task `T-20261114-pj-12b7`) depend on which frame governs.

Space Apps 2026 facts (participant FAQ and organizer answers, read 2026-11-14): submission closes 15 Nov 23:59 local; demo is a video ≤ 30 s or ≤ 7 slides; Universal Event teams need ≥ 2 members for global judging; global awards require meaningful use of at least one NASA data source from the challenge Resources; SI/AI use must be disclosed; teams may not begin work on challenges before the hackathon.

## Framing

Keep the full portfolio ambition instead of a cut-down weekend bet, accept a fixed public showing on Sunday, and use the remaining days for whatever does not fit.

## Options considered

1. **A — Hackathon-lite plan governs this weekend**: assumes Sunday 23:00 is fixed and portfolio scope does not fit; consequence: spherical horizon, no layer B, portfolio resumes later.
2. **B — Portfolio scope governs, Sunday as the date**: assumes all of `D-9f04` fits in a day and a half; consequence: DEM masks, layer B and deep search before Sunday.
3. **C — Portfolio scope governs, no date**: assumes no clock, as in `D-7e2a`; consequence: sources chosen for the full product, no time-based cut.

## Decision

**B, extended:** portfolio scope (`D-20261114-pj-9f04`) governs from now. Target is the full scope by Sunday 15 Nov; the project continues until Thursday 20 Nov; if not everything fits by Sunday, a defined cut is what is submitted to Space Apps. The hackathon-lite plan is rejected.

## Rationale

"The portfolio scope is feasible in a day and a half; I can do it. The project continues until Thursday 20 November; if not everything fits by Sunday, I finish it over the following days, and we define what is presented at the hackathon."

## Checks raised

- `D-7e2a` says this is not a contest submission → pj: there is a Space Apps submission on Sunday; project runs until 20 Nov. This record supersedes `D-7e2a`.
- "Running out of time" is only visible at the end; fixed time / variable scope suggests an earlier checkpoint → to be set in the `/shape-up` replan.
- Score formula, success X/Y/Z and visualization set are still deferred and block the build; engine-ledger decisions consume the same hours → acknowledged; handled by the replan.
- Profile lists beginner in ephemerides/SPICE/lunar terrain; geometry is the piece most likely to grow → not answered separately; covered by the same replan.
- Universal Event with one builder is not eligible for global judging → pj: registered for the Universal Event, knows it does not qualify, will pitch with friends, does not seek awards.
- Rule against starting before the hackathon; repo holds records from 11–13 Nov → pj: those were decisions only, zero code, and pj does not seek awards.

## Values

| Name | Value | Notes |
|------|-------|-------|
| delivery_context | portfolio_with_space_apps_submission | Replaces `solo_portfolio` from `D-7e2a` |
| challenge_role | space_apps_entry | Universal Event; replaces `heritage_brief` |
| global_judging | not_sought | Award-only rules (team ≥ 2, Resources data use) are not targets |
| team | owner_only | Builder is pj alone; friends join for the pitch |
| space_apps_submission_deadline | 2026-11-15 23:59 local | Video ≤ 30 s or ≤ 7 slides; SI use disclosed |
| project_window_end | 2026-11-20 | Work continues after the submission |
| hack_submission_cut | deferred — defined in the `/shape-up` replan on top of this task's decisions | |
| hackathon_lite_plan | rejected | `docs/plans/2026-11-14-hackathon-lite-plan.md` is not adopted |

## Expected behavior and validation

"That I don't have time to finish it by tomorrow." (Sunday 15 November 2026.)

## Consequences

- `project.md` must move "rules & eligibility (Space Apps)" from `out` into scope (submission format, SI disclosure, NASA-branding limits) and add milestones 2026-11-15 (submission) and 2026-11-20 (project end). Edit on the default branch or as its own small PR, not from this feature branch.
- `primary_body_v1 = moon` from `D-7e2a` is not restated; `primary_body = moon` in `D-20261114-pj-b8d3` covers it.
- Data and visualization decisions in `T-20261114-pj-12b7` are taken for the full portfolio scope; the hack cut is chosen afterwards.
- The weekend plan is redone with `/shape-up`.
