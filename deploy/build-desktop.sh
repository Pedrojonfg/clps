#!/usr/bin/env bash
# Build the installable desktop app with the Python engine bundled as a sidecar.
# Needs: Python 3.12, npm, Rust and the Tauri system libs. Output: desktop/src-tauri/target/release/bundle/
# PyInstaller does not cross-compile: run this once per OS (Linux, macOS, Windows).
set -euo pipefail
cd "$(dirname "$0")/.."

# A clean venv keeps the bundle to ~0.5 GB; building from a full conda env pulls in 1.6 GB.
VENV=build/engine-venv
[ -d "$VENV" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q numpy scipy rasterio fastapi "uvicorn[standard]" pyarrow spiceypy pyinstaller

ENGINE=desktop/src-tauri/engine
rm -rf "$ENGINE" build/engine
"$VENV/bin/pyinstaller" --noconfirm --onedir --name lunar-eval-api \
  --distpath build/engine --workpath build/engine-work --specpath build/engine-work \
  --paths . --add-data "$PWD/web:web" \
  --collect-submodules uvicorn --collect-submodules lunar_eval --collect-submodules api \
  --collect-all rasterio --collect-all spiceypy --collect-all pyarrow \
  api/sidecar.py
mv build/engine/lunar-eval-api "$ENGINE"
touch "$ENGINE/.gitkeep"

(cd desktop && npm ci && npm run tauri build)
