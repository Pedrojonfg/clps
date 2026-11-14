---
id: D-20261114-pj-5994
title: "Precompute on pj's PC for the demo, then a Hetzner CX43 for the full cap and serving"
date: 2026-11-14T13:04:08Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: dependencies & ops
task: T-20261114-pj-12b7
concepts: [hosting]
supersedes: []
relates: [D-20261114-pj-f369, D-20261114-pj-4ffe]
ai: recommendation
---
# Precompute on pj's PC for the demo, then a Hetzner CX43 for the full cap and serving

## Context

`D-20261114-pj-f369` needs horizon masks precomputed over 80–90°S: 1 km spacing for the demo (~289 k masks) and 100 m later (~28.9 M masks). Measured cost: ~150 ms per mask on one core, 22 masks/s on pj's PC (Ryzen 5 PRO 215, 12 threads, 7 GB RAM). pj accepts a fixed server of about 20 EUR/month and is not commercializing the project. Prices checked 2026-11-14 (Hetzner after the 15 Jun 2026 rise, excluding VAT; hourly billing capped at the monthly price).

## Options considered

1. **pj's PC**: free; demo cap in ~4 h; 100 m cap in ~15 days of continuous running; 7 GB RAM forces tiled DEM reads.
2. **Hetzner CX43** (8 shared vCPU, 16 GB): 15.99 EUR + 0.50 EUR IPv4 per month (~20 EUR with Spanish VAT); estimated 7–15 masks/s; 100 m cap in ~26–52 days; also serves the app. Limited stock.
3. **Hetzner CAX31** (ARM, 8 vCPU, 16 GB): 20.99 EUR; same role if the CX43 is out of stock.
4. **Hetzner CX53** (16 vCPU, 32 GB) billed hourly for bursts: 29.49 EUR/month cap; faster, more expensive if left running.
5. **Oracle Always Free A1** (2 OCPU, 12 GB): free; several times slower; capacity often unavailable.

## Decision

**Demo precompute on pj's PC; one paid month of a Hetzner CX43 (CAX31 if out of stock) for the 100 m cap and for serving, with a second month if the run does not finish.**

## Rationale

AI recommendation accepted by pj: cheapest path that fits the budget; the demo does not wait for a server; the CX43 has enough RAM for tiled 10 m and 20 m mosaics and can keep serving after the run. pj: "the paid server month is used for the cap at 100 m (worst case, I'll pay one more month); tonight, once the demo site is chosen, we set it computing on my PC with less spacing and more resolution."

## Values

| Name | Value | Notes |
|------|-------|-------|
| precompute_host_demo | pj's PC | Tiled DEM reads (7 GB RAM) |
| precompute_host_full | Hetzner CX43; CAX31 if out of stock | ~20 EUR/month with VAT |
| server_months_budget | 1, a second if the 100 m run is unfinished | |
| server_benchmark | first hour on the server measures masks/s before committing to the full run | Estimates are ±2× |

## Consequences

- PGDA DEMs are downloaded once to the server (the 5 m mosaic does not support HTTP range reads).
- Cesium ion tokens and any server credentials stay out of git.
