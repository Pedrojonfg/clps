#!/usr/bin/env bash
# Resume the 1 km cap recompute into data/masks/cap_1km_new (tile-level progress.json).
# Safe to re-run after reboot, sleep, or crash: finished tiles are skipped.
set -euo pipefail
REPO="${HOME}/clps"
OUT="${REPO}/data/masks/cap_1km_new"
PROG="${OUT}/progress.json"
LOG="${REPO}/logs/precompute-cap_1km_new.log"
PY="${REPO}/.venv/bin/python"
WORKERS="${PRECOMPUTE_WORKERS:-4}"

mkdir -p "${REPO}/logs" "${OUT}"
cd "$REPO"

NT=0
if [[ -f "$PROG" ]]; then
  NT=$(python3 -c "import json; print(len(json.load(open('$PROG'))['tiles']))" 2>/dev/null || echo 0)
fi
if [[ "$NT" -ge 44 ]]; then
  echo "[$(date -Iseconds)] cap_1km_new already complete ($NT/44); nothing to do" | tee -a "$LOG"
  exit 0
fi

# Avoid a second pool if one is already computing
if pgrep -f "scripts/precompute.py --out data/masks/cap_1km_new" >/dev/null 2>&1; then
  echo "[$(date -Iseconds)] precompute already running ($NT/44); exit" | tee -a "$LOG"
  exit 0
fi

echo "[$(date -Iseconds)] resuming precompute ($NT/44) workers=$WORKERS" | tee -a "$LOG"
exec "$PY" -u scripts/precompute.py --out data/masks/cap_1km_new --workers "$WORKERS" >>"$LOG" 2>&1
