---
id: U-20261115-pj-fc26
person: pj
date: 2026-11-15T12:21:55Z
task: T-20261115-pj-7b5c
---
# UI / desktop packaging decide — pj

## Concepts

| Concept | Role | Status | Source | Evidence | Next check |
|---------|------|--------|--------|----------|------------|
| client compute vs server compute | prerequisite | demonstrated | D-cc6f | Chose desktop-primary; secondary UI only if compute stays local; falsified on lack/unwillingness of local hardware (unlikely / little to lament) | — |
| product desktop shell vs portfolio static web | core | demonstrated | D-cc6f; D-c973 | Desktop is the product; static web at most demo/pitch/docs; priority = desktop works; falsified on web≠desktop drift | — |
| design-system authority vs ad-hoc styling | core | demonstrated | D-01b0 | Blueprint strict for now; may change later; falsified on not liking the look (not a big deal) | — |
| silent AI-slop drift from half-following a kit | hazard | introduced | D-01b0 | Chose strict authority to avoid half-kit drift | — |
| embedding a data-dense toolkit inside a desktop shell | hazard | introduced | D-bdaf; D-50a5 | Tauri + React Blueprint in webview; falsified on look/work poorly (weak) | — |

## Notes

- Warm-up skipped: open debts (climatology, hazard proxy, nodata fill, QuickMap roles) do not touch this decide's concepts.
- Decide-only pass; no build. Queue 1–6 closed 2026-11-15.
- Slight process skip: own item 3 brief shown compactly when pj asked to jump to 5–6 after falsification.
