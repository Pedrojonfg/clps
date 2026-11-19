---
id: D-20261118-pj-633d
title: "Local solar time from SPICE et2lst, adapted to the Diviner convention"
date: 2026-11-18T17:24:30Z
author: pj
decided-by: pj
status: accepted
mode: own
domain: method & validation
task: T-20261118-pj-a670
concepts: [local solar time, climatology]
supersedes: []
relates: [D-20261114-pj-41a2, D-20261118-pj-b3dc]
ai: options+critique
---
# Local solar time from SPICE et2lst, adapted to the Diviner convention

## Context

External audit item 1. `moonpark/hazards/lst.py` computes local solar time as UTC hour of day + longitude/15, dropping minutes, so it completes a full 24 h cycle every Earth day. A lunar solar day lasts about 29.5 Earth days, so the true local solar time advances about 0.8 h per Earth day. A check with SPICE for a test site (lon 222.51) over 2027-01-01..03 gave true values 9.29, 9.50, 9.70, 10.10, 10.92 h at 0, 6, 12, 24, 48 h, against the code's 14.83, 20.83, 2.83, 14.83, 14.83. The temperature climatology (`D-20261114-pj-41a2`) is indexed by local solar time in 96 bins of 0.25 h per season, so every analysis picks a wrong bin, and any 24 h window sees the whole thermal cycle.

## Framing

Use a published, standard definition instead of our own formula, and match the convention of the dataset it indexes. Cost is not the constraint: 4,464 Sun positions (31 days at 10 min) take 0.09 s with SPICE.

## Options considered

1. **A, current approximation (UTC hour + lon/15)**: assumes the Moon rotates once per Earth day; consequence: wrong bins.
2. **B, own formula from the SPICE sub-solar longitude**: 12 + (lon - sub-solar lon)/15; consequence: correct, but a convention we maintain.
3. **C, SPICE `et2lst`**: assumes NAIF's definition is the reference; consequence: same numbers as B (9.293, 10.104, 21.471 h in three checked cases), no own formula.

## Decision

**C.** Compute local solar time with SPICE `et2lst` (planetocentric longitude, body Moon) instead of our own formula. Adapt to the Diviner PCP convention, which must be checked in its documentation and data; no extra light-time correction beyond what `et2lst` does.

## Rationale

(Translated from pj's Spanish.) Calculate it with SPICE from the real position of the Sun; in the end it is not very expensive because we were going to compute the Sun position anyway. If NAIF has a function that gives the correct result automatically, there is no point in reinventing the wheel. I would investigate directly what the Diviner convention is (it surely says so somewhere) and adapt to it. Light-time correction does not seem very necessary for now; I would trust NAIF without trying to change much, since that would be overkill.

## Checks raised

- Convention mismatch between SPICE and Diviner (what 0 h is, longitude direction) would produce a sign or 12 h error no current test catches → pj: look it up in Diviner documentation and adapt.
- Light-time correction changes sub-solar longitude by fractions of a degree → pj: not needed; trust NAIF. (Checked: our LT+S formula matches `et2lst` to 0.001 h, so `et2lst` already includes it.)
- No test compares local solar time with a reference → open (see Consequences).

## Values

| Name | Value | Notes |
|------|-------|-------|
| lst_method | SPICE `et2lst`, body 301, planetocentric | |
| lst_light_time_correction | none beyond `et2lst` default | |
| lst_bin_width_h | 0.25 | 96 bins/season as in the product (`LTIM=(NUM-1)*0.25`) |
| diviner_lst_noon_convention | noon = 12 h, validated by a test against the data that finds the local time of the temperature maximum | pj. Earlier data check (AI): hottest bin within 11.5-13.25 h at 4 of 8 test points and at 16-19.75 h at the other 4 (terrain suspected, unverified) |
| season_definition | subsolar latitude below equator = summer | matches ODE PCP page |

## Later answers (pj, translated)

A test against the data, finding the moment at which it is hottest, and taking noon as 12 hours. Fine.

## Expected behavior and validation

(pj, translated.) The choice would be wrong if it were very expensive to compute or unrealistic. Not stated by pj: the check for "unrealistic" is a test of local solar time against a reference and against the Diviner convention; the cost check is already done (0.09 s per 31 days at 10 min).

## Consequences

- Replace `local_solar_time_h_from_utc` with an `et2lst`-based function (one SPICE call per instant, reusable by all sites), keeping `lst_bin_index`.
- Add reference tests: several dates and longitudes, including wrap at 24 h, against `et2lst` values.
- Season definition already matches the product; the "summer on any exception" fallback is removed by `D-20261118-pj-b3dc`.
- Local copy of the climatology has missing bins (95/96 summer, 87/96 winter); under `D-20261118-pj-b3dc` hours falling into a missing bin block the hazard analysis. Not decided here: whether the data store must be complete before release (audit items 18-20).
