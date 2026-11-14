---
id: U-20261114-pj-5893
title: "S3/S4 engine spec session"
date: 2026-11-14T17:42:25Z
author: pj
task: T-20261114-pj-8138
concepts: [topographic horizon mask, visibility series]
---
# S3/S4 engine spec session

| Concept | Status | Evidence | Next check |
|---------|--------|----------|------------|
| topographic horizon mask | demonstrated | Named local relief blocking Sun despite small positive smooth-horizon elevation near south pole; reused without prompting | — |
| needs-adapted score | introduced | Chose Π Φ(slack/σ) + capped bonus; could not falsify; wants ratio cap experiment | tune β via score_layer1_tune |
| minima and feasibility | demonstrated | Chose layer-0 `min_continuous_lit_h` default 0; falsified via upstream S3 metric quality | — |
| success X/Y/Z | demonstrated | Accepted validation without golden week; X/Y/Z + unit + short E2E per D-1a46 | reopen on regression |