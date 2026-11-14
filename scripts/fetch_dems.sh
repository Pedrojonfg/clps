#!/usr/bin/env bash
# Resume-safe PGDA DEM fetch for the D-f369 schedule.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/data/dem"
mkdir -p "$DEST"
UA="lunar-eval/0.1 (+https://github.com/Pedrojonfg/clps)"

fetch() {
  local url="$1" name="$2"
  echo "==> ${name}"
  curl -L --fail --retry 5 --retry-all-errors \
    -A "$UA" -C - -o "${DEST}/${name}" "$url"
}

fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_60S_240MPP_ADJ.TIF" "LDEM_60S_240MPP_ADJ.TIF"
fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_60S_120MPP_ADJ.TIF" "LDEM_60S_120MPP_ADJ.TIF"
fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF" "LDEM_80S_80MPP_ADJ.TIF"
fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_40MPP_ADJ.TIF" "LDEM_80S_40MPP_ADJ.TIF"
fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF" "LDEM_80S_20MPP_ADJ.TIF"
fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_83S_10MPP_ADJ.TIF" "LDEM_83S_10MPP_ADJ.TIF"
fetch "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/87S/ldem_87s_5mpp.tif" "ldem_87s_5mpp.tif"
echo "done"
