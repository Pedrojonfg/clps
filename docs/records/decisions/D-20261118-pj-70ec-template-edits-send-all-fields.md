---
id: D-20261118-pj-70ec
title: "Template edits: every field is sent, and an edited template becomes Custom"
date: 2026-11-18T17:33:56Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261118-pj-a670
concepts: [effective requirements]
supersedes: []
relates: [D-20261118-pj-75f1, D-20261114-pj-8588, D-20261117-pj-0c5e]
ai: options+critique
---
# Template edits: every field is sent, and an edited template becomes Custom

## Context

External audit item 8. Read from `desktop/src/api.ts` and `moonpark/api/app.py`: with a mission template selected, the form copies the template's values into the fields, but the request carries only `template_id` for seven of them (max night, max no-Earth, continuous lit, both-at-once, Sun %, Earth %, gap hours), and the server uses the template's values. Edits to those fields are shown on screen but never evaluated, with no message. Total lit time, battery and hazard limits are always sent.

## Framing

What is shown, what is sent and what is evaluated must be the same list (`D-20261118-pj-75f1`). Honesty over convenience.

## Options considered

1. **A, template wins silently (current)**: assumes the user does not edit; consequence: shown edits are ignored.
2. **B, lock template-controlled fields**: assumes templates are fixed; consequence: no tuning without leaving the template.
3. **C, send every field; an edited template stops being named and shows as Custom**: assumes the form is the source of truth and the template is only a starting point; consequence: the template name is accurate only while the values are the template's.

## Decision

**C.** The UI always sends every field. Once the user edits a field, the UI no longer shows the template's name and shows the existing "Custom" label instead.

## Rationale

(Translated from pj's Spanish.) Send everything, out of honesty. In the UI, simply stop showing the template name and show "custom" (or whatever already exists for custom values).

## Checks raised

- None raised; pj asked for the record and the next decision without the options table.

## Values

| Name | Value | Notes |
|------|-------|-------|
| template_fields_sent | all fields, always | |
| edited_template_label | "Custom" (existing label) | |
| template_id_after_edit | the template name or id appears (and is sent) only when all values equal the template's; otherwise Custom | pj |
| edit_back_to_template_values | yes: when all values equal the template's again, the name returns | follows from the same rule, pj |
| server_overrides_from_template | none for fields the request provides | derived from "send everything"; `D-20261117-pj-0c5e` precedence (explicit > template > default) stays for clients that omit a field |

## Later answers (pj, translated)

Very simple: you only show the template name or id when all the values are equal. If any value differs, it is not the template. With that criterion I think the questions are answered.

## Expected behavior and validation

(pj, translated.) There is no falsifiability criterion. Implied check, not stated by pj: after editing any field with a template selected, the evaluated values equal the displayed ones, and the label reads Custom.

## Consequences

- `buildSiteQuery` sends the seven fields regardless of `template_id`; the server stops replacing Sun/Earth thresholds and gap hours with the template's when the request provides them.
- Regression test: select a template, edit one field, assert the request and the evaluation use the edited value.
- Same rule applies to the regional search request (`D-20261118-pj-75f1`).
