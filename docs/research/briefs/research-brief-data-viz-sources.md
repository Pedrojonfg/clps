# Research Brief: Data and visualization sources for the site×time evaluator

**Depth:** wide
**Date:** 2026-11-14
**Purpose:** Choose what actually feeds the score, the maps, and the first-person view, against portfolio scope (`D-9f04`, `D-b8d3`, `D-60ab`). Recommendation for the engine ledger. Not a locked decision record.

## Executive Summary

The four links on the challenge resource list (LROC QuickMap, Moon Trek, JPL Horizons, CSA Moon exploration) are viewers plus one ephemeris service. They do not expose the site×time score. Compute Sun and Earth directions offline with SPICE, and block them with a horizon mask built from a LOLA DEM (PGDA). Use Horizons only as a server-side check of the smooth-horizon case. Draw the horizon chart ourselves. Put the first-person view on CesiumJS plus Cesium Moon (free ion Community plan while the project stays non-commercial): south-pole terrain is already tiled at about 5 m, with NAC imagery near 1 m inside 85.5°S. Temperature and dust do not have a public time series; treat them as labeled climatology and static hazard layers.

Recommended runtime cost: **$0**. The only paid switch later is Cesium ion Commercial, from $149/month, if the demo becomes a product or the free streaming quota is exceeded. Do not buy ACT QuickMap.

## How this sits on the current product

| Product piece (`D-60ab`, `D-9f04`, `D-b8d3`) | What must be true of the data | Recommended source |
|---|---|---|
| Score at a site and a time (Sun, Earth, both, neither) | Elevation at that azimuth, at that time, against the **local** horizon | SPICE directions + PGDA DEM horizon mask |
| Thresholds, neighborhood search, deep search | Many sites × many times, offline, cacheable | Precomputed masks on a site grid; ephemeris is cheap per time |
| Useful visualizations | Horizon silhouette and a four-case timeline first; a truthful camera second | Custom chart; Cesium Moon for the camera |
| Provenance | Kernel set, DEM version, and frame named in the UI | Pin DE421-family kernels to match PGDA `MOON_ME`, and say so |
| Temperature, dust, related hazards | In the score only if the model is honest | Diviner climatology + static hazard grids. No dust time series |
| Full trajectory | Out | Do not call Ames Lunar Browser or invent a propagator |
| Other bodies later | Providers, not Moon types hardcoded | Same seams: ephemeris, horizon, hazards, imagery. Trek and Cesium already have Mars tiles; PGDA does not |

The earlier domain brief (`research-brief-clps-domain.md`) listed this menu. This brief picks from it.

## The four official links

| Link | What it actually is | Use in this product |
|---|---|---|
| [Lunar QuickMap](https://quickmap.lroc.im-ldi.com/) | Public face of ACT-REACT QuickMap, a commercial web GIS (ACT, with LROC/ASU). The shared URL opens a wide south-polar window in projected meters, with Earth shadow enabled. `stack=3314` is an internal QuickMap state, not a dataset id. | Hands-on reference and a spot-check of our shadow against their TerrainShadows view. No public API for illumination-at-a-time. Do not scrape tiles or copy the app. |
| [Moon Trek](https://trek.nasa.gov/moon/) | NASA JPL viewer. Public OGC WMTS tiles, including south-pole illumination percent and average Earth visibility. | Context basemap in our UI. Those layers are long-term averages, so they do not replace the score. |
| [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) | Ephemeris service. Observer tables return azimuth and elevation from a lunar geodetic site. | Validation of the **smooth** horizon (no terrain). Server-side, cached, one request at a time. |
| [CSA Moon exploration](https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/) | Outreach: Artemis, Gateway, Canadarm3, LEAP. | No engineering dataset. CSA open data that mentions the Moon is analogue fieldwork (a Quebec quarry), not a lunar DEM. |

Horizons fair-use rules (SSD API docs, read 2026-11-14): cache results, one request at a time, back off on errors, send an application-specific `User-Agent` with contact info. Explicit rule: do not embed these APIs in a website (NASA CORS policy). A browser must not call Horizons directly.

Horizons elevation is measured from the plane perpendicular to local zenith on the reference ellipsoid. It is not the visible horizon. At the south pole the terrain term dominates. Sample output currently cites DE441; PGDA grids cite DE421 `MOON_ME`. Expect close agreement on smooth-horizon angles and do not require bit-identical numbers.

## Compute path (the score)

### Ephemeris — SPICE, offline

- Library: [SpiceyPy](https://github.com/AndrewAnnex/SpiceyPy) (MIT wrapper). Toolkit itself: NAIF, no fee, commercial use allowed, acknowledgement encouraged. Redistribution of an unmodified toolkit mirror needs NAIF clearance; shipping it inside our own tool is allowed. Do not modify toolkit source.
- Kernels: generic kernels from `https://naif.jpl.nasa.gov/pub/naif/generic_kernels/` (leap seconds, planetary SPK, lunar PCK/FK/PA). Pin versions in-repo (or a lockfile of URLs and checksums).
- Frame: PGDA products are in the DE421 `MOON_ME` frame, polar stereographic, radius 1737.4 km. Load a kernel set consistent with that frame and name it in provenance. A newer planetary kernel without a stated frame is a provenance bug.
- Why not Skyfield as the engine: Skyfield is also MIT and uses JPL ephemerides, and it is a fine cross-check. The lunar body-fixed frames that match LOLA are the SPICE frames. One engine in the hot path.

### Horizon mask — PGDA / LOLA, precomputed

For each candidate site, from the DEM, store max terrain elevation angle versus azimuth. At runtime, Sun or Earth is visible when its elevation at that azimuth clears the mask. That is the whole geometric core.

| Product | What | Role |
|---|---|---|
| [PGDA 90](https://pgda.gsfc.nasa.gov/products/90) | South-pole LOLA DEM, cloud-optimized GeoTIFF, polar stereographic. 20 m/px products cover 80–90°S (`LDEM_80S_20MPP_ADJ.TIF`), with slope, roughness, error, hillshade, PSR prefixes | Default grid for search. 20 m is enough to build masks over a region |
| [PGDA 81](https://pgda.gsfc.nasa.gov/products/81) | 5 m/px mosaic, 87–90°S. Multi-GB GeoTIFFs | Named sites inside 87°S when the demo needs a tighter mask |
| [PGDA 78](https://pgda.gsfc.nasa.gov/products/78) | 5 m/px DEMs, slopes, uncertainty for named sites (Shackleton rim, de Gerlache, Nobile, Malapert, Connecting Ridge, and others) | Site catalogue labels plus high-res masks for the curated list |
| [PGDA 69](https://pgda.gsfc.nasa.gov/products/69) | Average illumination, permanent shadow, average Earth visibility over ~18.6 years, hourly steps, 60–240 m/px. GeoTIFF and COG. Earth is “visible” if any part of the disc clears terrain, so it is slightly optimistic for a DSN link | Map context and a search prior. **Not the score.** Averages hide the date the planner actually has. Authors say to contact them for a specific interval; do not block on that |

PDS LOLA GDRs via the [ODE REST API](https://oderest.rsl.wustl.edu/) are the archive behind these grids. Prefer the PGDA GeoTIFFs over hunting raw GDRs. USGS also hosts the global 118 m LOLA DEM; that resolution is too coarse for a polar horizon mask.

Cite Barker et al. 2021 for the improved south-pole maps, and Mazarico et al. 2011 for the illumination method.

### Horizons — check, not the loop

`GET https://ssd.jpl.nasa.gov/api/horizons.api`

Observer ephemeris, `CENTER='coord@301'`, `COORD_TYPE='GEODETIC'`, `SITE_COORD='east_lon,lat,alt_km'`, `QUANTITIES='4'` (azimuth, elevation). `COMMAND='10'` is the Sun, `'399'` is Earth. Run from our server, cache by site and time window, compare a handful of epochs to SPICE on a smooth horizon. Quantity tables of thousands of sites belong in SPICE.

## Visualization path

The interface has three different pictures. They should not share one library.

### 1. Horizon chart and timeline — custom, primary

Azimuth–elevation plot: terrain silhouette from our mask, Sun and Earth tracks for the chosen window, time-to-set, and the four cases (both / Sun only / Earth only / neither). This is the picture that makes the score legible. No external API draws it for an arbitrary site and date. Canvas or SVG. No map library.

### 2. Context map — Trek tiles and PGDA rasters

Moon Trek WMTS (public, no key). Documented pattern:

`https://{endpoint}/1.0.0/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png`

Capabilities for the layers called out for this challenge:

- `https://trek.nasa.gov/tiles/Moon/SP/WAC_POLE_ILL_PCT_SOUTH_100M/1.0.0/WMTSCapabilities.xml`
- Earth visibility layer id `AVGVISIB_85S_060M_201608_EARTH_SP` (same host, `Moon/SP/…`)

South-pole NAC mosaic metadata (access constraints: none; use constraints: none): LROC NAC average mosaic inside 85.5°S, orthorectified on the LOLA 5 m polar DEM. FGDC record credits USGS / LMMP. WAC global mosaic credits the LROC team. Cite NASA/GSFC/ASU for LROC imagery.

Trek is US government work in practice (public domain; cite). Some apps proxy `trek.nasa.gov` in development because browser CORS is not part of the contract. If the browser blocks tiles, proxy them. Do not depend on an undocumented CORS header.

Lunaserv (LROC WMS) is a desktop/QGIS path for the same PDS imagery during development. Cite Estes et al. 2013 if used in research. The historical endpoint `http://webmap.lroc.asu.edu/` may have moved with the `im-ldi.com` domain. Not a runtime dependency.

### 3. First person — CesiumJS + Cesium Moon

This is the visualization problem the official viewers already solved and that we should not rebuild.

- Engine: [CesiumJS](https://cesium.com/), Apache-2.0. `Cesium.Ellipsoid.MOON`, globe off, load 3D Tiles.
- Content: [Cesium Moon](https://cesium.com/platform/cesium-ion/content/cesium-moon/), ion asset id `2684829` (as published on the Cesium Moon page). 3D Tiles from LRO: south of 87.5°S the terrain is about 5 m; NAC imagery about 1 m inside 85.5°S; WAC about 100 m farther out. Sources listed by Cesium: NASA and USGS Astrogeology.
- Account: ion Community is free for personal non-commercial projects and unfunded education. Global 3D content, including Cesium Moon, is included with an ion account. Community streaming quota is 15 GB/month (pricing page, read 2026-11-14), which is enough for a portfolio demo.
- Paid: Commercial plan from $149/month (individual) if the use becomes commercial, the account holder’s company is over the revenue/funding line in Cesium’s FAQ, or the quota is exceeded. The score engine does not import Cesium, so the viewer can be swapped later.
- Lighting: drive the Sun direction from our SPICE state so the picture matches the score. The mesh is the backdrop; it is not a second illumination model.
- Token: an ion token in a frontend is visible. Keep it out of git. Quota abuse is the operational risk, not a license leak of NASA data.

Fallback if ion terms or quota become a problem: build a local mesh with three.js (MIT) from a clipped PGDA GeoTIFF (geotiff.js, MIT) plus a hillshade or a small NAC crop. That is a site diorama, not a streamed globe. Implement it ourselves.

Repos looked at and not taken as dependencies:

| Project | License | Why it stays out of the app |
|---|---|---|
| [OpenSpace](https://github.com/OpenSpace/OpenSpace) | MIT | Excellent LRO/LOLA globe, but a native C++ desktop/planetarium app. Study the camera, do not embed. |
| [crater-viewer](https://github.com/vlas-sokolov/crater-viewer) | GPL-3.0 | GeoTIFF to three.js mesh. The idea is fine; the code is not, if we want a permissive portfolio repo. |
| [lunar-walk](https://github.com/hh-hang/lunar-walk) | MIT code; models include CC BY-NC and CC BY-SA | Procedural terrain and a game loop. Not a LOLA surface. Skip the models. |
| Stellarium, Celestia | GPL family | Sky simulators. Wrong product, and GPL if linked. |
| NASA Web WorldWind | Apache-2.0 | Older globe stack. Cesium is the maintained Moon path. |

QuickMap’s TerrainShadows (2D and 3D, Sun or Earth as the light, traverse lighting, line of sight) is the expert tool we are not licensing. Use the public site to check one or two epochs of our mask. ACT sells the product; the public LROC instance is the free window.

## Layer B — temperature and dust

| Need | Public data | Honest use |
|---|---|---|
| Temperature | [LRO Diviner GDRs](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm). Level 2: brightness temperature binned by mapping cycle, split day/night. Level 3: rock abundance, soil temperature, Christiansen feature | Static rock-abundance and soil-temperature grids as hazards. A temperature-versus-local-time climatology from the bins, multiplied by our shadow state (in shadow, use the night/PSR side). Label it climatology. It is not a forecast for an arbitrary future hour |
| Dust | No public site×time lofting or plume field. LADEE/LDEX is an exosphere measurement, not a landing-site score | Static proxies already in the grids: Diviner rock abundance, PGDA slope and roughness, PSR mask. Say “hazard proxy” in the UI. Do not invent a plume model for v1 |
| Slope / roughness | PGDA slope and roughness GeoTIFFs (products 78, 81, 90) | Constraint inputs the engine ledger can threshold |

## Licenses (non-commercial portfolio, public repo assumed permissive)

| Asset | Terms | Fits a public non-commercial repo? |
|---|---|---|
| NASA PDS / LOLA / Diviner / PGDA grids | US government work. NASA SMD SPD-41a points new SMD data at CC0. Cite anyway | Yes |
| LROC imagery from PDS or PDS interfaces | Public domain. Credit `NASA/GSFC/Arizona State University`. Research citations: Robinson et al. 2010 and the product-specific papers | Yes |
| LROC website images that are not PDS products | Copyrighted. Education allowed with credit. Commercial use needs permission | Use PDS products, not featured-image downloads |
| Trek tiles | No access or use constraints on the FGDC records checked. Cite NASA/JPL and the instrument team | Yes |
| Horizons output | US government work. Fair-use limits on the API, not on a cached table we computed ourselves | Yes, within the API rules |
| SPICE toolkit | NAIF rules, no fee, commercial OK, cite. Not an OSI license; do not treat it as MIT | Yes |
| SpiceyPy, Skyfield, three.js, geotiff.js | MIT | Yes |
| CesiumJS | Apache-2.0 | Yes, including a later commercial app |
| Cesium Moon via ion Community | Cesium Global 3D Content terms. Free for personal non-commercial and unfunded education. Commercial use needs a paid plan | Yes while this stays a portfolio. The viewer is replaceable |
| QuickMap software | ACT commercial product. Public site is a viewer for PDS holdings | Use the site. Do not copy the software |
| CSA page text and infographics | Canadian government web content. Not a data product we redistribute | Link out; do not scrape copy into the UI |
| OpenSpace | MIT, with credit | Only if we ever shell out to it. Not the plan |
| crater-viewer and other GPL viewers | GPL-3.0 | Do not copy source into the repo |

This is not legal advice. The practical rule: NASA numbers and rasters with citation, permissive libraries, Cesium Moon only under the ion plan that matches how the demo is used.

## What we will not pay for

- ACT QuickMap / TerrainShadows as a service. It is the expensive way to rent the visualization we can check by eye.
- Mapbox or other Earth tile hosts. They are the wrong body.
- A dust or thermal CFD code. The portfolio claim breaks if the number is decorative.

Optional later, still $0: ShadowCam PDS images for texture inside permanent shadow, where a WAC mosaic is black. Not needed for the score.

## Architecture seam

```
EphemerisProvider     Moon: SPICE kernels. Later: same interface, Mars kernels
HorizonProvider       Moon: PGDA mask. Later: MOLA or another DEM
SurfaceHazardProvider Moon: Diviner + LOLA slope/roughness/PSR
ImageryProvider       Moon: Cesium Moon and/or Trek WMTS. Later: Cesium Mars, Trek Mars
Score + search        Body-agnostic. Consumes the four providers
```

Horizons stays a test fixture (`SmoothHorizonOracle`), not a provider in the request path.

## Risks

- Cesium ion Community forbids commercial use and caps streaming. A viral demo can exhaust 15 GB/month. Mitigation: the mesh is not in the score path; fall back to a clipped three.js mesh.
- An ion token in the client can be reused by strangers. Mitigation: restrict the token, rotate it, keep it out of git.
- PGDA 5 m mosaics are multi-GB. Do not load them in the browser. Precompute masks; stream pictures through Cesium or Trek.
- Calling the long-term average “the illumination on this date” would make the score false. The UI should show averages as context with their time span (about 18.6 years).
- DE421 versus the ephemeris Horizons is using (DE441 in a 2026 sample). Validation tolerances must allow that, plus the terrain term.
- QuickMap stack ids and projection codes are not a stable API.

## Open point (does not block the recommendation)

Accept Cesium ion Community for the first-person view under the non-commercial clause. If that clause is wrong for a later use, drop the tileset and keep SPICE, PGDA, and the horizon chart. No other source choice needs a fork.

## Sources

- https://quickmap.lroc.im-ldi.com/ — public Lunar QuickMap
- https://www.actgate.com/examples/lroc-quickmap and https://www.actgate.com/products/quickmap — ACT product description
- https://www.hou.usra.edu/meetings/lunarpolar2022/pdf/5028.pdf — QuickMap polar tools, TerrainShadows
- https://lroc.im-ldi.com/about/terms — LROC terms and citation
- https://trek.nasa.gov/moon/ and https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=moon — Trek WMTS
- https://trek.nasa.gov/tiles/Moon/SP/WAC_POLE_ILL_PCT_SOUTH_100M/1.0.0/WMTSCapabilities.xml
- https://ssd.jpl.nasa.gov/horizons/ and https://ssd-api.jpl.nasa.gov/doc/horizons.html and https://ssd-api.jpl.nasa.gov/doc/index.php — Horizons and fair use
- https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/ — CSA outreach page
- https://pgda.gsfc.nasa.gov/products/69 https://pgda.gsfc.nasa.gov/products/78 https://pgda.gsfc.nasa.gov/products/81 https://pgda.gsfc.nasa.gov/products/90
- https://pds-geosciences.wustl.edu/missions/lro/diviner.htm
- https://naif.jpl.nasa.gov/naif/rules.html
- https://cesium.com/platform/cesium-ion/content/cesium-moon/
- https://cesium.com/platform/cesium-ion/pricing
- https://cesium.com/blog/2024/08/06/introducing-cesium-moon-terrain/
- https://psdi.astrogeology.usgs.gov/moon/standards/licensing/ — SPD-41a / CC0 guidance
- https://github.com/OpenSpace/OpenSpace
- https://github.com/vlas-sokolov/crater-viewer
- https://github.com/hh-hang/lunar-walk
- https://spacedata.swapniltamse.com/challenges/lunar-landing-site-navigator/ — unofficial dataset index, useful, not a NASA source
