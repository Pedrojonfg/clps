---
id: D-20261118-pj-cd33
title: "v1 usage limits: only the strictly necessary ones, values taken from tests later"
date: 2026-11-18T21:36:29Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261118-pj-a670
concepts: [usage limits]
supersedes: []
relates: [D-20261118-pj-75f1, D-20261118-pj-8625, D-20261118-pj-b3dc]
ai: options+critique
---
# v1 usage limits: only the strictly necessary ones, values taken from tests later

## Context

External audit items 29 and 30. Read from `moonpark/api/app.py` and `moonpark/search/deep.py`: a single-site analysis accepts up to 744 hourly steps (about 31 days); the regional search takes a window of 1 to 168 hours; the deep search has a time budget `tmax_s = 300 s` that, per the audit, only sizes the number of starting points and does not stop the search; the region size has no limit; cancelling the request does not guarantee the engine stops. Everything runs on the user's computer. No measurements of time or memory at realistic sizes were run in this session (the attempt was stopped by pj, who preferred to decide first and test later).

## Framing

Restrict the user as little as possible; the limits that exist should be set at the point where requests start to fail.

## Options considered

pj stated a choice without asking for alternatives; no options table was shown.

## Decision

Keep **only the strictly necessary limits** (for example, coverage: the app cannot compute at the north pole). Because everything runs on the user's computer, no further caps are added up front. The remaining limit values are to be **derived from tests** that find where requests begin to fail.

## Rationale

(Translated from pj's Spanish.) Considering that everything runs on the user's PC, I would not put many limits, I would say only the strictly necessary ones (we cannot compute at the north pole, for example). I assume we can run tests to get these parameters. Later we do the tests; for now let us keep deciding.

## Checks raised

- None raised; pj asked to go on deciding and do the tests afterwards.

## Values

| Name | Value | Notes |
|------|-------|-------|
| coverage_limit | the app computes only where data covers (south polar cap); not at the north pole | the strictly necessary limit |
| other_limits | none up front | |
| limit_values_source | tests that find where requests start to fail | not run yet |
| max_window_site | to be set from tests (today 744 hourly steps) | pj: tests run at implementation, overnight |
| local_search_step | 1 h only | pj: "I see no reason to make it larger"; settles the `step_h` question |
| max_region_size | deferred — to be set from tests (today unlimited) | |
| max_search_time_and_partial_result | the search does not stop at the time budget; the budget is a target to try to meet | pj; this departs from audit item 28 (stop and mark partial) |
| cancel_long_jobs | a UI stop button that stops the engine, and the search can be continued later | pj; see `D-20261118-pj-1454` |

## Later answers (pj, translated)

The search time: no, it does not stop; it should try to meet it, but it does not stop at 5 minutes or whatever. Cancelling long jobs: a stop button in the UI, and the work should be saved so it can be continued later; if the user presses stop the engine must stop. Limits from tests: when you implement, create those tests and run them; I will leave you all night to run the tests and tell me the results in the morning. The local search step: I would restrict it to one hour.

## Expected behavior and validation

(pj, translated.) It would be a mistake if there were many errors because of these wide limits; the point is for the limits to be as narrow as needed to avoid errors, exactly there. pj expects tests to be able to find these parameters.

## Consequences

- A measurement task (time and memory at several region sizes, window lengths and resolutions) is needed to set the deferred values; it was not run here.
- Until the measurements exist, v1 has no documented usage limits other than coverage (audit item 30).
