# CLPS Lunar Mission Browser (team product)

NASA Space Apps Challenge 2026 — challenge **[CLPS Lunar Mission Browser](https://www.spaceappschallenge.org/2026/challenges/clps-lunar-mission-browser/)**.

This repository currently holds **product definition** (decision records + learning notes). Application code is not started yet. Engine/method decisions (score formula, search algorithms, data pipeline) are **deferred** to a future decision ledger.

## Challenge (what NASA asks)

South-pole missions face extreme **lighting** and **communication** constraints. Existing tools (e.g. Quickmap, Moon Trek, JPL Horizons) can answer where the Sun and Earth sit relative to a landing site’s horizon, but their interfaces are hard to use for **rapid scenario comparison**.

**Your challenge is to** build an intuitive tool so mission planners, educators, and the public can **compare landing sites and dates**, visualizing **Sun and Earth vs the local horizon** to assess:

- **solar power** potential, and  
- **direct-to-Earth (DTE)** communication windows.

Full statement archive: [`docs/sources/challenge-statements/clps-lunar-mission-browser.md`](docs/sources/challenge-statements/clps-lunar-mission-browser.md). Official **Resources** tab was empty when archived (2026-11-11).

### Layer A vs layer B

| Layer | In our product focus | Examples |
|-------|----------------------|----------|
| **A — Local sky at the site** | Yes | Sun/Earth elevation vs horizon; power & DTE windows |
| **B — Full landing campaign** | Only if time + track rules allow (`decidable`) | Temperature, dust, trajectories, EDL roughness |

Geometry primer (LaTeX source; compile locally): [`docs/learning/clps-horizon-geometry.tex`](docs/learning/clps-horizon-geometry.tex).

---

## Product decisions (accepted)

| ID | Title | Domain |
|----|-------|--------|
| [`D-20261111-pj-ea51`](docs/records/decisions/D-20261111-pj-ea51-audience-positioning.md) | Audience and positioning | problem framing |
| [`D-20261111-pj-60ab`](docs/records/decisions/D-20261111-pj-60ab-product-question.md) | Product question | problem framing |
| [`D-20261111-pj-5cf6`](docs/records/decisions/D-20261111-pj-5cf6-scope-48h.md) | 48h scope & definition of done | scope & success criteria |

Task that produced them: [`T-20261111-pj-c84f`](docs/records/tasks/T-20261111-pj-c84f-define-project.md) (product ledger closed; engine items deferred).

---

## Who it is for (`D-ea51`)

- **Primary user:** mission **planner** — backend depth of a real planning tool (constraints, scores, search).
- **Same product, secondary users:** **educators** and **general power users** — not a separate toy app; they are served by an **explainable, approachable UI** (provenance of each datum, clear viz).
- **UI modes:**
  - **Default:** friendly + explainable.
  - **Fallback:** more technical UI if friendliness slows a planner’s normal workflow — **without** dropping explainability.

Intent for viz modalities: **2D** and **projective 3D** (exact set cut by scope below).

---

## What question the product answers (`D-60ab`)

Not “pretty map only.” The product is **scored evaluation under planner constraints**, with search:

1. Planner provides **date/time** (and site) plus **flexibility / thresholds** on outcomes, e.g.:
   - max time without sunlight,
   - max time without radio (Earth below horizon),
   - requirement that sun **and** radio overlap,
   - relative weights / other thresholds.
2. System returns a **score**.
   - If **minima fail** → score can be **zero**, then search over nearby **date/time** (and related inputs) for the **nearest feasible** case.
   - Inspect **neighborhood** of the current inputs for a **substantial** score improvement.
3. **Deep-search mode** (name TBD): user gives one or more **time–space ranges**; system seeks a **global** maximum under the same score logic.
4. Score design (later, engine ledger) should reward staying **away from thresholds** and improving sun / radio / both-at-once windows.
5. **Visualizations** accompany the loop; usefulness over cosmetics.

**Falsification (owner):** this product idea fails if local search is never conclusive, or if no reliable score can be built from planner needs — then fall back toward compare-only / hybrid.

Four visibility cases (mental model for windows):

| Case | Sun above horizon | Earth above horizon |
|------|-------------------|---------------------|
| Both | yes | yes |
| Sun only | yes | no |
| Radio only | no | yes |
| Neither | no | no |

DTE means **direct** radio to Earth (no relay). Relay satellites change the problem; the challenge centers on horizon geometry for DTE.

---

## Scope for the hackathon (`D-5cf6`)

| Bucket | Includes |
|--------|----------|
| **Must** | One visualization; **needs-adapted score**; **explained thresholds** |
| **Stretch** | Local search; global maximization (deep mode); friendly UI; additional visualizations |
| **Decidable** (time / post-hackathon; check track compliance) | Temperature; dust; trajectories |
| **Out** (or post-hackathon) | Native mobile app |

**Definition of done (ambitious):** must **and** stretch delivered, and the **backend works well** — useful outcomes **X, Y, Z** to be defined in the engine/metrics ledger.

**Risk (owner):** over-scoping so the engine does not actually work well. Schedule accordingly.

Note: friendly UI is **stretch** here, while `D-ea51` treats it as the **default** mode — Sunday may ship technical + explainable without full “friendly” polish.

---

## Explicitly not decided yet (engine ledger)

Open a separate decision-flow task for:

- Score formula and success metrics **X, Y, Z**
- Neighborhood / deep-search algorithms and stopping rules
- Data path (Horizons vs precomputed maps vs LOLA/DEM horizon)
- Technical validation level and public **claims**
- Team roles / recruitment plan

Domain brief (research): [`docs/research/briefs/research-brief-clps-domain.md`](docs/research/briefs/research-brief-clps-domain.md).

---

## Repo layout

```
docs/records/          decision-flow records (project, people, tasks, decisions, understanding)
docs/sources/          archived challenge text and raw fetches
docs/research/briefs/  research notes
docs/learning/         geometry primer (.tex; PDF gitignored)
```

Language: **repo English**; chat language per person (`docs/records/project.md`).

---

## Compile the geometry primer

```bash
cd docs/learning
pdflatex clps-horizon-geometry.tex
```

Generated PDF and LaTeX auxiliaries are **not** tracked in git.
