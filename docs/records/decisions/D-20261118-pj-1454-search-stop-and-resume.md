---
id: D-20261118-pj-1454
title: "Long searches: no hard time stop, a Stop button that halts the engine, and resumable runs"
date: 2026-11-18T21:59:28Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261118-pj-a670
concepts: [stoppable searches]
supersedes: []
relates: [D-20261118-pj-cd33, D-20261118-pj-75f1, D-20261115-pj-54f0]
ai: options+critique
---
# Long searches: no hard time stop, a Stop button that halts the engine, and resumable runs

## Context

External audit items 28 and 29. Read from `moonpark/search/deep.py` and `app.py`: the deep search has a time budget of 300 s that only sizes the number of starting points; closing the request does not guarantee the engine stops. `D-20261118-pj-75f1` makes searches heavier by evaluating every requirement.

## Framing

Honest, complete results over a fixed time cut; the user stays in control of a long run.

## Options considered

pj answered the questions directly; no options table was shown.

## Decision

- The time budget is a target the search tries to meet; it **does not stop** the search when reached.
- The UI has a **Stop button**; pressing it **stops the engine**.
- The state of a stopped search is **saved** so it can be **continued later**.

## Rationale

(Translated from pj's Spanish.) The search does not stop; we should try to meet the time, but it does not stop at five minutes or whatever. For cancelling, we can include a button in the UI to stop it, and then it should be possible to continue: so we need to save it so it can be continued later. And if they press stop, the engine must stop.

## Checks raised

- This departs from the audit's suggestion to stop at the budget and return a marked partial result → pj prefers a complete result.

## Values

| Name | Value | Notes |
|------|-------|-------|
| time_budget_behaviour | target only; no automatic stop | |
| stop_button | yes; stops the engine | |
| resume_stopped_search | yes; the stopped state is saved and the search can continue | |
| resume_state_format_and_location | the same JSON as a normal saved analysis, holding what was computed up to the stop and leaving out what is not yet obtained; stored in Documents with the saved analyses | pj |
| resume_after_app_update | yes; the data is in the user's Documents, so an update does not affect it | pj: "end of the problem" |

## Later answers (pj, translated)

When you stop a search, the same JSON that would be saved normally is saved, only up to where it got and without the parameters it has not yet obtained. So you do not care that the application updates, because the information is in your documents. End of the problem.

## Expected behavior and validation

pj did not state a criterion for what would make this a mistake. Implied check, not stated by pj: stop, close the app, reopen, continue gives the same result as an uninterrupted run.

## Consequences

- The search engine needs a cooperative stop check and a way to serialise and restore its progress.
- No partial-result marking is needed, because a stopped search is resumed, not reported as finished.
