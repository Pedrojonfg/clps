# External resources

**Last reviewed:** 2026-11-14
**Owner:** pj
**Scope:** external data sources, services, viewers, libraries and assets that the lunar south-pole site×time evaluator uses or has considered.
**Fact source:** [`docs/research/briefs/research-brief-data-viz-sources.md`](research/briefs/research-brief-data-viz-sources.md), plus the product pages listed under [Sources](#sources). Its recommendations are not binding. The roles below come from decision records.
**AI disclosure:** This document was drafted with SI/AI assistance and checked against the linked sources on the review date.

## Purpose

This catalogue answers five questions for every external resource: what it is, which part of the product uses it, when it is used, how it is accessed, and under what terms. It does not make choices. Where the role of a resource has been decided, the decision record is cited. Where it has not, the entry says **Pending decision** and gives no recommendation.

### Project frame

- Portfolio scope governs the project. Something will be submitted to NASA Space Apps 2026 by **2026-11-15 23:59 local time**, and work continues until **2026-11-20**. Global judging is not sought (`D-20261114-pj-d7d9`).
- The product scores a lunar site at a given time for Sun visibility (power) and Earth visibility (direct-to-Earth radio) against the local horizon, and searches for better sites or times (`D-20261111-pj-60ab`).
- Layer B (temperature, dust and related surface hazards) is in scope. Trajectories are out of scope. Data enters through body-agnostic providers (`D-20261114-pj-b8d3`).
- Provenance is part of the product: the user interface names the data and versions behind a result (`D-20261114-pj-3c91`).

### Status legend

| Status | Meaning |
|---|---|
| **Decided** | Role set by an accepted decision record (cited). |
| **Pending decision** | Candidate. Role not decided; this document makes no recommendation. |
| **Context only** | Consulted by eye, for reference, or for citations. Not a code or data dependency. |
| **Not used** | Evaluated and excluded, with the reason stated. |

### Usage legend

| When | Meaning |
|---|---|
| Build-time precompute | Read once, offline, to produce derived products (for example horizon masks). |
| Runtime (server) | Read by the backend while answering a request. |
| Runtime (browser) | Loaded by the user's browser. |
| Test-only | Used to produce saved fixtures for automated tests. |
| Context only | Not loaded by the product. |

## Summary

| Resource | Product piece | When | License | Cost | Status |
|---|---|---|---|---|---|
| NAIF SPICE generic kernels | Sun and Earth geometry | Runtime (server) and precompute | NAIF rules | $0 | Decided (`D-4ffe`); version pending |
| SPICE Toolkit | Kernel reader | Runtime (server) and precompute | NAIF rules | $0 | Decided via kernels; wrapper pending |
| SpiceyPy | Python wrapper for SPICE | Runtime (server) and precompute | MIT | $0 | Pending decision |
| Skyfield | Ephemeris library | Runtime (server) and precompute | MIT | $0 | Pending decision |
| JPL Horizons API | Ephemeris test oracle | Test-only | US Gov. work, fair use | $0 | Decided (`D-4ffe`) |
| PGDA 90 large-area DEMs | Horizon mask, slope, PSR | Build-time precompute | Public domain, cite | $0 | Decided (`D-f369`) |
| PGDA 81 5 m mosaic | Horizon mask near the pole | Build-time precompute | Public domain, cite | $0 | Decided (`D-f369`) |
| PGDA 78 site DEMs | Named sites, high-res masks | Build-time precompute | Public domain, cite | $0 | Decided (`D-f369`) |
| PGDA 69 illumination maps | Long-term averages | To be decided | Public domain, cite | $0 | Pending decision |
| Hetzner Cloud CX43 | Precompute and serving host | Precompute and runtime (server) | Commercial service | ~€16.49/mo + VAT | Decided (`D-5994`) |
| LOLA GDRs (PDS, ODE REST) | Archive behind PGDA | Context only | Public domain | $0 | Context only |
| USGS global LOLA DEM (118 m) | Global terrain | Context only | Public domain | $0 | Context only |
| LRO Diviner GDRs | Layer B temperature, rock abundance | Build-time precompute | Public domain, cite | $0 | Pending decision (engine ledger) |
| Moon Trek WMTS | Basemap and context layers | Runtime (browser) | Public domain, cite | $0 | Pending decision |
| LROC NAC/WAC mosaics | Imagery | Runtime (browser) | Public domain (PDS), credit | $0 | Pending decision |
| CesiumJS | First-person viewer engine | Runtime (browser) | Apache-2.0 | $0 | Pending decision |
| Cesium Moon (ion asset 2684829) | First-person terrain and imagery | Runtime (browser) | Cesium ion terms | $0 to $149+/mo | Pending decision |
| three.js | Alternative 3D viewer | Runtime (browser) | MIT | $0 | Pending decision |
| geotiff.js | GeoTIFF reader in JavaScript | Runtime (browser) | MIT | $0 | Pending decision |
| Lunar QuickMap | By-eye spot check | Context only | Commercial (ACT) | $0 public site | Context only |
| Lunaserv (LROC WMS) | Desktop GIS during development | Context only | Public domain (PDS) | $0 | Context only |
| ShadowCam PDS images | Texture inside permanent shadow | Context only | Public domain (PDS) | $0 | Context only |
| CLPS SPICE Data Archive | Mission kernels | Context only | NAIF / PDS | $0 | Context only |
| OpenSpace | Reference desktop viewer | Context only | MIT | $0 | Context only |
| crater-viewer | Reference code | Context only | GPL-3.0 | $0 | Not used |
| lunar-walk | Reference code | Context only | MIT code, CC BY-NC models | $0 | Not used |
| CSA Moon exploration page | None | Not used | Canadian Gov. web content | $0 | Not used |
| LADEE / LDEX | None | Not used | Public domain | $0 | Not used |
| Ames Lunar Browser, trajectory tools | None | Not used | — | — | Not used (`D-b8d3`) |

Short IDs in the table refer to the full decision IDs `D-20261114-pj-4ffe` and `D-20261114-pj-b8d3`.

## Ephemeris and geometry

### NAIF SPICE generic kernels

- **What it is:** Binary and text kernel files published by NASA's Navigation and Ancillary Information Facility (NAIF): leap seconds (LSK), planetary ephemeris (SPK), lunar orientation (binary PCK) and frame definitions (FK).
- **Product piece:** Sun and Earth azimuth and elevation at each evaluated site and time. This feeds the score and the local and deep search.
- **When:** Runtime (server) and build-time precompute. Computation is local; no network call per evaluation.
- **Access:** `https://naif.jpl.nasa.gov/pub/naif/generic_kernels/`. Kernel files should be pinned in the repository or in a lockfile of URLs and checksums.
- **License:** NAIF rules. No fee; commercial use is allowed; acknowledgement is requested. Redistributing an unmodified mirror of the toolkit requires NAIF clearance; shipping it inside the project's own tool is allowed. Not an OSI license.
- **Cost:** $0.
- **Status:** **Decided.** Sun and Earth geometry is computed locally from kernels (`D-20261114-pj-4ffe`). The kernel version and lunar frame are **Pending decision**.
- **Facts relevant to the pending choice:** PGDA terrain products are referenced to the `MOON_ME` frame of the DE421 ephemeris. Horizons sample output read on 2026-11-14 cites DE441. Whatever kernel set is chosen is named in the product's provenance (`D-20261114-pj-3c91`).

### SPICE Toolkit, SpiceyPy and Skyfield

| Library | What it is | License | Status |
|---|---|---|---|
| [SPICE Toolkit](https://naif.jpl.nasa.gov/naif/toolkit.html) (CSPICE) | NAIF's reference implementation for reading kernels and computing geometry | NAIF rules (see above) | Required by any SPICE-based path. Toolkit source must not be modified. |
| [SpiceyPy](https://github.com/AndrewAnnex/SpiceyPy) | Python wrapper around CSPICE | MIT | **Pending decision** |
| [Skyfield](https://rhodesmill.org/skyfield/) | Pure-Python astronomy library that reads JPL ephemerides | MIT | **Pending decision** |

- **Product piece:** The ephemeris provider behind the body-agnostic seam (`D-20261114-pj-b8d3`).
- **When:** Runtime (server) and build-time precompute.
- **Cost:** $0.
- **Pending:** The library choice is deferred together with frame and kernel version (`D-20261114-pj-4ffe`, value `ephemeris_library`).

### JPL Horizons API

- **What it is:** JPL Solar System Dynamics ephemeris service. Observer tables can return azimuth and elevation of the Sun or Earth for a geodetic site on the Moon.
- **Product piece:** Independent check of the local kernel computation for the smooth-horizon case.
- **When:** **Test-only.** Tables are requested once, saved as fixtures in the repository, and compared against local results with a tolerance test; tests make no network calls. At most a minimal runtime cross-check may be added later, server-side only, possibly limited to the solution proposed by local or deep search.
- **Access:** `GET https://ssd.jpl.nasa.gov/api/horizons.api`

  | Parameter | Value |
  |---|---|
  | `EPHEM_TYPE` | `'OBSERVER'` |
  | `COMMAND` | `'10'` (Sun) or `'399'` (Earth) |
  | `CENTER` | `'coord@301'` (a site on the Moon) |
  | `COORD_TYPE` | `'GEODETIC'` |
  | `SITE_COORD` | `'east_lon,lat,alt_km'` |
  | `QUANTITIES` | `'4'` (apparent azimuth and elevation) |
  | `START_TIME`, `STOP_TIME`, `STEP_SIZE` | Time window and step |

  Measured on 2026-11-14: one site, one month, 6-hour step, 121 rows, about 1 second (`D-20261114-pj-4ffe`).
- **Limitation:** Horizons elevation is measured from the plane perpendicular to local zenith on the reference ellipsoid. It ignores terrain, so it describes a smooth horizon, not the visible one. It cannot validate terrain blocking; the horizon mask needs its own check.
- **License:** US government work. The fair-use policy limits API usage, not the use of saved results. See [Usage policies](#usage-policies).
- **Cost:** $0.
- **Status:** **Decided** as test oracle (`D-20261114-pj-4ffe`). Tolerance, test cases and any runtime cross-check are deferred in the same record.

## Terrain and horizon

The horizon model is **Decided** (`D-20261114-pj-f369`). Masks reach 250 km and use a distance-graded DEM schedule built from the LOLA products below, published by NASA GSFC's Planetary Geology, Geophysics and Geochemistry Laboratory (PGDA). PGDA publishes no LOLA DEM finer than 5 m per pixel.

| Distance from the site | DEM pixel scale | Source |
|---|---|---|
| 0–250 m | Finest available: 5 m, else 10 m, else 20 m | PGDA 81 / PGDA 78, else PGDA 90 83S 10 m, else PGDA 90 80S 20 m |
| 250 m–1 km | 20 m | PGDA 90 80S 20 m (or the 5 m products resampled) |
| 1–2 km | 40 m | PGDA 90 80S 40 m |
| 2–5 km | 100 m | Resampled from PGDA 90 |
| 5–25 km | 80 m | PGDA 90 80S 80 m; 120 m (60S) where rays leave 80–90°S |
| 25–250 km | 240 m | PGDA 90 60S 240 m |

The 5 m mosaic (PGDA 81) does not support HTTP range reads; download it to the compute host.

All PGDA products listed here are south polar stereographic, in meters, in the `MOON_ME` frame of the DE421 ephemeris, with a 1737.4 km reference radius.

### PGDA 90 — Large-area south-pole LOLA DEMs

- **What it is:** Improved LOLA digital elevation models and companion layers for the south polar region, distributed as cloud-optimized GeoTIFFs (COG).
- **Product piece:** Candidate input for horizon masks, slope and roughness constraints, and the permanently shadowed region (PSR) mask.
- **When:** Build-time precompute, if adopted. Files at this size are not intended for the browser.
- **Access:** `https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/<FILENAME>`, for example `https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_60S_240MPP_ADJ.TIF`. File names follow `PREFIX_LAT_PIX_STEMS.TIF`.

  Elevation model (`LDEM_*_ADJ.TIF`) sizes:

  | Coverage | Pixel scale | File | Size |
  |---|---|---|---|
  | 60–90°S | 240 m | `LDEM_60S_240MPP_ADJ.TIF` | 210 MB |
  | 60–90°S | 120 m | `LDEM_60S_120MPP_ADJ.TIF` | 785 MB |
  | 60–90°S | 60 m | `LDEM_60S_60MPP_ADJ.TIF` | 2.9 GB |
  | 75–90°S | 30 m | `LDEM_75S_30MPP_ADJ.TIF` | 2.7 GB |
  | 80–90°S | 80 m | `LDEM_80S_80MPP_ADJ.TIF` | 181 MB |
  | 80–90°S | 40 m | `LDEM_80S_40MPP_ADJ.TIF` | 685 MB |
  | 80–90°S | 20 m | `LDEM_80S_20MPP_ADJ.TIF` | 2.6 GB |
  | 83–90°S | 10 m | `LDEM_83S_10MPP_ADJ.TIF` | 4.8 GB |

  Sibling layers exist for each grid and are usually larger than the elevation file (for example 3.7–3.8 GB each at 80°S, 20 m):

  | Layer | Content |
  |---|---|
  | `LDEC_…` | LOLA spot count per pixel |
  | `LDEM_…_ERR` | Height error (m) |
  | `LDEM_…_EFFRES` | Effective resolution (m) |
  | `LDEM_…_HILL` | Hillshade (45° altitude, 45° azimuth) |
  | `LDSM_…`, `LDSM_…_ERR` | Slope and slope error (degrees) |
  | `LDRM_80S_…` | Multi-baseline roughness, slope, RMS deviation, Hurst exponent (50 m and 1000 m grids) |
  | `LPSR_80S_20MPP_ADJ` | PSR map (148 MB GeoTIFF) and PSR shapefiles |

  Raw point clouds are also published (`LDEM_80S_ADJ.XYZI`, 13 GB; `LDEM_60S_ADJ.XYZI`, 48 GB).
- **License:** NASA data, public domain in practice. Cite Barker et al. (2021).
- **Cost:** $0.
- **Status:** **Decided** (`D-20261114-pj-f369`): 10 m, 20 m, 40 m, 80 m, 120 m and 240 m grids in the mask schedule.

### PGDA 81 — South-pole 5 m mosaic

- **What it is:** A 5 m/pixel LOLA DEM mosaic of 87–90°S built from 97 blended 20 × 20 km fields.
- **Product piece:** Candidate high-resolution terrain close to the pole.
- **When:** Build-time precompute, if adopted.
- **Access:** `https://pgda.gsfc.nasa.gov/products/81`. Elevation file `https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/87S/ldem_87s_5mpp.tif` (3.3 GB). Companion files: hillshade (820 MB), slope (4.9 GB), count map (140 MB).
- **License:** Public domain; cite Barker et al. (2021).
- **Cost:** $0.
- **Status:** **Decided** (`D-20261114-pj-f369`): first 250 m of masks within 87–90°S.

### PGDA 78 — High-resolution DEMs for named sites

- **What it is:** 5 m/pixel LOLA DEMs for 26 named south-pole sites (27 entries; `Site20v2` is an extended version of Site 20). Sites include Connecting Ridge, Shackleton rim, Nobile rim, de Gerlache rim, Leibnitz beta plateau, Malapert massif, Haworth, Shoemaker, Amundsen rim and Faustini rim. Each site provides elevation, spot counts, slope, height and slope uncertainty, 100 statistical clones, point clouds and, for some sites, region-of-interest shapefiles.
- **Product piece:** Candidate site catalogue labels and high-resolution horizon masks for a curated site list. The candidate site list beyond these sites is still open (task fog in `T-20261114-pj-12b7`).
- **When:** Build-time precompute, if adopted.
- **Access:** `https://pgda.gsfc.nasa.gov/products/78`. GeoTIFF per site, for example `Site04_final_adj_5mpp_surf.tif`.
- **Note:** About 90% of 5 m pixels are interpolated because of LOLA's track spacing. Median RMS height error is about 0.30–0.50 m.
- **License:** Public domain; cite Barker et al. (2021).
- **Cost:** $0.
- **Status:** **Decided** (`D-20261114-pj-f369`): first 250 m of masks at the named sites; reference DEMs for the mask tolerance test. The site list itself is still open.

### Archive and global terrain (context only)

| Resource | What it is | Why context only |
|---|---|---|
| [LOLA GDRs via ODE REST API](https://oderest.rsl.wustl.edu/) | PDS archive of LOLA gridded data records | The PGDA GeoTIFFs above are derived from this archive and are easier to consume. |
| USGS global LOLA DEM | Global 118 m elevation model | Coarser than the PGDA polar grids; listed for completeness. |

## Illumination products

### PGDA 69 — Lunar polar illumination and Earth visibility

- **What it is:** Long-term average solar illumination, permanent shadow, average Earth visibility and sky visibility for both poles. Averages are computed with hourly steps over about 18.6 years (one lunar nutation cycle).
- **Resolution and coverage (south):** 240 m (65–90°S), 120 m (75–90°S), 60 m (85–90°S). Sky visibility at 240 m only.
- **Access:** `https://pgda.gsfc.nasa.gov/products/69`. Formats: PDS IMG, GeoJPEG2000, GeoTIFF and COG.
- **Caveats stated by the authors:** These are averages over long periods; the authors invite contact for a specific duration at a specific site. Earth counts as visible if any part of its disc clears the terrain, which is slightly optimistic for radio links. COG overviews average full-resolution values, which matters for quantitative use.
- **Product piece:** To be decided. The averages do not describe the illumination at a specific date and time.
- **License:** Public domain; cite Mazarico et al. (2011).
- **Cost:** $0.
- **Status:** **Pending decision** (role of long-term averages).

## Surface context (layer B)

Layer B is in scope (`D-20261114-pj-b8d3`). Temperature and dust models are deferred to the engine ledger.

| Resource | What it is | Status |
|---|---|---|
| [LRO Diviner GDRs](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | Level 2: brightness temperature binned by mapping cycle, day and night. Level 3: rock abundance, soil temperature, Christiansen feature. | **Pending decision** (engine ledger). No public time series predicts temperature at an arbitrary future hour. |
| PGDA slope, roughness and PSR layers | See PGDA 78, 81 and 90 above | **Pending decision** (engine ledger) |
| Dust | No public site×time dust lofting or plume dataset exists. | No data source identified. |

## Visualization and basemaps

The horizon chart and four-case timeline are drawn by project code; no external service renders them for an arbitrary site and date. The visualization set is still deferred (`D-20261114-pj-d7d9`, checks raised). The first-person viewer and the basemap are both **Pending decision**.

### Moon Trek WMTS

- **What it is:** NASA JPL Solar System Treks viewer for the Moon, with public OGC WMTS tile services. No API key.
- **Product piece:** Candidate basemap and context layers (for example south-pole illumination percentage and average Earth visibility).
- **When:** Runtime (browser), if adopted.
- **Access:** Tile pattern `https://{endpoint}/1.0.0/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png`. Capabilities:
  - `https://trek.nasa.gov/tiles/Moon/SP/WAC_POLE_ILL_PCT_SOUTH_100M/1.0.0/WMTSCapabilities.xml`
  - `https://trek.nasa.gov/tiles/Moon/SP/AVGVISIB_85S_060M_201608_EARTH_SP/1.0.0/WMTSCapabilities.xml`
- **Note:** Cross-origin (CORS) access from browsers is not documented as part of the service contract. If browsers block tiles, a proxy is needed.
- **License:** The FGDC records checked list no access or use constraints. Cite NASA/JPL and the instrument team.
- **Cost:** $0.
- **Status:** **Pending decision** (basemap: Moon Trek WMTS or self-served PGDA tiles).

### LROC imagery

- **What it is:** Lunar Reconnaissance Orbiter Camera mosaics. The south-pole NAC average mosaic covers 85.5–90°S, orthorectified on the LOLA 5 m polar DEM; its FGDC record credits USGS and LMMP. The WAC global mosaic credits the LROC team.
- **Product piece:** Candidate imagery for the basemap or viewer, through Moon Trek, Cesium Moon or PDS.
- **License:** PDS products are public domain; credit NASA/GSFC/Arizona State University. Images on the LROC website that are not PDS products are copyrighted: education use is allowed with credit, and commercial use needs permission.
- **Status:** **Pending decision** (follows the basemap and viewer decisions).

### CesiumJS and Cesium Moon

- **What it is:** CesiumJS is an open-source 3D globe engine (`Cesium.Ellipsoid.MOON`, 3D Tiles). [Cesium Moon](https://cesium.com/platform/cesium-ion/content/cesium-moon/) is ion asset `2684829`: Moon terrain and imagery from LRO data. Cesium lists about 5 m terrain south of 87.5°S, NAC imagery near 1 m inside 85.5°S and WAC about 100 m elsewhere; sources listed are NASA and USGS Astrogeology.
- **Product piece:** Candidate first-person view.
- **When:** Runtime (browser), streamed from Cesium ion, if adopted.
- **License:** CesiumJS is Apache-2.0. Cesium Moon is covered by Cesium ion and Global 3D Content terms.
- **Cost:** ion Community plan is free for personal non-commercial projects, exploratory evaluation and unfunded educational activities, with 15 GB/month streaming and 10 GB storage. Cesium's FAQ requires a paid plan for companies over $50K in annual revenue or funding, government projects, funded educational research, or usage above the free quota. Commercial plan from $149/month (individual).
- **Status:** **Pending decision** (first-person viewer: CesiumJS with Cesium Moon, three.js, or none). Token handling is described under [Usage policies](#usage-policies).

### three.js and geotiff.js

- **What it is:** [three.js](https://threejs.org/) is a WebGL 3D library. [geotiff.js](https://geotiffjs.github.io/) reads GeoTIFF and COG files in JavaScript.
- **Product piece:** Candidate locally built terrain mesh from a clipped PGDA GeoTIFF, as an alternative first-person view. geotiff.js would also be needed for any browser-side reading of PGDA rasters.
- **When:** Runtime (browser), if adopted.
- **License:** MIT (both).
- **Cost:** $0.
- **Status:** **Pending decision.**

### Context-only viewers

| Resource | What it is | Use |
|---|---|---|
| [Lunar QuickMap](https://quickmap.lroc.im-ldi.com/) | Public instance of ACT-REACT QuickMap, a commercial web GIS by ACT with LROC/ASU. Includes TerrainShadows (Sun or Earth as light source). | By-eye spot check of one or two epochs. No public API for illumination at a given time. Runtime use is out of scope (`T-20261114-pj-12b7`). Do not scrape tiles or copy the software. Stack IDs in URLs are internal state, not a stable API. |
| Lunaserv (LROC WMS) | WMS service for PDS LROC imagery, usable from QGIS | Desktop development aid only. The historical endpoint `http://webmap.lroc.asu.edu/` may have moved. Cite Estes et al. (2013) if used in research. |
| ShadowCam PDS images | Imagery inside permanently shadowed regions | Possible later texture where WAC mosaics are black. Not needed for the score. |

## Reference and third-party repositories

None of these is a dependency. They were reviewed for ideas only.

| Project | License | Note |
|---|---|---|
| [OpenSpace](https://github.com/OpenSpace/OpenSpace) | MIT | Native C++ desktop/planetarium application with an LRO/LOLA globe. Reference for camera behaviour. |
| [crater-viewer](https://github.com/vlas-sokolov/crater-viewer) | GPL-3.0 | GeoTIFF-to-three.js mesh. Source must not be copied into this repository if it is to stay permissively licensed. |
| [lunar-walk](https://github.com/hh-hang/lunar-walk) | MIT code; models CC BY-NC and CC BY-SA | Procedural terrain, not a LOLA surface. Models are non-commercial or share-alike and are not reused. |
| Stellarium, Celestia | GPL family | Sky simulators; a different product. |
| NASA Web WorldWind | Apache-2.0 | Older globe stack. |
| [Unofficial dataset index](https://spacedata.swapniltamse.com/challenges/lunar-landing-site-navigator/) | — | Useful link list; not a NASA source. |
| [CLPS SPICE Data Archive](https://naif.jpl.nasa.gov/pub/naif/pds/pds4/clps/clps_spice/document/spiceds_v003.html) | NAIF / PDS | Mission kernels for CLPS payloads; trajectory-oriented, so context only. |

## Not used and why

| Resource | Reason |
|---|---|
| QuickMap or ACT software at runtime | Proprietary commercial software with no public API for illumination at a given time. Out of scope (`T-20261114-pj-12b7`). |
| [CSA Moon exploration page](https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/) | Outreach content (Artemis, Gateway, Canadarm3, LEAP). No lunar DEM or ephemeris. CSA open data mentioning the Moon is terrestrial analogue fieldwork. Link out only; do not copy text or infographics. |
| Trajectory products, NASA Ames "Lunar Browser" | Full trajectory computation is out of the product (`D-20261114-pj-b8d3`). An optional approach filter may consume external trajectory products later. |
| LADEE / LDEX | Exosphere dust measurement, not a landing-site dust field. |
| Mapbox and other Earth tile hosts | Wrong body. |
| Dust or thermal CFD codes | No validated input data for a site×time model. |

## Licensing and attribution

NASA data used here is US government work. NASA SMD policy SPD-41a directs new science data toward CC0. Citation is still expected and is part of the product's provenance. This section is not legal advice.

| Asset | Terms | Attribution required |
|---|---|---|
| NASA PDS, LOLA, PGDA, Diviner data | Public domain (US government work) | Cite product papers |
| Moon Trek tiles | No access or use constraints in the FGDC records checked | Cite NASA/JPL and instrument team |
| LROC PDS products | Public domain | NASA/GSFC/Arizona State University |
| LROC non-PDS website images | Copyrighted; education use with credit | Do not use |
| Horizons output | US government work; API fair use applies | Cite JPL Horizons |
| SPICE Toolkit and kernels | NAIF rules; no fee; no redistribution of an unmodified mirror without clearance | Acknowledge NAIF |
| SpiceyPy, Skyfield, three.js, geotiff.js | MIT | Keep license notices |
| CesiumJS | Apache-2.0 | Keep license and NOTICE |
| Cesium Moon | Cesium ion terms; free non-commercial tier | Keep the on-screen credits CesiumJS displays |
| QuickMap software | ACT commercial product | Not used in the product |
| OpenSpace | MIT | Not used |
| crater-viewer | GPL-3.0 | Not used |
| lunar-walk | MIT code; CC BY-NC / CC BY-SA models | Not used |

### Ready-to-paste credit lines

Use only the lines for resources the product actually ships with.

```text
Lunar topography: LRO Lunar Orbiter Laser Altimeter (LOLA) data products from the NASA Goddard Planetary Geology, Geophysics and Geochemistry Laboratory (PGDA). Barker, M.K., et al. (2021), Improved LOLA Elevation Maps for South Pole Landing Sites: Error Estimates and Their Impact on Illumination Conditions, Planetary & Space Science, 203, 105119, doi:10.1016/j.pss.2020.105119.
```

```text
Long-term illumination and Earth visibility: Mazarico, E., et al. (2011), Illumination conditions of the lunar polar regions using LOLA topography, Icarus, 211, 1066-1081, doi:10.1016/j.icarus.2010.10.030.
```

```text
Geometry computed with the SPICE system from NASA's Navigation and Ancillary Information Facility (NAIF), JPL. Kernels: <list pinned kernel files>.
```

```text
Ephemeris validation: JPL Horizons On-Line Ephemeris System, NASA/JPL Solar System Dynamics.
```

```text
Imagery: Lunar Reconnaissance Orbiter Camera (LROC), NASA/GSFC/Arizona State University.
```

```text
Basemap tiles: NASA Moon Trek, NASA/JPL. Layer: <layer id>, <instrument team>.
```

```text
3D terrain: Cesium Moon, Cesium ion. Source data: NASA and USGS Astrogeology.
```

## Usage policies

### JPL Horizons and SSD APIs (fair use)

From the [SSD API fair-use policy](https://ssd-api.jpl.nasa.gov/doc/index.php), read 2026-11-14:

- Send only requests reasonably necessary for the use case; cache and reuse results.
- Send one request at a time; no simultaneous requests.
- Handle errors, rate limits and outages by backing off, not by retrying repeatedly.
- Send an application-specific `User-Agent` header with product name, version and contact information.
- Do not embed the APIs in a website (NASA CORS policy). The browser must never call Horizons directly.
- Data formats can change without notice; check the `version` field in each response.

In this project, Horizons tables are requested once with an application-specific `User-Agent` and stored as test fixtures (`D-20261114-pj-4ffe`).

### Cesium ion tokens

Applies only if Cesium Moon is adopted.

- Keep ion access tokens out of git. Load them from environment variables or untracked configuration.
- A token used in a browser is visible to anyone. Restrict it to the required asset and allowed URLs, and rotate it if it leaks.
- Monitor streaming usage against the 15 GB/month Community quota.

### NASA Space Apps 2026 rules

From the [participant FAQ](https://www.spaceappschallenge.org/resources/participant-faqs/) and an [organizer answer on GitHub](https://github.com/nasa/spaceapps/discussions/1849), read 2026-11-14:

- Use of SI/AI tools (the 2026 FAQ uses the term "Super Intelligence") must be disclosed in the submission. AI-generated images and videos need a visible watermark; AI-generated code and data must be acknowledged in descriptive text and metadata.
- AI-generated content must not use, contain or modify NASA branding or design elements, such as NASA logos, flags or mission identifiers.
- Global awards require meaningful use of at least one NASA data source from the challenge Resources. Global judging is not sought for this project (`D-20261114-pj-d7d9`).

## Pending decisions

Each item below is open. This document does not recommend an option.

1. **Horizon model and DEM resolution:** decided in `D-20261114-pj-f369`. Still open inside it: spacing and resolution around the demo site.
2. **Role of PGDA 69 long-term averages:** whether and how illumination and Earth-visibility averages appear in the product.
3. **Ephemeris details:** kernel version, lunar frame and library (SpiceyPy or Skyfield). Also deferred: test tolerance, test cases and any runtime Horizons cross-check (`D-20261114-pj-4ffe`).
4. **First-person viewer:** CesiumJS with Cesium Moon, three.js, or none.
5. **Basemap:** Moon Trek WMTS or self-served PGDA tiles.
6. **Precompute hosting:** decided in `D-20261114-pj-5994`: pj's PC for the demo, then one month of a Hetzner CX43 (CAX31 if out of stock) for the 100 m cap and serving.
7. **Layer B models:** temperature and dust, in the engine ledger (`D-20261114-pj-b8d3`).

## Sources

Decision records:

- [`D-20261114-pj-d7d9`](records/decisions/D-20261114-pj-d7d9-frame-portfolio-until-nov20.md) — portfolio scope through 2026-11-20; Space Apps submission on 2026-11-15
- [`D-20261114-pj-4ffe`](records/decisions/D-20261114-pj-4ffe-ephemeris-local-kernels.md) — local kernels; Horizons as test oracle
- [`D-20261114-pj-b8d3`](records/decisions/D-20261114-pj-b8d3-layer-b-bodies-trajectory.md) — layer B in, trajectories out, body-agnostic seam
- [`D-20261114-pj-3c91`](records/decisions/D-20261114-pj-3c91-audience-portfolio.md) — audience; provenance required
- [`D-20261111-pj-60ab`](records/decisions/D-20261111-pj-60ab-product-question.md) — product question
- [`T-20261114-pj-12b7`](records/tasks/T-20261114-pj-12b7-data-viz-sources.md) — data and visualization sources task

External:

- https://pgda.gsfc.nasa.gov/products/90 — large-area south-pole LOLA DEMs
- https://pgda.gsfc.nasa.gov/products/81 — 5 m mosaic, 87–90°S
- https://pgda.gsfc.nasa.gov/products/78 — 5 m DEMs for named sites
- https://pgda.gsfc.nasa.gov/products/69 — polar illumination and Earth visibility
- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/ — SPICE generic kernels
- https://naif.jpl.nasa.gov/naif/rules.html — NAIF rules
- https://ssd.jpl.nasa.gov/horizons/ — JPL Horizons
- https://ssd-api.jpl.nasa.gov/doc/horizons.html — Horizons API documentation
- https://ssd-api.jpl.nasa.gov/doc/index.php — SSD API fair-use policy
- https://trek.nasa.gov/moon/ — Moon Trek
- https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=moon — Trek WMTS API
- https://lroc.im-ldi.com/about/terms — LROC terms and citation
- https://quickmap.lroc.im-ldi.com/ — Lunar QuickMap
- https://www.actgate.com/products/quickmap — ACT QuickMap product
- https://pds-geosciences.wustl.edu/missions/lro/diviner.htm — Diviner data
- https://oderest.rsl.wustl.edu/ — ODE REST API
- https://psdi.astrogeology.usgs.gov/moon/standards/licensing/ — SPD-41a / CC0 guidance
- https://cesium.com/platform/cesium-ion/content/cesium-moon/ — Cesium Moon
- https://cesium.com/platform/cesium-ion/pricing — Cesium ion plans and FAQ
- https://cesium.com/blog/2024/08/06/introducing-cesium-moon-terrain/ — Cesium Moon announcement
- https://github.com/AndrewAnnex/SpiceyPy — SpiceyPy
- https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/ — CSA Moon exploration
- https://www.spaceappschallenge.org/resources/participant-faqs/ — Space Apps participant FAQ
- https://github.com/nasa/spaceapps/discussions/1849 — Space Apps organizer answer on AI use and branding
