# Redistribution terms for the relief data we would host

Research for D-20261118-pj-6fea (`redistribution_licence`), done 2026-11-18. Not legal advice.

## What we would host

| Files (data/dem) | Source page | Paper the source asks to cite |
|---|---|---|
| `LDEM_60S_{240,120}MPP_ADJ`, `LDEM_80S_{80,40,20}MPP_ADJ`, `LDEM_83S_10MPP_ADJ`, `LDSM_80S_80MPP_ADJ`, `LPSR_80S_20MPP_ADJ` (from `pgda.gsfc.nasa.gov/data/LOLA_20mpp/`) | PGDA product 90, "A New View of the Lunar South Pole from LOLA", https://pgda.gsfc.nasa.gov/products/90 (data DOI 10.60903/gsfcpgda-lola-spole) | Barker et al. 2023, PSJ 4, 183 |
| `ldem_87s_5mpp.tif` (`data/LOLA_5mpp/87S/`) | PGDA product 81, "South Pole LOLA DEM Mosaic", https://pgda.gsfc.nasa.gov/products/81 | Barker et al. 2021, PSS 203, 105119 |
| `Site{01,04,07,11}_final_adj_5mpp_surf.tif` (`data/LOLA_5mpp/<Site>/`) | PGDA product 78, "High-Resolution LOLA Topography for Lunar South Pole Sites", https://pgda.gsfc.nasa.gov/products/78, and its README https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/README | Barker et al. 2021, PSS 203, 105119 |

The relief tiles are a lossless re-packaging of these files (same float32 values, cut into 512 px tiles).

## What each source says

- **PGDA product 90** (LOLA_20mpp: LDEM/LDSM/LPSR): "Please cite this paper when using these products: Barker et al., 2023 Planet. Sci. J., 4, 183." The page has a "Data Usage Policy" heading with no text under it. No licence. Footer: "Reproduction Guidelines" links to NASA's media guidelines (http://www.nasa.gov/multimedia/guidelines/index.html). NASA Official/Curator: Erwan Mazarico.
- **PGDA product 81** (87S 5 m mosaic): "Please cite the following reference when using any of these products:" Barker et al. 2021. No licence or usage policy.
- **PGDA product 78** (site mosaics; the start and the end of the page were read; the middle, about 86k characters, is the per-site file listing and was not read): "Please cite the following reference when using any of the products described above:" Barker et al. 2021. No licence or usage policy.
- **LOLA_5mpp README** (read in full): describes the files (`*_surf.tif`: "surface height Z (meters) with interpolation filling empty pix"), the site numbering after Mazarico et al. 2011, and says "Please refer to the following paper for further details." Barker et al. 2021. No licence, no usage terms.
- **DataCite record** for 10.60903/gsfcpgda-lola-spole (api.datacite.org): publisher Goddard Space Flight Center, creator Barker, Michael; `rightsList` is **empty** (no licence registered).
- **PDS Geosciences Node FAQ** (https://pds-geosciences.wustl.edu/faq.html): "Data sets archived in the PDS are in the public domain." They are classified TSPA and "may be exported outside the United States as public open literature." "PDS data sets should be cited in the same way that published research is cited."
- **JPL policy for PDS material** (https://pds-geosciences.wustl.edu/jplcopyright.html): material "may be used by any person for any purpose without prior permission"; no endorsement by Caltech, JPL or NASA may be "claimed or implied".
- **NASA media usage guidelines** (https://www.nasa.gov/nasa-brand-center/images-and-media/): NASA material "generally are not subject to copyright in the United States"; "NASA should be acknowledged as the source of the material"; commercial use "must not explicitly or implicitly convey NASA's endorsement"; NASA insignia and logos are "protected by law"; third-party copyrighted material needs the holder's permission. The page covers images, audio, video and 3D media, not scientific data specifically.
- **NASA SMD Science Information Policy** (https://science.nasa.gov/researchers/science-data/science-information-policy/): open-sharing principles ("Research data and software are shared at the time of publication..."), but no data licence (no CC0, no "without restriction" wording).

## What is unclear / not verified

- **None of the PGDA products states a licence.** The PDS "public domain" sentence applies to data *archived in the PDS*. These `_ADJ` and 5 m products are on PGDA (a GSFC lab site), not in the PDS archive as far as we found, so that sentence does not cover them directly.
- That they are uncopyrighted US-government works (17 U.S.C. 105) is likely (NASA GSFC publisher, GSFC-hosted, NASA guidelines say "generally" not copyrighted) but **not verified**: the 2023 paper has non-NASA co-authors (e.g. MIT), and we did not confirm who produced the data or under which contract. US-government-work status also says nothing about rights outside the US.
- NASA's media guidelines are about media, not datasets; we apply their attribution and no-endorsement rules by analogy.
- We did not contact PGDA. The empty "Data Usage Policy" heading on product 90 suggests a policy may have been intended.

## Conclusion

**Only with attribution.** Every source we found points the same way: free use, cite the paper, credit NASA, no endorsement. Nothing restricts redistribution, and the public LOLA data is treated as public domain. Hosting the files unchanged (or losslessly tiled) in our store is very likely fine **if** we:

1. ship the attribution below with the app, the README and the store (a `relief/ATTRIBUTION.txt` beside the manifests);
2. cite Barker et al. 2023 (LOLA_20mpp models) and Barker et al. 2021 (5 m mosaics);
3. use no NASA logo or wording that suggests NASA endorses or runs the service;
4. say that the data are re-packaged (tiled), not modified.

Remaining risk: no explicit licence exists. Before the first public publish of relief, the cautious step is a short courtesy email to the PGDA curator (Erwan Mazarico, listed on the product pages) to confirm that redistribution with citation is OK. That needs the owner, so it has not been done.

## Attribution text (reuse in the app / README / store)

> Relief and elevation data: NASA Lunar Reconnaissance Orbiter, Lunar Orbiter Laser Altimeter (LOLA) team, NASA Goddard Space Flight Center Planetary Geodynamics Data Archive (pgda.gsfc.nasa.gov). Polar elevation models: Barker, M.K., et al. (2023), "A New View of the Lunar South Pole from the Lunar Orbiter Laser Altimeter (LOLA)", Planet. Sci. J. 4, 183, doi:10.3847/PSJ/acf3e1 (data doi:10.60903/gsfcpgda-lola-spole). 5 m mosaics: Barker, M.K., et al. (2021), "Improved LOLA Elevation Maps for South Pole Landing Sites: Error Estimates and Their Impact on Illumination Conditions", Planet. Space Sci. 203, 105119, doi:10.1016/j.pss.2020.105119. Re-packaged into tiles for this app, values unchanged. Not endorsed by NASA.
