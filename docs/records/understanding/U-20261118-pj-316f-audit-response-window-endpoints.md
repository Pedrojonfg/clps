---
id: U-20261118-pj-316f
person: pj
date: 2026-11-18T16:45:11Z
task: T-20261118-pj-a670
---
# Window endpoints (audit response) — pj

## Concepts

| Concept | Role | Status | Source | Evidence | Next check |
|---------|------|--------|--------|----------|------------|
| sample vs interval | core | introduced | moonpark/visibility.py; D-20261118-pj-9413 | proposed last-minus-first for durations unprompted, noted hour 24 is the next day's hour 0; falsification answered with a criterion, not a failure condition | 2026-11-25 explain why 3 hourly dark samples bound the night between 2 h and 4 h and what changes at 10 min |
| pessimistic bound | core | introduced | D-20261118-pj-9413 | derived that the safe side flips for minimum limits after being shown the question; chose lower bound for light | 2026-11-25 state which bound each of the four limits uses |
| not evaluable vs favorable default | core | introduced | moon.py, pcp.py; D-20261118-pj-b3dc | asked whether the missing data was user input or program data, then refined the rule to block only hazard analyses when only hazard data is missing; falsifier given as frequency of the block, not a wrong-result condition | 2026-11-25 explain which analyses still run if only the temperature bin is missing and why PSR is different |
| climatology | core | shaky | D-20261114-pj-41a2; ODE PCP page | warm-up: said it is used because it is the one available (correct) but thought the map uses lunar time rather than local solar time | 2026-11-20 explain what the climatology number is and is not, and why local solar time is not the Earth hour of day |
| local solar time | prerequisite | introduced | SPICE et2lst; D-20261118-pj-633d | chose SPICE over own formula citing cost and not reinventing; falsifier given as cost/realism; asked to look up the Diviner convention | 2026-11-25 say how local solar time advances per Earth day on the Moon and why a 24 h window barely changes it |
| effective requirements | core | introduced | app.py; D-20261118-pj-75f1 | stated that searches using different requirements would mislead the user; chose warn-and-continue for unevaluable requirements and drop-and-count for cells without data; falsifier was cost, accepted | 2026-11-25 explain which list of requirements the search and the analysis each use and what the user sees when one is unevaluated |
| template vs manual edit | core | introduced | api.ts, app.py; D-20261118-pj-70ec | chose to send every field and relabel as Custom for honesty; gave no falsifier and asked to skip the options | 2026-11-25 say which seven fields the server ignored under a template and why the label must change |
| heuristic score vs probability | core | introduced | score.py; D-20261118-pj-1bc9 | stated the score orders sites and is not a probability of success; reused the compact-plus-expandable provenance pattern; falsifier not given | 2026-11-25 say what the sigma in the score is and why the product of terms is not a probability |
| cache identity | core | introduced | remote.py, publish_masks.py; D-20261118-pj-62d3 | reasoned that replacing, not adding, causes the problem; weighed storage cost; chose the version identifier as simplest effective check after being shown the three options | 2026-11-25 explain why same URL plus same size can hide a changed file and what the identifier fixes |
| first-run cost | core | introduced | PlannerScreen.tsx, store manifests; D-20261118-pj-23ab | chose a notice, a short explanation and a mocked walkthrough; falsifier: walkthrough wasted time or user not learning what is downloaded | 2026-11-25 say what a first real analysis downloads and what happens to hazard analyses if it is interrupted |
| offline promise | core | introduced | web/*.html; D-20261118-pj-d99f | chose to bundle libraries and promise only past analyses plus recompute on cached data; noted that new masks need a connection unprompted | 2026-11-25 list what works with no network and what does not |
| on-demand data cuts | core | introduced | terrain.py, publish_masks.py; D-20261118-pj-6fea | asked whether the mask pattern (download only what you use) applied to the DEMs, then chose precomputed cuts over range reads | 2026-11-25 explain why the mask is a horizon profile and cannot give a 3D ground, and what the cuts add |
| saved analysis | core | introduced | analysesStore.ts; D-20261118-pj-8625 | proposed saving the full result as files the user can delete; asked what is common and about permissions; chose Documents | 2026-11-25 explain what a saved analysis holds now and why opening one no longer recomputes |
| usage limits | core | introduced | app.py, deep.py; D-20261118-pj-cd33 | reasoned that everything runs on the user's PC so few limits are needed; proposed deriving the limits from tests | 2026-11-25 say which limit is strictly necessary and how the others will be found |
| release evidence | core | introduced | desktop-release.yml; D-20261118-pj-fc4d | chose to announce each OS only after testing it, with a retreat rule; deferred architectures and did not answer the test checklist | 2026-11-25 say what must be tested on each OS before announcing it and what an unsigned installer shows the user |
| stoppable searches | core | introduced | deep.py; D-20261118-pj-1454 | chose no hard time stop, a stop button and resumable runs | 2026-11-25 explain what stopping a search does and what is saved |
| delegated wording and UI details | core | debt | D-1bc9, D-23ab, D-8625, D-62d3 | pj delegated the score label text, first-run dialog layout, walkthrough skip, stage labels, folder name, recompute warning and update mechanism details to the AI | before release: read and approve those texts and screens |
| terrain gaps | core | introduced | grid.py, raster.py; D-20261118-pj-d90c | chose the unfavorable-side fill with a discreet notice for consistency with the earlier decisions; reading 1a; falsifier: too many false negatives | 2026-11-25 explain why a hole filled with the mean can make the horizon optimistic and what the new rule does |
| tile scheme for relief | core | introduced | terrain.py, manifests; D-20261118-pj-6fea | asked how problematic request count and manifest size are, then chose fixed-pixel tiles for coherence with the resolution schedule; falsifier: the setup becoming never-ending | 2026-11-25 explain why tile size in pixels keeps files similar across resolutions |

## Notes

- Warm-up on debts (climatology, nodata fill) not asked this session; item 3 on the agenda (local solar time) touches climatology.
