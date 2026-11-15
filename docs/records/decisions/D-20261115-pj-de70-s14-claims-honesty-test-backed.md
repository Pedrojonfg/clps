---
id: D-20261115-pj-de70
title: "S14 claims: assert only what tests/ADRs back; update README when runs land"
date: 2026-11-15T12:12:16Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-98c4
concepts: [claims honesty, success X/Y/Z, provenance]
supersedes: []
relates: [D-20261114-pj-41fa, D-20261115-pj-fe17, D-20261115-pj-1a9e, D-20261115-pj-358b]
ai: options+critique
---
# S14 claims: assert only what tests/ADRs back; update README when runs land

## Context

S14 must lock what the portfolio may state as fact. Prior decisions already fix X/Y/Z (`D-41fa`), demo mask honesty (`D-a988`), and PGDA 69 README wording until results (`D-fe17`).

## Framing

Prefer total honesty over marketing; claims track evidence as tests are run.

## Options considered

1. **Fixed marketing claim list independent of test status.**
2. **Evidence-gated claims** (chosen): only assert what a passing test or binding ADR supports; if a test exists but has not been run (or failed), say that and update the README when it runs.

## Decision

**Evidence-gated.** A portfolio claim is allowed as a closed fact only when a test or ADR backs it. If a test exists but has not been run, the public text says the test exists and will update the README (or validation doc) when results land — it does not pretend the check already passed.

Allowed-as-fact **when green / ADR-settled** (illustrative, maintained from ADRs): X/Y/Z per `D-41fa`; schedule tolerances per `D-f369` with the 28-point suite; layer-1 β/cap per `D-48ee`; dust label and β=cos(θ) per `D-050d`/`D-06cb`; demo computed-vs-mocked masks per `D-a988`.

## Rationale

What is validated with a test — being very honest — when there is a test and it has not been run, you cannot claim it as done. You say: there is a test; when it is run the README or whatever will be updated. Honesty and sincerity throughout; base on the ADRs and keep updating as tests are run.

## Checks raised

- Premature “validated with PGDA 69” → already forbidden until numbers (`D-fe17`); restated under `D-358b`.
- Overnight failures before final product → OK interim (`D-1a9e`); final product must not keep false claims.

## Values

| Name | Value | Notes |
|------|-------|-------|
| claims_rule | evidence_gated_test_or_adr | Core S14 rule |
| claims_unrun_test_wording | test_exists_readme_updates_when_run | Not “passes” |
| claims_source_of_truth | decision_records_plus_test_status | Not ad-hoc copy |

## Expected behavior and validation

Wrong if the final README asserts a closed validation result that never ran or still fails.

## Consequences

- S14/S15 copy and footer follow this rule; `D-358b` lists explicit forbidden/provisional patterns.
- S12 overnight results promote PGDA 69 / short-night text from planned → reported when numbers exist.
