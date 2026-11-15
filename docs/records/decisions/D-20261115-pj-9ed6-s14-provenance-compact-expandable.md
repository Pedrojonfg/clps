---
id: D-20261115-pj-9ed6
title: "S14 provenance: full honesty in payload; compact one-line + expandable UI"
date: 2026-11-15T12:12:17Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: claims & interpretation
task: T-20261115-pj-98c4
concepts: [provenance, claims honesty]
supersedes: []
relates: [D-20261115-pj-671e, D-20261114-pj-8764, D-20261115-pj-de70, D-20261115-pj-06cb]
ai: recommended
---
# S14 provenance: full honesty in payload; compact one-line + expandable UI

## Context

S14 needs a provenance inventory (payload vs UI vs footer). pj set the rule: maximum honesty so anyone can see where numbers come from, without letting citation walls hurt UX — prefer minimal footprint or compressed/expandable disclosure. S10 already uses persistent one-liner + expandable details (`D-671e`). pj asked the AI to lock the technical layout under that rule.

## Framing

Complete traceability in data; progressive disclosure in the interface.

## Options considered

1. **Dump full provenance always visible on screen.**
2. **Docs/README only** (no on-UI provenance).
3. **Full nested provenance in API/payload; UI = one status line + expandable details; footer = short global line + NASA disclaimer** (chosen).

## Decision

**Compact UI, complete payload.**

- **Payload / API (required):** nested provenance for sky (kernels/ephemeris), mask (schedule version + computed vs mock), score (formula, decision IDs, sigmas/β), temperature (product, season, bin, fill), dust (non-lofting label, Metzger β=cos(θ), LDSM, Apollo constants), search (mode + provisional flag when `D-0ee7` applies). Machine-readable; tests may assert keys.
- **UI (required, minimal chrome):** one persistent **status line** (e.g. Live vs Mock; mask computed vs mocked; score formula short tag). Full citations live under a single **“Details / Provenance”** control (expandable), same pattern as S10. No wall of source sentences in the first viewport.
- **Footer (required, short):** NASA non-affiliation disclaimer + at most one compressed source chip when live (e.g. “SpiceyPy · DE440 · PGDA LOLA”); not a second essay.
- **README:** narrative honesty and how-to; not a substitute for missing UI disclosure on hybrid/mock views.

## Rationale

Accepted technical layout under pj’s rule: maximum honesty and sincerity so anyone can see where everything came from; not for profit — but disclaimers must not worsen UX. Cite everything necessary in the smallest space, compressed/expandable. Citing is required; it must not degrade the experience.

## Checks raised

- Honesty vs clutter → resolved by payload-complete + UI progressive disclosure.
- S10 pattern already accepted → reused for S8/main planner surfaces.

## Values

| Name | Value | Notes |
|------|-------|-------|
| provenance_payload | full_nested_required | Sky, mask, score, temp, dust, search |
| provenance_ui_pattern | one_status_line_plus_single_expandable | Matches `D-671e` spirit |
| provenance_ui_first_viewport | no_citation_wall | Expandable holds the list |
| provenance_footer | nasa_disclaimer_plus_optional_short_chip | Not a full inventory |
| provenance_dust_ui_minimum | non_lofting_label_in_expandable_or_status | `D-06cb` / `D-050d` |
| provenance_mask_ui_minimum | computed_vs_mock_on_status_line | `D-a988` |

## Expected behavior and validation

Wrong if a user cannot discover origins (expandable/payload empty) or if the first screen is dominated by citation paragraphs. UX check: main chart/score usable without opening Details.

## Consequences

- Implement/align `web/index.html` provenance + footer with this pattern; keep S10 as-is where already compliant.
- S15 pack may screenshot the compact line; full lists belong in docs/validation or expandable.
