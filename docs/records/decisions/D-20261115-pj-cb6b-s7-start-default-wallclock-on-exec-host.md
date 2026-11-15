---
id: D-20261115-pj-cb6b
title: "Start default follows wall-clock budget on the execution host"
date: 2026-11-15T10:11:24Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261115-pj-2cbd
concepts: [deep_search_start_default, stopping rule / budget, multi-start placement]
supersedes: []
relates: [D-20261115-pj-e3cf, D-20261115-pj-54f0, D-20261114-pj-5994]
ai: options+critique
---
# Start default follows wall-clock budget on the execution host

## Context

`D-e3cf` requires a concrete default for the regular space-filling start mesh when the user does not set N/density. Session criteria included wall-clock budget, ~5–10 starts per dimension, spacing vs climb neighbourhood, and honest ETA. Hosting today points at a Hetzner CX43 for serving (`D-5994`), but pj wants a later conversation on whether deep search should run on that server or on the planner’s own machine with masks supplied from the server.

## Framing

Tie the default effort to how long the run may take on the machine that actually evaluates scores, not to a density copied from another product.

## Options considered

1. **A — Fixed density** (~5/axis or fixed km/h step), ignore hardware.
2. **B — Wall-clock budget on the hardware of whoever/whatever executes the search** (T_max and execution host still to pin).
3. **C — Fraction of grid cells** (e.g. √N), hardware-agnostic.
4. **D — No numeric default**; user must always choose N.

## Decision

**B.**

## Rationale

pj (2026-11-15): Wall-clock budget based on the hardware the space-agency person is using. Confirmed B, but later we should talk about whether in the end we want everything to run on a web app with the load on our server, or we just want to have all the masks on the server (or whatever) and then have things run on their own computers. Because in the end the people who will use this product, who are not the average person but people with fairly powerful computers, will get much better performance using their own hardware. And besides, that way my part is almost free and I am not suffering the load of doing very expensive calculations that they could do with the hardware they already have.

## Checks raised

- Agency users with very bad hardware (unlikely) → accepted as low-probability product risk.
- Cannot access hardware info → depends on execution host; browser inventory is weak; server-side or a short calibration probe is the practical read. pj expected access to be sensible for the execution host.
- T_max still unset → deferred to the next value on this task.
- Server vs client execution → deferred explicit decide (architecture / dependencies & ops); until then “execution host” means wherever the score loop runs.

## Values

| Name | Value | Notes |
|------|-------|-------|
| deep_search_start_default_basis | wall_clock_budget_on_execution_host | Densest regular mesh that fits the budget; T_max locked in `D-8a25` |
| deep_search_execution_host | deferred — later decide (server-heavy web vs masks-on-server + local compute) | pj: discuss later; affects whose hardware is measured |
| deep_search_start_default_calibration | short_probe_or_known_host_cost | e.g. time one site sky+score on the execution host |

## Expected behavior and validation

pj (2026-11-15): That the agency people had very bad hardware (not probable), or that one could not access that information about their hardware (which I understand does not make sense, right?).

## Consequences

- Implementation densifies/sparsens the regular start grid to meet T_max on the execution host (with ETA).
- Do not assume the planner’s laptop is the host until `deep_search_execution_host` is decided.
- Agenda later: server-side deep search vs distribute masks / run locally (cost to pj vs performance for agencies).
