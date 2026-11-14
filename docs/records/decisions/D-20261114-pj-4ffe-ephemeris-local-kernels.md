---
id: D-20261114-pj-4ffe
title: "Sun/Earth geometry computed locally from kernels; Horizons as test oracle"
date: 2026-11-14T11:40:01Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: data & sources
task: T-20261114-pj-12b7
concepts: [ephemeris, topographic horizon mask]
supersedes: []
relates: [D-20261114-pj-d7d9, D-20261114-pj-b8d3, D-20261111-pj-60ab]
ai: options+critique
---
# Sun/Earth geometry computed locally from kernels; Horizons as test oracle

## Context

The score (`D-20261111-pj-60ab`) needs Sun and Earth azimuth/elevation for every site × time evaluated, including local and deep search over many combinations. JPL ephemerides can be consumed by querying Horizons over HTTP (measured 2026-11-14: one site, one month, 6 h step, 121 rows ≈ 1 s; fair use requires one request at a time, caching, no browser calls) or by loading the published kernel files in a library and computing locally. pj accepts server deployment. Portfolio scope governs (`D-20261114-pj-d7d9`).

## Framing

Trade evaluation throughput and learning value against implementation time and the risk of silent geometry errors (frames, apparent vs geometric positions, ephemeris version).

## Options considered

1. **A — Horizons per request, cached on the server**: assumes few combinations are needed; consequence: no kernels; search throttled by fair use.
2. **B — Horizons tables downloaded once and stored**: assumes the site/time grid is known in advance; consequence: fast reads; anything off-grid needs new requests.
3. **C — Local kernels**: assumes kernels and frames can be learned; consequence: no external limit; correctness is on us.
4. **D — Local kernels for the score, Horizons to cross-check selected cases**: as C, plus a few requests; consequence: two independent paths for the smooth horizon.

## Decision

**Local kernels compute the geometry (C), validated by a tolerance test against Horizons (D-style).** If the test passes in all cases, the product computes exclusively with local kernels; at most a minimal runtime cross-check, possibly only of the solution proposed by local/deep search.

## Rationale

"Much lower cost per calculation (from the brief), and I genuinely want to understand how the calculations are done — in the end, the project is also for learning. We compute it ourselves, we test with a tolerance against Horizons; if it works well in all cases, the final product computes only on our side, without cross-checking (or with minimal cross-checking, maybe only of the solution proposed by local/deep search)."

## Checks raised

- "Lower cost per calculation" came from the AI's explanation → recorded as "(from the brief)"; the learning motive is pj's.
- Falsification is about pj's capacity, not about whether the numbers are right; a frame or sign error gives plausible wrong numbers near a 1° Sun → pj: add a tolerance test against Horizons.
- Falling back to Horizons on Sunday throttles deep search under fair use; switching is cheap only behind a provider interface (`D-b8d3`) → not answered separately.
- Library (NAIF SPICE via SpiceyPy vs Skyfield), frame and kernel version are still open → agenda item 5.

## Values

| Name | Value | Notes |
|------|-------|-------|
| ephemeris_source | local_kernels | Behind the ephemeris provider seam (`D-b8d3`) |
| horizons_role | test_oracle | Smooth-horizon az/el only; saved fixtures, no network in tests |
| ephemeris_test_tolerance_deg | deferred — set after the first comparison once conventions (ephemeris version, apparent vs geometric, lunar frame, site radius) match | |
| ephemeris_test_cases | deferred — sites × epochs defined when the test is written | "All cases" = this set |
| runtime_horizons_crosscheck | deferred — none, or only the search-proposed solution; decide after the test passes | Server-side only if used |
| ephemeris_library | deferred — agenda item 5 (with frame and kernel version) | |

## Expected behavior and validation

"Not being able to understand or do the calculations, or not having time to implement it; in that case we change this without problem."

## Consequences

- Horizons does not validate terrain blocking; the DEM horizon mask needs its own check (agenda item 3).
- A failing or unfinished local path falls back to Horizons through the same provider interface, with throttled search.
- Saved Horizons tables live in the repo as fixtures, requested once with an application-specific User-Agent.
