# ADR digest C: D-20261115 records (claims, validation, product, S10, deploy)

Paths: `docs/records/decisions/D-20261115-pj-<id>-*.md`. All 31 are **accepted**. Only one supersedes anything: **8c03 supersedes D-20261114-pj-5994**. None of the 31 has been superseded.

## 1. One line per ADR
- **01b0**: Blueprint is the strict UI authority for now; no half-kit custom styling.
- **1264**: S15 = Remotion video after UI; pj owns the pitch; no contest submission.
- **1a9e**: S12 is done when scripts and tests exist; heavy runs overnight; red results must be fixed before the final product.
- **2533**: Static demo and docs go on GitHub Pages; host to be revisited later.
- **358b**: "No lying." Forbidden and provisional claims are derived from the ADRs.
- **3832**: Masks are mocked in this demo; the product will get masks from a server API later.
- **39f3**: Short-night re-check is a separate report. If error exceeds 5 h, success Y is reopened.
- **3c4a**: Docs make install and try-today clear; pj sets pitch length.
- **4494**: S11 for this tranche means static deploy plus docs. The mask API is out.
- **50a5**: React plus `@blueprintjs` inside the Tauri webview.
- **573b**: The 100 m precompute and the server benchmark come after this tranche.
- **6663**: No NASA affiliation. The hackathon is heritage and inspiration only.
- **671e**: Cesium backdrop is not our model. UI shows a one-line notice plus expandable provenance.
- **7d58**: Backdrop engine is CesiumJS with Cesium Moon (ion).
- **8c03**: Remote serves horizon masks only; evaluator runs on the client.
- **8fd2**: Portfolio done when the UI is finished; then video, docs, disclosure.
- **9ab3**: PGDA 69 protocol: ~18.6 y average illumination at PGDA-78 sites, report only.
- **9ed6**: Full provenance in the payload; compact status line plus expandable panel in the UI.
- **a988**: Overnight masks = computed; rest = mocked; full cap = planned.
- **ac34**: S10 hybrid: third-party backdrop plus our labelled mask and sky.
- **ac74**: S10 fallback is a 2D mask panorama.
- **b6fe**: Blueprint dark theme with kit defaults, including radius.
- **bdaf**: Desktop shell is Tauri.
- **c30e**: No host process beyond GitHub Pages in this tranche.
- **c973**: The static web/Pages demo is not the product. Desktop is the priority.
- **cacb**: README structure: what / how / try-today (with honest limits) / future masks and API.
- **cc6f**: Desktop-first on user hardware; any secondary UI keeps compute local.
- **de70**: Claims are evidence-gated: only what a test or ADR backs.
- **e062**: S10 entry shares site and time with S8.
- **f2d3**: S10 camera: 2 m observer, synced to S8, limited look-around.
- **fe17**: PGDA 69 only in the S12 report and README; not in score, search or X/Y/Z.

## 2. Themes
- **Claims honesty / evidence gating** (de70, 358b, a988, 3832, 671e, 9ed6, cacb, 6663, fe17): a claim is allowed only when it is "evidence_gated_test_or_adr" (de70:50). Unrun tests: "test exists, README updates when run" (de70:51). 358b:47-52 forbids: mocks as computed; Cesium as our model; dust as lofting rate; PGDA 69 validated without numbers; S7 global optimum before megatest; X/Y/Z closed with unrun/red tests.
- **Validation** (9ab3, 39f3, 1a9e, fe17): PGDA 69 = Δ pp per site (ours − map), "No product pass/fail threshold in v1" (9ab3:35). Short-night re-check: Site01 plus PGDA-78 sites with a 40–80 h longest night, 5 h tolerance. It "does not automatically change `success_y`" (39f3:35). Why: the 28-point Y gate only used ≥392 h nights; VIPER-like ~50 h error is "unmeasured" (39f3:20).
- **Product architecture** (8c03, cc6f, c973, bdaf, 50a5, 01b0, b6fe): the server only stores and serves masks; score, search and live sky run on the user's machine (8c03:50-51). Pages is "not_product" (c973:48).
- **First-person view** (ac34, 7d58, 671e, f2d3, e062, ac74): Cesium terrain is context only; ours = mask plus Sun/Earth geometry (671e:48-49); 2 m observer matching masks (f2d3:49); 2D panorama fallback.
- **Deploy** (4494, 2533, c30e, 573b): Pages only; no VPS, mask API or 100 m run this tranche; ion token client-side, referrer-restricted (2533:53).

## 3. Most interesting decisions and why
1. **8c03: compute on the client, masks-only server.** Rejected: app+API+compute on pj's server, "cost and performance capped by what pj pays" (8c03:29). Users have strong hardware and "my part is almost free" (cb6b:39). The falsifier: if client compute were infeasible, "the failure is the product, not this split" (8c03:61).
2. **ac34: hybrid view.** Option C, third-party tiles with our sky on top, was "easy to misread as our terrain model" (ac34:30). D was chosen because "an impressive UI helps the end user understand the complexity … but honesty must be kept" (ac34:39). On-UI labels are mandatory (ac34:54).
3. **7d58: Cesium over the AI's recommendation.** The AI recommended Three.js with baked NASA imagery (7d58:28). pj chose Cesium because the project is portfolio-only and unmonetized, so the ion Community plan fits (7d58:39).
4. **de70 + 358b: honesty as a rule, not a curated list.** pj declined to hand-pick sentences: "total honesty; base on the ADRs and update as tests are proven" (358b:37).
5. **39f3: measure, don't silently rewrite.** Rejected: S2, fail CI; S3, Site01 only; S4, fold the re-check into Y immediately (39f3:29-31). If error exceeds 5 h, Y is reopened through a new decision, "do not silence" (39f3:35).
6. **fe17: PGDA 69 as external evidence, not a feature.** Rejected: putting it into X/Y/Z or into the score (fe17:31-32). Reason: "only a report … I do not think it has any use in the actual product" (fe17:40).
7. **bdaf / 01b0: Tauri and strict Blueprint.** Electron was rejected as "heavy on disk/RAM" and Qt as "far from Blueprint React" (bdaf:28-30). Mixing Blueprint with custom "premium" styling was rejected as the "classic half-kit AI-slop hazard" (01b0:30).

## 4. Pivots
- **Hackathon to solo portfolio.** Space Apps 23:00 submission dropped (1264:20, 34; T-98c4:94). NASA becomes heritage only (6663).
- **Server-hosted app to client compute.** D-5994 had the server running the app. 8c03 supersedes it. CX43 was out of stock (U-2624:23).
- **Browser demo to desktop product.** 8c03/2533 filled `client_packaging` as `browser_static_demo`. Two hours later cc6f:50 demoted that to "tranche demo fill only", and c973 adds "Maybe we have to remove the pages" (c973:38).
- **"Precomputed masks ⇒ search cheap" was only half-true.** Ephemeris costs ~0.4–0.5 s per site (U-8420:26). That led to two search modes plus a 5-minute budget (54f0, 8a25).
- **Process:** S10/S11 "jumped to implementation checkpoint too early; pj reopened Decide" (T-2b7a:80).
- **Tune evidence changed values.** β=0.15 gave inversion rates <2% (≈0.94% feasible), which meant REOPEN, so β=0.25 / cap 0.40 was adopted (T-d567:63; 48ee).
- **Understanding status.** The hazard-proxy warm-up was graded "shaky": pj missed Metzger 2024, the Apollo constants and the non-lofting label (U-96f5:13). Most S10–S15 concepts are only "introduced" (U-2624, U-96f5). "Demonstrated" covers: client vs server compute (U-2624:25), desktop vs static web, and Blueprint authority (U-fc26:13-15).

## 5. What is not done or validated (don't overclaim)
- **PGDA 69 and short-night:** harness only. `docs/validation.md` says "planned" and "No overnight run recorded yet". Do not say "validated against PGDA 69" (fe17:54). Do not say Y covers VIPER-like short nights (39f3:60).
- **S7 deep search:** the megatest harness was "not executed" (T-2cbd:70). The optimized mode is "best seen", not the grid optimum (54f0:64; 0ee7:51).
- **No mask API, no 100 m cap, no server benchmark** (4494:51-53; 573b). The mask publish location is TBD (a988:51).
- **Desktop app:** decided only (T-7b5c); untracked `desktop/` Tauri+Blueprint scaffold; Python bridge deferred (bdaf:51).
- **Remotion video / portfolio done:** both gated on a finished UI (1264:52; 8fd2).
- **Demo, computed vs mocked:**
  - **Computed:** the ~290k-mask 1 km cap on disk, `data/masks/cap_1km`, ~839 MB (demo-data-and-masks.md:16-21). Locally, `/site` uses a real Site01 DEM mask plus SPICE sky when data is present (T-9e03:15).
  - **Mocked:** mask series shown in the Pages demo (demo-data-and-masks.md:9, 28).
  - **Not ours:** Cesium Moon relief, labelled "Backdrop: Cesium Moon — not our model" (671e:51).
  - Say which you show: local real-data run or Pages mock.
