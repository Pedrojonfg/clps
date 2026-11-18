# Experiment: real imagery on the first-person relief

Kept for the record of `D-20261118-pj-f6b3` (decision: do not drape imagery; the surface stays procedural).

- `make_textures.py`: builds `a.png` and `b.png` from `data/imagery/WAC_ROI_SOUTH_SUMMER_100M.TIF` (LROC WAC south summer mosaic, NASA/GSFC/Arizona State University, not in git; download from the LROC PDS `EXTRAS/BROWSE/WAC_ROI/WAC_ROI_SOUTH_SUMMER/`, 829 MB).
- `client-albedo-uniform.patch`: the throw-away change to `web/firstperson.js` that reads `?albedo=<url>` (needs CORS) and mixes it into the procedural material. Written against the relief shader of PR 29; not meant to be merged.
- `compare-horizon.png`, `compare-ground.png`: Site01, 2027-02-10, three variants stacked top to bottom: procedural (today), (a) photo where lit and procedural elsewhere, (b) shadows filled and the photo's illumination envelope removed. Brightness is lifted by the same gamma on all three so the differences can be seen.
