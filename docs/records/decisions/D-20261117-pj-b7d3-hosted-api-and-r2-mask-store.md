---
id: D-20261117-pj-b7d3
title: "Masks on R2; evaluator API hosted off pj's machine"
date: 2026-11-17T12:00:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: architecture
task: T-20261115-pj-5200
concepts: [static mask store, hosted evaluator, product reachable without pj's PC]
supersedes: [D-20261115-pj-3832]
relates: [D-20261115-pj-8c03, D-20261115-pj-4494]
ai: none
---
# Masks on R2; evaluator API hosted off pj's machine

## Context

`D-3832` deferred the mask API. `D-8c03` kept the evaluator on the client, but the desktop app
only works while a FastAPI process runs on pj's WSL. pj: that is unusable, solve it whatever it
violates.

## Decision

1. Horizon masks (the 1 km cap, ~880 MB) are static files in Cloudflare R2, served at
   `masks.pedrojon.com`, with a checksummed `manifest.json`. Clients fetch tiles on demand and cache them.
2. The evaluator FastAPI is hosted on a VPS (`deploy/api/`, Docker + Caddy, `api.pedrojon.com`).
   The desktop build bakes that origin (`VITE_API_BASE`). This reverses the "evaluator runs on the
   client" half of `D-8c03`; packaging the engine inside the app stays a later option.
3. First-person view gets a user toggle for the 2D panorama.

## Consequences

- The app works with pj's PC off. The VPS now bears compute cost; there is no auth or rate limit yet.
- The Pages demo stays mocked until a rate limit exists.
- `D-3832` ("mocks now, API later") is superseded.
