#!/usr/bin/env bash
# Build the desktop UI against the hosted API (default https://api.pedrojon.com) into desktop/dist.
# Then `cd desktop && npm run tauri build` packages it. Override: VITE_API_BASE=https://other ./deploy/build-desktop.sh
set -euo pipefail
cd "$(dirname "$0")/.."

(cd desktop && VITE_API_BASE="${VITE_API_BASE:-https://api.pedrojon.com}" npm run build)
cp web/map.html web/map.js web/firstperson.html web/firstperson.js desktop/dist/
cp -r web/assets/. desktop/dist/assets/
