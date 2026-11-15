---
id: D-20261115-pj-0ee7
title: "S7 validation: demo bar now; medium megatest tonight"
date: 2026-11-15T10:25:36Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-2cbd
concepts: [stopping rule / budget, silent incomplete search]
supersedes: []
relates: [D-20261115-pj-54f0, D-20261115-pj-8a25, D-20261115-pj-1ebf, D-20261114-pj-52bd]
ai: options+critique
---
# S7 validation: demo bar now; medium megatest tonight

## Context

S7 needs a validation bar before calling the scope done. Prior records already deferred optimized-vs-`total_coverage` checks (and step sizes) post-demo (`D-54f0`, `D-8a25`, `D-1ebf`). Cost order: small boxes minutes; ~50×50 km × 7 d coverage ~23 min; a medium megatest band ~1–2 h on this machine class.

## Framing

Unblock a working demo today without pretending the method is fully oracle-checked; schedule a real comparison tonight.

## Options considered

1. **A — Megatest mandatory before S7 done**.
2. **B — Demo usable = v1 bar; megatest harness created today; run tonight (medium ~1–2 h); does not block demo done**.
3. **C — Synthetic unit tests only; no megatest plan**.

## Decision

**B**, with megatest scope in the **medium** band (~1–2 h).

## Rationale

pj (2026-11-15): That the demo works. We will run the extensive test tonight; it has to be created but not necessarily run (in any case, tell me how long you think it will take and I will choose the best moment to run it). Medium band is fine.

## Checks raised

- Defaults could be very bad and the demo might not look good → accepted as the v1 falsifier; for the final product, nothing (megatest carries that).

## Values

| Name | Value | Notes |
|------|-------|-------|
| s7_validation_v1_bar | demo_usable | Working deep-search path in the demo |
| s7_megatest_status | harness_required_run_tonight | Created with the build; execution tonight |
| s7_megatest_scope | medium_approx_1_to_2_h | e.g. one ~50×50 km × ~7 d coverage ref + optimized/default + step-size variants |
| s7_method_claims_until_megatest | provisional | Do not over-claim vs grid optimum |

## Expected behavior and validation

pj (2026-11-15): That the defaults were very bad and the demo did not turn out well, but as for the final product, nothing.

## Consequences

- Build includes a runnable megatest script/tests even if CI does not wait on the full night run.
- Demo may ship with provisional deep-search quality labels.
- Tonight: run medium megatest; record outcome (new event or follow-up decision if defaults change).
