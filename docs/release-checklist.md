# Release checklist (prepared overnight 2026-11-17; updated 2026-11-21)

## Verified
- CI workflow `desktop-release.yml` built the installers on Linux, Windows and macOS (run 44186563271, all green), each with a smoke test of the bundled engine (`/health` and `/site?mock=1&local_search=1` with a non-empty leaderboard).
- Linux: `deploy/build-desktop.sh` produced deb, rpm and AppImage locally. The release binary launched under xvfb, started the engine on a free loopback port, and `/health` and the mock local search answered.
- `scripts/publish_masks.py --dry-run` builds both manifests (cap_1km: 90 files, 879 MB; data: now 416 files / 2737 MB including relief cuts).
- **2026-11-21 WSL:** AppImage rebuild finished (`moonpark_0.1.0_amd64.AppImage`, also copied to `~/apps/moonpark.AppImage`). Bundled `moonpark-api --port …` returns `/health` ok and mock `/site?mock=1&local_search=1` with a 47-entry leaderboard.
- **2026-11-21:** fill-stats for D-d90c committed on `feat/recompute-cap-masks` (`scripts/precompute.py`, `cap_index.py`, `tests/test_cap_fill_stats.py`). Full 1 km recompute into `data/masks/cap_1km_new/` is in progress (swap to `cap_1km` when 44/44).

## Not verified
- The UI of the packaged app was not looked at (no screenshot under xvfb); only the engine side was exercised.
- Windows and macOS installers were built but never launched.
- Real-data evaluation from the packaged engine: `masks.pedrojon.com/cap_1km/latest.json` is still empty/404 — R2 publish not done (needs `R2_*` env).
- macOS and Windows builds are unsigned: expect Gatekeeper / SmartScreen warnings.
- New cap tiles with fill stats not yet swapped/published (wait for recompute).

## Decisions for you
1. Upload the data: set `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` (and `R2_BUCKET` if not `lunar-masks`), then `python scripts/publish_masks.py`. Check `masks.pedrojon.com` serves it. Then run the packaged app with an empty cache to test the first download (up to ~0.7 GB with hazards; progress UI exists in the planner).
2. Cut the release: push a tag `vX.Y.Z` (the workflow then creates a DRAFT release with the three installers). Decide the version and whether to wait for more PRs first.
3. Code signing / notarization for macOS and Windows, if you want to avoid the warnings.
