---
id: D-20261118-pj-fc4d
title: "v1 platforms: announce Linux, Windows and macOS only after testing each; unsigned binaries explained like other open-source projects"
date: 2026-11-18T21:43:17Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: scope & success criteria
task: T-20261118-pj-a670
concepts: [release evidence]
supersedes: []
relates: [D-20261115-pj-de70, D-20261118-pj-d99f, D-20261118-pj-62d3]
ai: options+critique
---
# v1 platforms: announce Linux, Windows and macOS only after testing each; unsigned binaries explained like other open-source projects

## Context

External audit items 35 and 42. Read from `.github/workflows/desktop-release.yml`: CI builds installers for Linux (`.deb`, `.AppImage`), Windows (`.msi`) and macOS (`.dmg`) and creates a draft release; nothing is published. The README lists "launching the packaged app on each OS" as pending, and the audit notes the engine smoke test uses fake data and does not replace installing and using the app. There is no code signing or notarization. Practitioner guides (not official docs) say Windows SmartScreen warns on unsigned installers ("More info", "Run anyway") and macOS Gatekeeper blocks unsigned apps (right-click Open or `xattr -cr`). Architectures: the CI matrix builds one installer per OS (`macos-latest` believed to be Apple Silicon, not verified).

## Framing

Do not announce what has not been tested, as with the removed 28-point claim (`D-20261115-pj-de70`).

## Options considered

1. **A, announce all three after testing each**: consequence: full promise, backed by tests.
2. **B, announce one first**: consequence: smaller reach, lower risk.
3. **C, announce all three, marking the untested one**: consequence: transparent, but not what pj wants.

## Decision

**A.** Linux, Windows and macOS are announced for v1, but only after pj has tested the installer on each. A system that cannot be tested enough is withdrawn from the announcement. For unsigned binaries, the release says what other open-source projects with unsigned binaries say.

## Rationale

(Translated from pj's Spanish.) For all three, I will make sure to test it on all of them first. As for the unsigned binaries, we say the same as all open-source projects whose binaries are not signed, which I understand are the majority. Let us leave the architectures as deferred; we will come back when the product is ready and we have to test the installer.

## Checks raised

- Which architectures to announce → pj: deferred until the installer is tested.
- Checklist for "tested enough" (clean user without Python, Node or the repository; first-run download; a real analysis; the views; save and reopen; restart; uninstall), per the audit → not answered; kept as a proposal.
- Exact unsigned-binary wording with per-OS steps plus the sha256 of each installer, per the audit → not answered; kept as a proposal.

## Values

| Name | Value | Notes |
|------|-------|-------|
| announced_platforms | Linux, Windows and macOS, each only after pj tests it | |
| retreat_rule | an OS not tested enough is withdrawn from the announcement | |
| unsigned_binaries_message | the usual open-source wording for unsigned binaries | exact text deferred |
| architectures_announced | deferred — decide when the product is ready and the installer is tested | |
| test_checklist_per_os | the audit's list: clean user with no Python, Node or repository; first-run download; a real analysis; the views; save and reopen; restart; uninstall | accepted by pj |
| release_notes_and_hashes | deferred to just before publishing | pj |
| signing_plan | deferred to just before publishing | pj |

## Later answers (pj, translated)

Announced architectures: deferred, as I said. The per-system test list: I accept the audit's proposal. The next four (notes and hashes, signing, README rewrite, offline test) we will see before publishing; I defer them to that moment, since many things remain to be fixed.

## Expected behavior and validation

(pj, translated.) It would be a mistake if the app could not be tested enough on all the systems; in that case pj retreats without any problem.

## Consequences

- No platform is claimed in the README until it is tested; today's README text must be aligned at release.
- A tested-installer record per OS (what was run, which version, result) is needed before announcing.
