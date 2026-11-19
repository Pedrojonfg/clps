---
id: D-20261118-pj-6fea
title: "3D relief on a normal install: precomputed DEM cuts in the data store, fetched per site"
date: 2026-11-18T18:08:14Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261118-pj-a670
concepts: [on-demand data cuts]
supersedes: []
relates: [D-20261118-pj-62d3, D-20261118-pj-23ab, D-20261118-pj-d99f, D-20261115-pj-671e]
ai: options+critique
---
# 3D relief on a normal install: precomputed DEM cuts in the data store, fetched per site

## Context

External audit item 25. Read from `moonpark/terrain.py` and `scripts/publish_masks.py`: `/terrain` builds the first-person ground from LOLA elevation models found only in the local `data/dem/` folder (about 10.4 GB: 10 m 4.8 GB, 20 m 2.6 GB, the rest 3 GB), and the public store publishes only slope and PSR. On a normal install `/terrain` answers 503, so the README's "3D without a token" works only on the development machine. The main LDEM files are already tiled (512 px blocks, compressed, with overviews), so both range reads and cutting are technically possible. Masks themselves are directions (a horizon profile) and cannot give a ground mesh; the region map uses bundled images and does not need `/terrain` or ion.

## Framing

The 3D experience on a normal install should match what is announced, without asking the user for 10 GB.

## Options considered

1. **Path 1, range reads of the published TIFFs**: assumes partial network reads are enough; consequence: no whole-file sha256 check and nothing kept for offline.
2. **Path 2, precomputed cuts published like the masks**: assumes a cutting script is worth maintaining; consequence: manifest, sha256, versioning and offline cache all fit; more files in the store.
3. **Do not offer own relief**: consequence: the 2D panorama (and ion with a token) remain.

## Decision

**Path 2.** The elevation models are cut into pieces, published in the data store with a manifest and sha256 like the masks, and the client downloads only the pieces its site needs, so `/terrain` works on a normal install.

## Rationale

(Translated from pj's Spanish.) Path 2 is the best for the user, and we are not going to change the cutting script much in the near future, so the maintenance cost is not really one.

## Checks raised

- Path 1 cannot verify a whole-file sha256 (conflict with `D-20261118-pj-62d3`) and leaves nothing for offline use → pj chose path 2.
- Cutting script maintenance → pj does not expect many changes.

## Values

| Name | Value | Notes |
|------|-------|-------|
| relief_delivery | precomputed cuts in the data store, per-site download | |
| relief_manifest_and_checks | manifest with version id and sha256 after download | follows `D-20261118-pj-62d3` |
| cut_scheme | every model cut into tiles of the same size in pixels (the AI's example: 512 x 512, the source files' internal block size), so tile size in km scales with resolution (about 2.5 km at 5 m, 10 km at 20 m, 41 km at 80 m); one manifest per model | pj chose this option as the most coherent with earlier decisions (`D-20261114-pj-f369`, distance-graded resolution schedule); the 512 px value is the AI's example, not stated by pj |
| cut_zone_per_site | the windows `terrain.py` already reads per model (up to 30 km radius, 15 km at 10 m, 7.5 km at 5 m) | AI reading of the current code; about 65 MB per site (estimate) |
| site_tiles_5m | whole files | pj: no reason to cut them (AI: they are 40 MB each, 160 MB in total, uncompressed strips; the only possible gain is converting them to compressed tiles) |
| redistribution_licence | the AI researches it in depth as part of the implementation, and acts accordingly | pj. Status before that: unverified; the PGDA product page (products/78) states no licence, usage terms or citation format in the third of the page read, and links a LOLA_5mpp README not read |
| readme_3d_wording | deferred — release-time rewrite; the 2D panorama is the fallback | |

## Later answers (pj, translated)

I suppose the 5 m mosaics go whole; I do not understand why they should be cut; if you think they should be cut for some reason, explain it. About the redistribution licence: verify it and tell me what happens there.

On the licence of the elevation data: as part of the implementation process, you do a deep investigation. When I send you to implement, you investigate it and act accordingly.

## Later answers (pj, translated)

The option of tile size in pixels is the most coherent with previous decisions.

## Expected behavior and validation

(pj, translated.) It would be a mistake if the team were updating the cutting script all day; pj says that will not be the case.

For the cutting scheme (pj, translated): it would be a mistake if so many things had to be uploaded and precomputed to R2 that the process of setting it all up in the API became a never-ending story. Implied check, not stated by pj: measure the time of a full cut and publish.

## Consequences

- New cutting and publishing script for the elevation models; `terrain.py` must read through the store like the other data.
- First-run notice (`D-20261118-pj-23ab`) should say that a first 3D view downloads relief for that site.
- Implied test, not stated by pj: on a clean install with no local DEMs, `/terrain` returns relief for a covered site.
