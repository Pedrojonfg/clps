---
id: D-20261115-pj-fe17
title: "PGDA 69 role: S12 validation report + README mention; not in product logic"
date: 2026-11-15T12:05:59Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-98c4
concepts: [PGDA 69 averages, claims honesty, success X/Y/Z]
supersedes: []
relates: [D-20261114-pj-41fa, D-20261114-pj-bf69, D-20261115-pj-9ab3]
ai: options+critique
---
# PGDA 69 role: S12 validation report + README mention; not in product logic

## Context

`D-41fa` left `pgda69_in_xyz=false` reopenable at S12/P12. `D-bf69` keeps PGDA 69 averages out of the score. S12 decides the product/claims role once the comparison protocol exists (`D-9ab3`).

## Framing

Use the long-term map as external validation evidence without treating it as a site×time product feature.

## Options considered

1. **Out entirely.**
2. **S12 report only.**
3. **S12 report + README validation mention** (chosen).
4. **Enter X/Y/Z.**
5. **Enter score / planner logic.**

## Decision

**Report + README only.** PGDA 69 comparison belongs in the S12 validation report and may be cited in the README as validation evidence. It has **no role in product logic** (not score, not search, not X/Y/Z). `pgda69_in_xyz` stays **false**; `score_pgda69_averages` stays **out_v1**.

## Rationale

If I remember right, it is only a report — it can go in the README as used for validation, but I do not think it has any use in the actual product, so beyond that it is not needed. I would put it in the S12 report, of course, and in the README, but little more.

## Checks raised

- README claiming “validated with PGDA 69” before numbers exist → agreed: wording must say planned / see validation.md until results exist.
- Tests may fail overnight → fix before final product; premature final claims would be wrong.

## Values

| Name | Value | Notes |
|------|-------|-------|
| pgda69_in_xyz | false | Restated; not reopened into X/Y/Z |
| score_pgda69_averages | out_v1 | Restated from `D-bf69` |
| pgda69_product_role | validation_report_and_readme_only | Not engine/UI logic |
| pgda69_readme_claim_until_results | planned_or_pointer_to_validation_md | No completed-validation claim without numbers |

## Expected behavior and validation

Wrong if the final product README asserts completed PGDA 69 validation while tests/scripts failed or results are missing. Overnight failures before the final product are acceptable if fixed by then.

## Consequences

- S14 README copy must follow `pgda69_readme_claim_until_results`.
- P12 “role” agenda item is settled for v1 unless superseded.
