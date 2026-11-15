---
id: D-20261115-pj-6663
title: "S15 disclosure: no NASA affiliation; hackathon is heritage inspiration only"
date: 2026-11-15T12:15:24Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: claims & interpretation
task: T-20261115-pj-98c4
concepts: [claims honesty, portfolio pack vs contest]
supersedes: []
relates: [D-20261114-pj-7e2a, D-20261115-pj-9ed6, D-20261115-pj-cacb]
ai: options+critique
---
# S15 disclosure: no NASA affiliation; hackathon is heritage inspiration only

## Context

S15 SI / branding. UI footer already carries a NASA non-affiliation line (`D-9ed6`). Challenge text is heritage (`D-7e2a`).

## Framing

Be explicit in pack and README without implying endorsement or contest entry.

## Options considered

1. **NASA branding / logos in the pack.**
2. **Clear non-affiliation; hackathon as inspiration only** (chosen).
3. **No disclosure at all.**

## Decision

**Declare clearly:** no affiliation with or endorsement by NASA; the Space Apps / CLPS browser challenge is **inspiration / heritage** only, nothing more required for branding. No NASA logos or endorsement language in the pack.

## Rationale

I would declare very clearly that there is no affiliation, that the hackathon is simply inspiration, and little more.

## Checks raised

None beyond consistency with footer/`D-7e2a`.

## Values

| Name | Value | Notes |
|------|-------|-------|
| s15_nasa_affiliation | none | Required disclosure |
| s15_challenge_role | heritage_inspiration_only | Restate `D-7e2a` |
| s15_nasa_logos | out | |
| s15_disclosure_surfaces | readme_and_video_and_pitch_and_footer | Same meaning everywhere |

## Expected behavior and validation

Wrong if video/pitch/README imply NASA partnership or official contest submission.

## Consequences

- Remotion end-card / pitch first or last slide / README include the disclosure.
- Footer pattern already satisfies UI side.
