# CLPS / lunar site×time evaluator (portfolio)

Solo portfolio project inspired by the NASA Space Apps Challenge 2026 brief **[CLPS Lunar Mission Browser](https://www.spaceappschallenge.org/2026/challenges/clps-lunar-mission-browser/)**. Not a contest team entry.

This repository holds **product definition** (decision records + learning notes). Application code is not started yet. Engine/method decisions (score formula, search algorithms, data pipeline, layer-B models) are **deferred** to a future decision ledger.

## Challenge heritage (what NASA asked)

South-pole missions face extreme **lighting** and **communication** constraints. Existing tools (e.g. Quickmap, Moon Trek, JPL Horizons) can answer where the Sun and Earth sit relative to a landing site’s horizon, but their interfaces are hard to use for **rapid scenario comparison**.

The brief’s core ask: compare **landing sites and dates**, visualizing **Sun and Earth vs the local horizon** for **solar power** and **direct-to-Earth (DTE)** windows.

Full statement archive: [`docs/sources/challenge-statements/clps-lunar-mission-browser.md`](docs/sources/challenge-statements/clps-lunar-mission-browser.md).

### Layer A vs layer B

| Layer | In product? | Examples |
|-------|-------------|----------|
| **A — Local sky at the site** | Yes (core) | Sun/Earth elevation vs horizon; power & DTE windows |
| **B — Surface / ops hazards** | Yes (portfolio ambition) | Temperature, dust, related site hazards (`D-b8d3`) |
| **Flight dynamics** | No (except optional filter) | Full Earth–Moon trajectory / ΔV optimization out; approach accessibility filter allowed |

---

## Product decisions (current)

| ID | Title | Domain |
|----|-------|--------|
| [`D-20261111-pj-60ab`](docs/records/decisions/D-20261111-pj-60ab-product-question.md) | Product question (unchanged) | problem framing |
| [`D-20261114-pj-7e2a`](docs/records/decisions/D-20261114-pj-7e2a-project-frame-solo-portfolio.md) | Solo portfolio frame | problem framing |
| [`D-20261114-pj-3c91`](docs/records/decisions/D-20261114-pj-3c91-audience-portfolio.md) | Audience (supersedes `D-ea51`) | problem framing |
| [`D-20261114-pj-9f04`](docs/records/decisions/D-20261114-pj-9f04-scope-portfolio.md) | Portfolio scope & done (supersedes `D-5cf6`) | scope & success criteria |
| [`D-20261114-pj-b8d3`](docs/records/decisions/D-20261114-pj-b8d3-layer-b-bodies-trajectory.md) | Layer B / trajectory / multi-body | problem framing |

Task: [`T-20261114-pj-a1b2`](docs/records/tasks/T-20261114-pj-a1b2-reopen-product-portfolio.md).

---

## Who it is for (`D-3c91`)

- **Primary audience:** technical portfolio viewer (hiring / peer engineer reading the demo).
- **Domain depth bar:** mission-planner-grade calculations and metrics.
- **UI default:** technical + explainable (provenance required). Friendly educator skin optional later — not v1 done.

---

## What question the product answers (`D-60ab`, kept)

**Scored evaluation under planner constraints**, with search:

1. Planner provides **date/time** (and site) plus **flexibility / thresholds** (max time without sun, without radio, need both, weights…).
2. System returns a **score**; on minima fail → search toward nearest feasible; inspect **neighborhood** for gains.
3. **Deep-search mode** over user-specified time–space ranges (name TBD).
4. **Visualizations** accompany the loop; usefulness over cosmetics.

Four visibility cases (mental model):

| Case | Sun above horizon | Earth above horizon |
|------|-------------------|---------------------|
| Both | yes | yes |
| Sun only | yes | no |
| Radio only | no | yes |
| Neither | no | no |

---

## Scope for portfolio v1 (`D-9f04` + `D-b8d3`)

| Bucket | Includes |
|--------|----------|
| **Core** | Needs-adapted score; explained thresholds + provenance; useful viz set; local neighborhood search; deep-search mode |
| **Layer B (surface)** | Temperature, dust, related site hazards (models in engine ledger) |
| **Architecture** | Moon beachhead; **body-agnostic** providers so Mars/others can be a later pack |
| **Out of v1** | Full trajectory optimization; native mobile; Mars feature parity |
| **Optional bridge** | Approach / accessibility **filter** (consumes trajectory products; does not compute them) |

**Definition of done:** defendable portfolio demo — backend useful under explicit **X, Y, Z** (engine ledger).

---

## Explicitly not decided yet (engine ledger)

- Score formula and success metrics **X, Y, Z** (including how temp/dust enter)
- Neighborhood / deep-search algorithms and stopping rules
- Data path (Horizons vs precomputed maps vs LOLA/DEM horizon)
- Layer-B model choices and validation level
- Public **claims** wording

Domain brief: [`docs/research/briefs/research-brief-clps-domain.md`](docs/research/briefs/research-brief-clps-domain.md).

---

## Repo layout

```
docs/records/          decision-flow records (project, people, tasks, decisions, understanding)
docs/sources/          archived challenge text and raw fetches
docs/research/briefs/  research notes
```

Language: **repo English**; chat language per person (`docs/records/project.md`).
