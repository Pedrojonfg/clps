---
id: U-20261115-pj-8420
person: pj
date: 2026-11-15T08:25:01Z
task: T-20261115-pj-2cbd
---
# S7 deep search — pj

## Concepts

| Concept | Role | Status | Source | Evidence | Next check |
|---------|------|--------|--------|----------|------------|
| Quickmap / Moon Trek / Horizons roles | warm-up | shaky | U-20261115-pj-b256 | Warm-up skipped again: pj said already answered many times and is clear; no new graded evidence this turn | next defend or when search claims cite mask vs smooth el |
| deep search over user ranges | core | demonstrated | D-54f0 | Chose dual modes on user grid; falsify if hill climb fails vs coverage | — |
| search vs learned model | core | demonstrated | D-54f0 | Rejected Ridge/GD-as-engine; locked discrete multi-start hill climb + enumerate | — |
| stopping rule / budget | core | introduced | D-54f0 | ETA per mode; concrete stop / N starts still open | next decide |
| silent incomplete search | hazard | introduced | D-54f0 | Optimized mode must not claim grid optimum; coverage mode may | — |
| multi-start placement | core | demonstrated | D-e3cf | Regular space-filling + user N; falsify via bad default | — |
| deep_search_start_default | core | introduced | D-e3cf deferred | Next decision; criteria briefing this turn | this turn |

## Notes

- Session opened for S7 after `D-48ee` closed the S6 tune gate; P14 still unset.
- Warm-up skipped at pj request (repeated question).
- Approach: user ranges in UI; wants simple explainable “ML” (GD / Ridge / Lasso); asked for guidance on optimizing with few variables.
- Cost probe 2026-11-15 (Site01, hazards off): mask ~0.5 ms; series+score window ~0.1 ms; sky dominates (~0.4–0.5 s/site for ~2 d). Extrapolated: 10×10 km×7 d ~1 min; 50×50 km×7 d ~23 min; 50×50×30 d ~1.5 h. Assumption “precomputed masks ⇒ search cheap” only half-true: masks yes, ephemeris per site no.
- Research brief (discrete black-box): local search / hill climb = discrete GD analogue (neighbourhood); SA / multi-start for multimodality; SMBO/BO when evals expensive; coarse→fine as explainable hierarchy. Sources: Toussaint black-box lecture; GFO optimizer-selection; OpenMDAO gradient-free notes.
