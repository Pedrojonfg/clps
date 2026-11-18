#!/usr/bin/env bash
# Resume-safe NAIF generic kernels for Spike K (DE440 lunar PA).
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/data/kernels"
mkdir -p "$DEST"
UA="moonpark/0.1 (+https://github.com/Pedrojonfg/moonpark)"
BASE="https://naif.jpl.nasa.gov/pub/naif/generic_kernels"
fetch() { echo "==> $2"; curl -L --fail --retry 5 --retry-all-errors -A "$UA" -C - -o "$DEST/$2" "$1"; }
fetch "$BASE/lsk/naif0012.tls" naif0012.tls
fetch "$BASE/pck/pck00011.tpc" pck00011.tpc
fetch "$BASE/pck/moon_pa_de440_200625.bpc" moon_pa_de440_200625.bpc
fetch "$BASE/fk/satellites/moon_de440_250416.tf" moon_de440_250416.tf
fetch "$BASE/fk/satellites/moon_assoc_me.tf" moon_assoc_me.tf
fetch "$BASE/spk/planets/de440s.bsp" de440s.bsp
echo done
