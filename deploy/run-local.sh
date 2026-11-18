#!/usr/bin/env bash
# Start the API (:8000) and the desktop UI dev server (:1420, proxies to the API). Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "$0")/.."
source "$HOME/.nvm/nvm.sh" 2>/dev/null || true
uvicorn moonpark.api.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir moonpark &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd desktop
exec npm run dev
