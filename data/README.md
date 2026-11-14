# Local data (not in git)

GeoTIFFs, SPICE kernels, precomputed masks and parquet indexes live here and are gitignored.

| Path | Contents |
|------|----------|
| `dem/` | PGDA LOLA DEMs used by the horizon-mask schedule (`D-f369`) |
| `kernels/` | NAIF generic kernels for local Sun/Earth geometry (`D-4ffe`) |
| `masks/` | Memory-mapped `.npy` tiles plus parquet index (P2) |
| `fixtures/` | Generated test products; committed Horizons tables live under `tests/fixtures/horizons/` |

Fetch DEMs with `scripts/fetch_dems.sh`.
