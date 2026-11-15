---
id: T-20261115-pj-d567
title: "Close S6 green via layer-1 score tune"
kind: task
owner: pj
branch: scope/s6-layer1-tune
created: 2026-11-15T07:29:51Z
stage: done
relates: [T-20261114-pj-03a6, D-20261114-pj-6ce5, D-20261114-pj-52bd, D-20261114-pj-7520, D-20261115-pj-7c70, D-20261115-pj-d37a, D-20261115-pj-48ee]
---
# Close S6 green via layer-1 score tune

## Goal

Done means: the `D-6ce5` risk–bonus experiment has been run on the recorded inputs, pj has accepted or updated `β` / uplift cap, `score_layer1_tune_done` is true, and S6 can be treated as green under `D-52bd`. Origin: pj `/decision-flow` to close S6 green; asked whether this was only scripts.

## Triage

- Own/advise parts: whether current provisional β=0.15 and 30% uplift stay or change after the experiment (own, method & validation); what counts as a passing tune readout vs more work (own, method & validation); how the result is recorded (`score_layer1_tune_done` and any superseding values).
- Plumbing: a one-shot sweep script over Site01 windows × mission templates (and aggregate golden if present); histogram of uplift; ranking sanity checks from `D-6ce5` Expected behavior; optional code constant update if values change.

## Pending checkpoint

None.

## Orientation

- Concepts: needs-adapted score / risk×bonus (core, `D-7520`/`D-6ce5`); uplift cap (core); ranking sanity among feasible sites (core); silent bonus wash-out of risk (hazard); S6 green vs “tests pass” (hazard — tune gate forgotten).
- Facts: S6 search built on `T-03a6` (stage audit); tune closed in `D-48ee` (β=0.25, uplift 0.40, `score_layer1_tune_done` true); code and score tests match.
- Decisions surfaced: accept vs change β/cap after experiment; what readout means “tune done”.
- Approach: pj — watch pairwise cases where bonus lets a higher-risk (lower R) site×time outrank a lower-risk one; if that is very common (>~40%, invented) or almost never (<~2%, invented), reopen the tune decision and rethink (not automatically move β; a “weird” case may still be right). Middle band left as the path to accept. Later: variance + top-k overlap when inversion rates stayed &lt;2%.

## Decisions

- D-20261115-pj-7c70 — Tune gate: accept in 2–40% risk-order inversion band; reopen outside
- D-20261115-pj-d37a — Tune experiment: separate feasible and infeasible pair-inversion rates
- D-20261115-pj-48ee — Layer-1 tune: β=0.25, uplift cap 0.40; tune done, reopen if geography differs


## Auto decisions

| Choice | Reason |
|--------|--------|
| One-shot sweep script under `scripts/` with table/histogram output | agenda OK |
| Script I/O details (paths, print format) | engineering hygiene / auto |
| Hazards off in the sweep | isolate schedule layer-1 β/cap; not recorded as own |
| Window 24 h, step 1 h on Site01 week 2027-01-01..07 | matches proposed addition; enough pairs |
| Inversion = same template, R_a>R_b but companion_a<companion_b (strict, either order) | proposed addition |
| Thin-N flag if pairs < 50 | proposed addition |
| Production constants updated in `lunar_eval/score.py` + tests to β=0.25 / uplift 0.40 | follows `D-48ee` |

## Fog

- Whether ~40% / ~2% become locked Values or stay orientative cues — settled in `D-7c70` as locked band values.

## Out of scope

- Reopening the layer-1 formula shape (`D-7520`) beyond β / uplift values.
- S7 / P14, S9 map, and finishing the empty Audit section of `T-03a6` (separate; green gate is this tune).

## Build

2026-11-15: `scripts/tune_layer1_bonus.py` — Site01 week × 10 templates, then `--year 2027` (53 chunks, 75410 scores, ~12 s). Full-year β=0.15: feas≈0.94% REOPEN, infeas=0.00% REOPEN; β sweep still &lt;2%. Follow-up variance + top-k on feasible varying-R templates → `D-48ee`. Code: `_BETA=0.25`, `_MAX_UPLIFT=0.40`; `tests/test_score.py` green.

## Audit

Tune values match `D-48ee` in score module and tests (2026-11-15). Sibling `T-03a6` Audit section still empty (out of this task).

## Detours

- Sibling task `T-20261114-pj-03a6` remains at stage audit with empty Audit section; its Build already excluded this tune.
- Parallel chat confirmed `D-48ee` while this session opened on S7; residual pending checkpoint cleared here after record + code already landed.
