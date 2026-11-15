---
id: D-20261115-pj-2533
title: "Static demo and docs deploy on GitHub Pages for now"
date: 2026-11-15T11:25:40Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: dependencies & ops
task: T-20261115-pj-5200
concepts: [public HTTPS demo honesty, secrets/tokens in git]
supersedes: []
relates: [D-20261115-pj-4494, D-20261115-pj-8c03, D-20261115-pj-7d58, T-20261115-pj-2b7a]
ai: recommended
---
# Static demo and docs deploy on GitHub Pages for now

## Context

`D-4494` requires a static deploy plus docs for this tranche (no mask API). `D-8c03` keeps product compute on the client. Cesium Moon (`D-7d58`) needs HTTPS for a public demo; the ion token will be client-side and should be referrer-restricted.

## Framing

Ship a public portfolio URL with minimum ops.

## Options considered

1. **A — GitHub Pages** (recommended): free HTTPS; fits static `web/` + docs.
2. **B — Cloudflare Pages / Netlify**: same idea; another account.
3. **C — Hetzner static nginx**: useful only if a VPS is already paid.
4. **D — Local + video/README only**: no public URL.

## Decision

**A — GitHub Pages for now**, with an explicit revisit later.

## Rationale

Accepted the recommendation: GitHub Pages is fine for now, again for simplicity, but note it to review in the future.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| deploy_target | github_pages | Fills deferred from `D-4494` |
| deploy_target_revisit | yes — reconsider host after the demo tranche | pj request |
| public_https_role | static_demo_and_docs | Same as `D-4494`; not evaluator hosting |
| client_packaging | browser_static_demo | Enough for this portfolio tranche; fuller packaging still open later |
| cesium_ion_token_in_pages | client_bundle_with_ion_referrer_restriction | Not a server secret; still not committed as a writable secret file if avoidable — use Pages env / build inject when practical |

## Expected behavior and validation

Demo and docs reachable over HTTPS on GitHub Pages. Wrong if Pages cannot host the Cesium demo or if revisit is forgotten when ops needs change (custom domain, mask API, paid ion).

## Consequences

- `deploy/` documents how to enable Pages and what gets published.
- Revisit host when leaving “demo tranche” simplicity.
