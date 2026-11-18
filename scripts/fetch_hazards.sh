#!/usr/bin/env bash
# Resume-safe Layer-B rasters: LDSM + LPSR (PGDA) and Diviner PCP (PDS).
# PCP ASCII tabs are converted to compact .npz and the .tab is deleted.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEM="${ROOT}/data/dem"
PCP="${ROOT}/data/hazards/pcp"
mkdir -p "$DEM" "$PCP"
UA="moonpark/0.1 (+https://github.com/Pedrojonfg/moonpark)"
PCP_BASE="https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/diurnal/ltim/pols"

fetch() {
  local url="$1" dest="$2"
  echo "==> $(basename "$dest")"
  curl -L --fail --retry 5 --retry-all-errors -A "$UA" -C - -o "$dest" "$url"
}

fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDSM_80S_80MPP_ADJ.TIF" \
  "${DEM}/LDSM_80S_80MPP_ADJ.TIF"
fetch "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LPSR_80S_20MPP_ADJ.TIF" \
  "${DEM}/LPSR_80S_20MPP_ADJ.TIF"

python3 "${ROOT}/scripts/fetch_pcp_bins.py" --dest "$PCP" --base "$PCP_BASE" --ua "$UA" --jobs 6
echo "done"
