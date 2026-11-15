---
id: U-20261115-pj-203a
person: pj
date: 2026-11-15T10:34:40Z
task: T-20261115-pj-33ca
---
# S9 region score map — pj

## Concepts

| Concept | Role | Status | Source | Evidence | Next check |
|---------|------|--------|--------|----------|------------|
| Quickmap / Moon Trek / Horizons roles | warm-up | shaky | U-20261114-pj-3839; project Sources | Warm-up not retrieved: pj asked for the brief answer to save time; AI restated the settled distinction; no unaided evidence | next defend or when S9 claims cite basemap vs score grid |
| absolute score color scale | core | introduced | approach; D-7227 | Chose absolute RYG + clamp; falsification: out-of-range must not break (clamp to green) | — |
| relative stretch of this query's scores | hazard | introduced | approach | Named the failure mode; allowed in-query relative dots only on infeasibles (`D-8acb`) | — |
| cell fill / nearest-sample paint | core | introduced | D-834a | Interpolate overview; solid on lift; falsification: users may call interpolate dishonest — accepted for now | — |
| local-search candidate set | prerequisite | introduced | D-85bf | Paint evaluated local/deep points; induce only if partial | — |
| silent incomplete search | hazard | introduced | D-85bf | Induced layer must stay more transparent / not claimed as scored | — |
| region score heatmap | core | introduced | D-4126 | Chose orbitable 3D Moon canvas over 2D basemap | — |
| infeasible display zero | prerequisite | introduced | D-8acb | Black fill for infeasible; UI score for feasibles | — |

## Notes

- Session pace: pj short on time; UI decide batched.
- D- records written 2026-11-15 after English rationale confirm.
