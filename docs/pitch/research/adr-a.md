# ADR digest A (D-20261111-* and D-20261114-* through 9f04)

Paths: docs/records/decisions/<id>-*.md

## 1. One line per ADR

- **5cf6** 48h hackathon scope: must/stretch/decidable/out. *Superseded* by 9f04.
- **60ab** Product question: score plus constrained search (local, then a "deep research" mode). Accepted. Still the north star.
- **ea51** Dual audience: planner-depth backend with a friendly UI for educators. *Superseded* by 3c91.
- **050d** Dust = Metzger (2024) soil-resistance proxy with Apollo-average soil and PGDA slope. Accepted.
- **1a46** No golden week-long CI file. X/Y/Z plus unit tests and a short E2E suffice. Accepted.
- **3c91** Audience = technical portfolio viewer, with a planner-depth backend. Accepted. Supersedes ea51.
- **41a2** Temperature = Diviner polar seasonal local-time climatology. Accepted.
- **41fa** Success X/Y/Z. Accepted. Supersedes 9f04 for `success_xyz` only.
- **4ffe** Sun/Earth geometry from local SPICE kernels, with Horizons as test oracle. Accepted.
- **52bd** S6 validation = synthetic tests plus one Site01 search E2E. Accepted.
- **5577** Infeasible candidates rank by R×bonus. UI shows a zero plus an "inside the impossible" score. Accepted. Settles a deferral in de42.
- **5994** Precompute on the PC for the demo, then a Hetzner CX43 for the 100 m cap and serving. Accepted.
- **5cfa** Temperature and dust limits are layer-0 fail-close. Accepted.
- **6ce5** Bonus uplift capped at 30% of R (was 10%). Accepted. Overrides 7520's cap value.
- **72bc** Local space search: 5 km neighbourhood on the 1 km grid, always scanned. Accepted.
- **7520** Layer-1 = R = ∏Φ(slack/σ) × (1+β·B), capped. Accepted. Supersedes de42.
- **7af3** Layer-0 gate on `min_continuous_lit_h`, default 0. Accepted.
- **7e2a** Project frame: solo portfolio. Accepted.
- **8588** S8 UI defaults: 10 mission templates, percent lit threshold, 5 h bridge, hazards toggle, visible error not silent mock. Accepted.
- **8764** Hazard provider returns per-hour fields plus nested provenance. Accepted.
- **9cc5** Local time search slides the window ±h with a leaderboard. Accepted.
- **9e53** Phase-0 contracts and provider seams. Accepted.
- **9f04** Portfolio scope: the 60ab loop plus layer-B surface hazards. Accepted. Supersedes 5cf6. Its `success_xyz` value was superseded by 41fa.

## 2. The problem as framed

- **User.** A mission planner sets the depth bar (`domain_persona: mission_planner`, 3c91:45). The person who must be impressed first is a "technical reader of the demo (hiring manager, peer engineer)" (3c91:20). Educator friendliness was dropped as the default (3c91 superseding ea51).
- **Question.** The starting point is the Space Apps brief's "rapid comparison of landing sites and dates via Sun/Earth vs local horizon (power and DTE)" (60ab:20). The product goes further: "decision support under explicit feasibility constraints… not visualization alone" (60ab:24). The planner gives a site, a time and needs such as max night or max hours without Earth. They get a score that "can be zero if minima are not met," and the tool then searches for "the nearest case where the minima are met" (60ab:38). A deep-search mode looks for a global maximum.
- **Why it's hard.**
  - At the south pole the Sun sits around 1°, so "a frame or sign error gives plausible wrong numbers" (4ffe:44).
  - Terrain dominates. Horizons "ignores terrain" (41fa:46), so a DEM horizon mask is needed: about 289k masks at 1 km and about 28.9M at 100 m, at ~150 ms each (5994:20).
  - There is no public forecast of temperature or dust for a given site×time (41a2:20, 050d:20).

## 3. Most defensible technical decisions

1. **Local SPICE kernels with Horizons as test oracle (4ffe).** Rejected: Horizons per request, throttled by fair use (4ffe:28). Reasons given: cost per calculation and "I genuinely want to understand how the calculations are done" (4ffe:39).
2. **Fail-closed, multi-layer score (7520, 5cfa, 7af3).** Layer 0 is hard minima (night, no-Earth, lit, temperature, dust) that force zero. Layer 1 is a survival probability R = ∏Φ(slack/σ) with σ = 5 h taken from the measured mask error budget (7520:58). Rejected: min-slack (no bonus credit) and min Φ (7520:28-29). Independence is a stated v1 assumption (7520:54).
3. **Capped bonus (6ce5).** The bonus "cannot fully disguise bad risk" (6ce5:39). The falsification test is explicit: wrong "if feasible sites with R≈0.35 routinely score above sites with R≈0.7" (6ce5:59).
4. **The "inside the impossible" score (5577).** Search needs a direction even when every candidate scores zero. The same R×bonus is computed with negative slacks, and the official score stays zero (5577:35).
5. **Measured climatology over a physics model (41a2).** The physics option (incidence, albedo, thermal inertia) was rejected as "a model on top of measurements that already include slope, albedo and rocks" (41a2:32). Each value is labelled "Not the temperature of the future hour" (41a2:53).
6. **Honest dust proxy (050d).** The weighted rock/slope/roughness index was rejected as "not physical dust" (050d:30). A full plume-erosion model was rejected as mission-specific (050d:32). LDEX is out because it measures "Exospheric ejecta, not plume scour" (050d:61). Required label: "soil_erodibility_resistance_not_lofting_rate" (050d:54).
7. **Numeric success criteria, not screenshots (41fa).** "A 3D view can inspect; it is not a metric" (41fa:24). X = kernel az/el vs Horizons. Y = longest night and longest lit within 5 h on 28 points vs the 5 m reference. Z = the score is zero/non-zero on hand scenarios.
8. **Contracts plus a provider seam (9e53, 8764).** Fixed shapes and body-agnostic provider seams. "Changing a field later is a new decision, not a silent edit" (9e53:24).

## 4. Pivots and reversals

- **Hackathon to solo portfolio (11 Nov to 14 Nov 2026).** The owner went solo and is "not optimizing for winning" (7e2a:20). The 48 h must/stretch taxonomy became "obsolete" (9f04:20). Former stretch items (local and deep search) became core because they were no longer "optional Sunday luck" (9f04:38).
- **Audience** shifted from friendly educator UI (ea51) to a technical, explainable tool (3c91). Reason: portfolio readers "judge clarity of model, honesty of claims" (3c91:38).
- **Score evolution.** Interim min(slack) code (de42) was replaced by the Φ-product plus bonus (7520). The bonus cap went from 10% to 30% within the same day because the owner wanted the bonus to "matter more" (6ce5:20), with tuning gated before S6.
- **Success criteria** went from "deferred" (5cf6, 9f04) to concrete X/Y/Z (41fa). PGDA 69 long-term illumination was explicitly kept out and parked until S12.
- **Golden-file regression test** was declined (1a46).

## 5. Surprising or novel points

- **Dual readout of a zero score** that still ranks infeasible options (5577).
- **σ comes from the validation tolerance.** The 5 h mask error budget (Y) also serves as the uncertainty in the probability score (7520:58). Validation and scoring share one error model.
- **Metzger slope substitution was an open research item.** It was marked "deferred — investigate substitution" (050d:57). Per the latest commit message (d158e3e) it has since been implemented, so check that before stating it as current status in the talk.
- **Subjectivity is admitted on the record.** The time-slide criteria are "arbitrary in the sense of subjective preference" (9cc5:38). The owner "could not name falsification cases" for layer-1 (7520:38) and could not think of a way to falsify 41fa (41fa:71).
- **Cost math.** 22 masks/s on the PC means about 15 days for the 100 m cap, hence a ~20 EUR/month server (5994:24).
- **Unexplored terrain.** ML/DL/RL for deep search is intent only (72bc:57). Multi-body support is architectural only. Trajectory optimization is out (9f04:47).
- **Status nuance.** 9f04 frontmatter still says `accepted`, but 41fa:12 lists it as superseded. That covers only `success_xyz`; the scope is restated, not replaced.
