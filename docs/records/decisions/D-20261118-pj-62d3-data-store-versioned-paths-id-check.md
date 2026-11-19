---
id: D-20261118-pj-62d3
title: "Data store: version in the path, one live version, client checks the version id"
date: 2026-11-18T17:48:19Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: data & sources
task: T-20261118-pj-a670
concepts: [cache identity]
supersedes: []
relates: [D-20261118-pj-b3dc, D-20261118-pj-633d, D-20261115-pj-a988]
ai: options+critique
---
# Data store: version in the path, one live version, client checks the version id

## Context

External audit items 19 and 20. Read from `scripts/publish_masks.py` and `moonpark/horizon/remote.py`: files are uploaded with `Cache-Control: public, max-age=31536000, immutable` under a fixed URL; the manifest lists size and sha256 per file; the client reuses a cached file if its size matches, without checking content. Replacing a file under the same URL can leave stale copies in browser and CDN caches and local caches, and can mix versions during an update. The mask manifest has `schedule_version`; the data manifest only has `schema`. Cloudflare R2 storage is $0.015/GB-month with free egress and 10 GB-month free (https://developers.cloudflare.com/r2/platform/pricing/); the store is about 3 GB.

## Framing

Keep the store cheap and simple. Masks will change only a few times in the coming years, since the plan is to precompute them at high precision and not touch them again.

## Options considered

1. **A, replace under the same URL (current)**: assumes content does not change; consequence: stale caches, mixed versions.
2. **B, version in the path, one live version; delete the previous after migration**: consequence: no cache problems, previous version gone.
3. **C, version in the path, keep previous versions**: consequence: earlier analyses reproducible, small cost.

## Decision

**B.** Each published version goes under its own path; only the latest is kept. The client detects an outdated local copy by comparing a **version identifier** from the manifest with the one stored with the cached files; on mismatch it downloads the new version. Past analyses may be recomputed only with the latest data, with a warning that precision has improved and the result may differ. Each saved analysis records the data version it was computed with.

## Rationale

(Translated from pj's Spanish.) How could the problems be solved without it being very expensive? Since the content of the masks will change only a couple of times in the coming years, I think it is enough to store the latest version well, and if someone wants to recompute past analyses, warn them that there is now more precision so the result may vary, and that's it. The problem comes from replacing, not from adding. Yes: the version goes in the path; yes, we save the version in the analysis. For detecting an outdated local copy: the identifier, because it is the simplest way that has maximum effectiveness.

## Checks raised

- "Latest only" does not remove cache problems if the new version reuses the old URL → pj: yes, version in the path.
- How the client notices its copy is old (size, identifier, sha256) → pj: identifier.
- Recompute warning needs each analysis to remember its data version → pj: yes, save it.

## Values

| Name | Value | Notes |
|------|-------|-------|
| store_versions_kept | one (latest) | previous version deleted after migration |
| version_in_path | yes | |
| outdated_copy_check | manifest version identifier vs stored identifier | |
| manifest_version_field | add a version field to the data manifest (the mask manifest already has `schedule_version`) | pj: add it |
| download_checksum | verify sha256 right after each download, to catch corruption | pj: it makes sense; current behavior kept |
| analysis_records_data_version | yes | links to audit item 33 |
| recompute_warning_text | a warning text stating that the data is newer and the result may differ | pj: "yes, text"; wording delegated to the AI |
| old_app_vs_new_data | only the latest app version may be used in the near future; the user is forced to update | pj: first versions will likely have bugs |
| force_update_mechanism | block the app and send the user to download the new version, as is conventional | pj: "I do not know which; as convention"; details delegated to the AI |
| analyses_survive_update | required — updating the app must not lose the user's past analyses | pj; how they are stored/migrated is open (audit item 33) |

## Additional reasoning (pj, translated)

It makes sense to check sha256 right after downloading to avoid corruption. We add a data manifest. Since the first versions will most likely have bugs to fix, at least in the near future only the latest app version should be usable (we force an update somehow), making sure the user does not lose past analyses when updating.

## Later answers (pj, translated)

The mechanism to force the update: I do not know exactly which; block the app and force going to the web to update the version, or whatever; as is the convention.

## Expected behavior and validation

(pj, translated.) It would be a mistake if there were so many changes that the user could never reproduce past analyses. pj notes this should not be a big problem because the plan is to precompute all the masks at high precision and not change them again.

## Consequences

- The publish script writes under a versioned path and a manifest carrying the version identifier; the client stores the identifier with the cache and re-downloads on mismatch.
- Saved analyses store the data version.
- A forced-update mechanism and a data-preserving update path are now requirements; their design is not decided here (release process, audit items 33, 35, 42).
