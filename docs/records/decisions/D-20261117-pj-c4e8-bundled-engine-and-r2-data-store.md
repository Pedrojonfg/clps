---
id: D-20261117-pj-c4e8
title: "Bundled engine (Tauri sidecar); masks, kernels and hazards from R2"
date: 2026-11-17T12:00:00Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: architecture
task: T-20261115-pj-5200
concepts: [client compute, static data store, sidecar packaging]
supersedes: []
relates: [D-20261115-pj-8c03, D-20261115-pj-3832, D-20261115-pj-4494]
ai: none
---
# Bundled engine (Tauri sidecar); masks, kernels and hazards from R2

## Context

`D-8c03` says the optimization/evaluation runs on the client and the remote only serves data.
The desktop app still needed a FastAPI process started by hand on pj's WSL, so it was unusable
for anyone else. An earlier draft of this work moved the evaluator onto a VPS; pj corrected that:
the computation stays on the client, the remote only gives back data. That draft is withdrawn.

## Decision

1. **The remote is a static store** (Cloudflare R2 at `masks.pedrojon.com`), not an API process:
   the 1 km mask cap (`cap_1km/`) and the rest of the runtime data (`data/`: SPICE kernels,
   Diviner PCP bins, LDSM and LPSR rasters). Checksummed manifests; clients fetch what a request
   needs and cache it. This fulfils `D-3832` ("API later").
2. **The evaluator ships inside the desktop app** as a PyInstaller folder started by Tauri on a
   free loopback port and stopped on exit (sidecar). The UI asks the shell for that origin.
3. **Without DEMs on the machine, a site snaps to its nearest 1 km cap cell** instead of being
   computed from the DEM. Fine detail below 1 km is not available to client machines.
4. The first-person view has a user toggle for the 2D panorama.

## Consequences

- Nothing of pj's has to be running. The first real evaluation downloads data (hazard rasters
  and PCP bins up to about 0.7 GB, kernels 44 MB, masks per tile ~30 MB), then works offline.
- Installers are per OS (PyInstaller does not cross-compile); the engine folder is large.
- The Pages demo stays mocked.
