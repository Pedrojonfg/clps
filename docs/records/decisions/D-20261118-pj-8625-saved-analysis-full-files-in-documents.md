---
id: D-20261118-pj-8625
title: "Saved analysis: the full result as a file in Documents, deletable by the user"
date: 2026-11-18T21:32:50Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261118-pj-a670
concepts: [saved analysis]
supersedes: []
relates: [D-20261118-pj-62d3, D-20261118-pj-b3dc, D-20261118-pj-75f1]
ai: options+critique
---
# Saved analysis: the full result as a file in Documents, deletable by the user

## Context

External audit item 33. Read from `desktop/src/lib/analysesStore.ts`: a saved analysis keeps the form and a five-field summary in the browser's local storage (maximum 40), and opening one recomputes it, so the result can differ and the saved copy is lost if the site data is cleared. A full result measured with real data takes 34 KB (24 h at 10 min); a 30-day window at 10 min is estimated at about 0.5 MB (not measured; the API refused 31 days). `D-20261118-pj-62d3` requires warning on recompute when data changed and keeping analyses across app updates.

## Framing

A saved analysis should be the result the user saw, easy to find and delete, not a recipe that may give another answer.

## Options considered

1. **A, browser storage, form and summary (current)**: consequence: result lost, recomputed on open.
2. **B, full files in the app data folder**: consequence: survives updates, not visible.
3. **C, full files in Documents/<app name>**: consequence: visible and shareable; needs an explicit permission for that folder.
4. **D, app data folder plus an Export button**: consequence: sharing is a separate action.

## Decision

**C.** The full result is saved as a file in `Documents/<app name>/` on the user's computer, and the user can delete it. Opening a saved analysis shows the stored result; a "Recalculate" action warns that the result may differ. Each file carries the data version, the app version and a file format version. A damaged file or a full disk gives a clear message and does not stop the others from opening.

## Rationale

(Translated from pj's Spanish.) Documents seems the most convenient, though there may be a permissions problem to create or access the folder; I like C: simple, easy to use. I understand the checks and I accept them.

## Checks raised

- The folder needs an explicit permission on `$DOCUMENT/<folder>` → pj accepted.
- The file must hold data version, app version and format version → pj accepted.
- Opening shows the stored result, with Recalculate and a warning → pj accepted.
- Damaged file or full disk must give a clear message → pj accepted.

## Values

| Name | Value | Notes |
|------|-------|-------|
| saved_analysis_content | full result (series, sky, mask, score, hazards) plus the form | pj: "save all the data" |
| saved_analysis_location | Documents/<app name>/ | |
| saved_analysis_permission_scope | only that subfolder | proposal accepted by pj |
| saved_analysis_metadata | data version, app version, file format version | needed by `D-20261118-pj-62d3` |
| open_behaviour | show the stored result; Recalculate with a warning | |
| delete_by_user | yes | in the app, or by hand |
| folder_name | the app's name | delegated to the AI by pj ("whatever") |
| file_format | one JSON file per analysis | pj |
| max_saved | no maximum | pj; cleanup by inactivity may come in a later version |
| migration_of_existing_saves | analyses already in browser storage are not migrated; they are discarded | pj: "you can scrap them, I do not care" |

## Later answers (pj, translated)

Format: probably JSON, one per analysis. Folder name: whatever. Maximum saved: there is no maximum; later, for future versions, perhaps some cleanup for inactivity. (Still unanswered: what happens to analyses already in browser storage.)

The analyses already saved in the browser: you can get rid of them, honestly I do not care.

## Expected behavior and validation

(pj, translated.) It would be a mistake if the files took up a lot of space and it were better for the user to regenerate them; pj says they should not take up much.

## Consequences

- The file-system permission and a save/open/delete layer replace `analysesStore.ts` browser storage.
- Past analyses stay readable after a forced app update (`D-20261118-pj-62d3`); the format version makes that possible.
- Implied test, not stated by pj: save, restart, open shows the same numbers without recalculating.
