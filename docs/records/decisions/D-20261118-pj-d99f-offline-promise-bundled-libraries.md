---
id: D-20261118-pj-d99f
title: "Offline: bundle the viewer libraries and promise only past analyses and recompute on downloaded data"
date: 2026-11-18T18:00:41Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261118-pj-a670
concepts: [offline promise]
supersedes: []
relates: [D-20261118-pj-b3dc, D-20261118-pj-23ab, D-20261115-pj-de70]
ai: options+critique
---
# Offline: bundle the viewer libraries and promise only past analyses and recompute on downloaded data

## Context

External audit item 24. The README says the app "works offline afterwards". Read from `web/firstperson.html` and `web/map.html`: Cesium (first-person 3D) and Three.js (region map) load from `cdn.jsdelivr.net`, so those views do not load offline; the first-person view falls back to the 2D panorama. The analysis, charts and 2D panorama work offline when the data is already cached. Textured 3D also needs Cesium ion over the network and a token.

## Framing

Minimal external dependency, and no promise the app cannot keep.

## Options considered

pj stated a choice without asking for alternatives; no options table was shown.

## Decision

The Cesium and Three.js libraries are **packaged inside the app**. Offline, the app promises only two things: viewing **past analyses** and **recomputing** with data **already downloaded**. Nothing more is promised. New masks need a connection.

## Rationale

(Translated from pj's Spanish.) Yes, we package the libraries inside. We promise viewing past analyses and recomputing with data that is already downloaded, nothing more than that (because I understand that loading new masks needs a connection). The rationale is simple: minimal external dependency, but not lying about it. I do not think offline mode is important enough to overdo it.

## Checks raised

- None raised; pj asked to proceed after answering the falsifier.

## Values

| Name | Value | Notes |
|------|-------|-------|
| bundled_libraries | Cesium and Three.js shipped with the app | removes the jsdelivr dependency for the viewers |
| offline_promise | view past analyses; recompute with already downloaded data | nothing else |
| textured_3d_offline | not promised | still needs Cesium ion and network |
| offline_test | deferred to just before publishing | pj |
| readme_offline_wording | deferred to just before publishing | pj |

## Later answers (pj, translated)

The offline test and the README rewrite are deferred to the moment when we think about publishing.

## Expected behavior and validation

(pj, translated.) It would be a mistake if users liked to use the app offline on a laptop that did not want to download those packaged libraries; that user is not pj's target, so it can proceed.

## Consequences

- The installer grows by the size of the libraries.
- The CSP added in PR #34 can drop `cdn.jsdelivr.net` from `script-src`/`style-src`/`connect-src` once the libraries are local.
- README "works offline" must be reworded to the two promised cases (at release).
