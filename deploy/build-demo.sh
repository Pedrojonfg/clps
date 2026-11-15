#!/usr/bin/env bash
# Build the static browser demo (desktop UI + embedded web pages, mocked data) into desktop/dist.
# Needs: `pip install -e ".[dev]"` and `npm ci` in desktop/.
set -euo pipefail
cd "$(dirname "$0")/.."

python scripts/export_demo_data.py desktop/public/demo
(cd desktop && VITE_STATIC_DEMO=1 npm run build)
cp web/map.html web/map.js web/firstperson.html web/firstperson.js desktop/dist/
cp -r web/assets/. desktop/dist/assets/
