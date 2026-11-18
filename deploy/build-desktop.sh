#!/usr/bin/env bash
# Build the installable desktop app with the Python engine bundled as a sidecar.
# Needs: Python 3.12, npm, Rust and the Tauri system libs. Output: desktop/src-tauri/target/release/bundle/
# PyInstaller does not cross-compile: run this once per OS (Linux, macOS, Windows).
set -euo pipefail
cd "$(dirname "$0")/.."

# A clean venv keeps the bundle to ~0.5 GB; building from a full conda env pulls in 1.6 GB.
VENV=build/engine-venv
PY=python3; command -v python3 >/dev/null || PY=python
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) BIN=Scripts; SEP=";" ;;   # Windows (Git Bash)
  *) BIN=bin; SEP=":" ;;
esac
[ -d "$VENV" ] || "$PY" -m venv "$VENV"
"$VENV/$BIN/python" -m pip install -q numpy scipy rasterio fastapi "uvicorn[standard]" pyarrow spiceypy pyinstaller

ENGINE=desktop/src-tauri/engine
rm -rf "$ENGINE" build/engine
"$VENV/$BIN/pyinstaller" --noconfirm --onedir --name moonpark-api \
  --distpath build/engine --workpath build/engine-work --specpath build/engine-work \
  --paths . --add-data "$(pwd -W 2>/dev/null || pwd)/web${SEP}web" \
  --collect-submodules uvicorn --collect-submodules moonpark \
  --collect-all rasterio --collect-all spiceypy --collect-all pyarrow \
  moonpark/api/sidecar.py
mv build/engine/moonpark-api "$ENGINE"
touch "$ENGINE/.gitkeep"

(cd desktop && npm ci && npm run tauri build)
