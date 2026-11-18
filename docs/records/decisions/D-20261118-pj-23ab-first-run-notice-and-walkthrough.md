---
id: D-20261118-pj-23ab
title: "First run: a notice about what is downloaded and a short walkthrough with mocked data"
date: 2026-11-18T17:56:47Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261118-pj-a670
concepts: [first-run cost]
supersedes: []
relates: [D-20261118-pj-b3dc, D-20261118-pj-62d3, D-20261115-pj-a988]
ai: options+critique
---
# First run: a notice about what is downloaded and a short walkthrough with mocked data

## Context

External audit item 23. Read from `desktop/src/screens/PlannerScreen.tsx`: data downloads lazily during the first real analysis, and only the files that analysis needs. The UI shows a progress bar (current file, MB, files done, total MB) and "Stored on this machine; works offline afterwards", but before it starts the user is not told how much will be downloaded, what it is or where it goes. The full store is about 3.4 GB (masks 879 MB, hazards 2,097 MB, slope and PSR 396 MB, kernels 46 MB, from the local manifests); the size of a typical first analysis was not measured.

## Framing

The user must not mistake a long first download for a frozen app, and should understand what the app does before it has real data.

## Options considered

pj stated a choice without asking for alternatives; no options table was shown.

## Decision

On first use the app shows a **notice** with a **short explanation of what will be downloaded**, and offers a **brief walkthrough of the app using mocked data** so the user can see how it works.

## Rationale

(Translated from pj's Spanish.) A notice, a brief explanation of what is downloaded, and a walkthrough of the app so the user can see how it works with mocked data (briefly).

## Checks raised

- None raised; pj asked to move to the next decision without the options table.

## Values

| Name | Value | Notes |
|------|-------|-------|
| first_run_notice | yes, with a short explanation of what is downloaded | |
| first_run_walkthrough | yes, brief, with mocked data labelled as mocked | labelling follows `D-20261115-pj-a988` |
| notice_content | what is downloaded, approximate size, storage location, progress, in the conventional first-run dialog | layout and wording delegated to the AI by pj; pj clarified this is interface, not how the download works |
| walkthrough_skippable | yes | delegated to the AI by pj |
| download_cancel_or_decline | cannot be cancelled or postponed | pj |
| stage_labels | downloading / processing / waiting | delegated to the AI by pj (follows audit item 23) |

## Later answers (pj, translated)

The first-run notice cannot be cancelled or postponed. I do not understand the content question; I take it as an interface matter, since how it works behind is already wired. As first-run screens usually work: a box in the centre that shows the download. If not, whatever; I do not think it is very important.

## Expected behavior and validation

(pj, translated.) It would be a mistake if the walkthrough were a waste of the user's time, or if the user did not find out what is going to be downloaded; pj thinks that with a brief walkthrough and a clear explanation there should be no problem.

## Consequences

- A first-run screen with the notice and the walkthrough; mocked data is labelled as such.
- Implied test, not stated by pj: a fresh install shows the notice before the first download starts.
