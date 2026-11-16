---
id: D-20261115-pj-c30e
title: "No extra host process beyond GitHub Pages for this tranche"
date: 2026-11-15T11:36:17Z
author: pj
decided-by: pj
status: accepted
mode: advise
domain: dependencies & ops
task: T-20261115-pj-5200
concepts: [public HTTPS demo honesty, secrets/tokens in git]
supersedes: []
relates: [D-20261115-pj-2533, D-20261115-pj-4494]
ai: none
---
# No extra host process beyond GitHub Pages for this tranche

## Context

`D-2533` chose GitHub Pages for the static demo. Item 11b asked whether TLS/process beyond Pages is needed today.

## Framing

Minimize ops for the demo day.

## Options considered

1. Pages only, no extra process (chosen).
2. Pages + CDN/proxy in front.
3. Own VPS (nginx/caddy) now.

## Decision

**For today / this tranche: no own server and no extra process beyond GitHub Pages; revisit later.**

## Rationale

pj: for now no own server or further process is needed — not for today; future later.

## Checks raised

None raised.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s11_extra_host_process | none_this_tranche | |
| s11_tls_provider | github_pages | |
| s11_own_vps_this_tranche | false | |

## Expected behavior and validation

Demo HTTPS comes only from Pages. Wrong if the tranche quietly depends on a second running service.

## Consequences

- `deploy/` documents Pages only.
- VPS / Caddy / systemd stay out until a later decision.
