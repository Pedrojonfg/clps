# Release checklist (prepared overnight 2026-11-17; updated 2026-11-21)

## Verified
- CI workflow `desktop-release.yml` built the installers on Linux, Windows and macOS (run 44186563271, all green), each with a smoke test of the bundled engine (`/health` and `/site?mock=1&local_search=1` with a non-empty leaderboard).
- Linux: `deploy/build-desktop.sh` produced deb, rpm and AppImage locally. The release binary launched under xvfb, started the engine on a free loopback port, and `/health` and the mock local search answered.
- `scripts/publish_masks.py --dry-run` builds both manifests (cap_1km: 90 files, 879 MB; data: now 416 files / 2737 MB including relief cuts).
- **2026-11-21 WSL:** AppImage rebuild finished (`moonpark_0.1.0_amd64.AppImage`, also copied to `~/apps/moonpark.AppImage`). Bundled `moonpark-api --port …` returns `/health` ok and mock `/site?mock=1&local_search=1` with a 47-entry leaderboard.
- **2026-11-21:** fill-stats for D-d90c committed on `feat/recompute-cap-masks` (`scripts/precompute.py`, `cap_index.py`, `tests/test_cap_fill_stats.py`). Full 1 km recompute into `data/masks/cap_1km_new/` is in progress (swap to `cap_1km` when 44/44).
- **2026-11-21:** real `/site` against local `data/` (kernels + current `cap_1km`) returns `data_source=real` and a feasible score (hazards off).
- **2026-11-21:** `scripts/publish_masks.py` uploaded both groups to R2 (`cap_1km/d1dd266012b1`, `data/cc02b519005a`). `masks.pedrojon.com/.../latest.json` serves the pointers; sample objects return HTTP 200.
- **2026-11-21:** packaged `moonpark-api` with an **empty cache** downloaded from the store and returned `data_source=real` (~495 MB pulled for one short window with hazards off).

## Not verified
- The UI of the packaged app was not looked at (no screenshot under xvfb); only the engine side was exercised.
- Windows and macOS installers were built but never launched on real machines.
- macOS and Windows builds are unsigned: expect Gatekeeper / SmartScreen warnings.
- Cap recompute with fill stats (D-d90c) still running into `data/masks/cap_1km_new/` (resume with 4 workers after an overnight death at 5/44). Publish again with `--only cap_1km` after swap.

## Remaining
1. Finish fill-stats recompute → swap → `publish_masks.py --only cap_1km`.
2. Optional later: code signing / notarization; run Win/mac installers on real machines.

## Released
- **2026-11-21:** tag `v0.1.0` — CI green ([run](https://github.com/Pedrojonfg/moonpark/actions/runs/44892380278)); GitHub Release published with Linux/Windows/macOS installers.
