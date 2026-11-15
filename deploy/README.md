# Browser demo on GitHub Pages

The public demo is the **desktop interface built for the browser**, with mocked data and no server:
https://pedrojonfg.github.io/clps/

## How it works

- `VITE_STATIC_DEMO=1` builds `desktop/` so the app reads JSON files in `demo/` instead of calling the API.
- `scripts/export_demo_data.py` writes those files by calling the API's own mock mode (`/mission-templates`, `/site?mock=1`, `/region-map` with the demo rows), so the browser demo shows exactly what local mock mode shows.
- The embedded pages (`web/map.html`, `web/firstperson.html`) get `?static=1` and read the same files.
- Every run returns the same mocked result; the UI says so in a banner. No masks, kernels or DEMs are published.

## Build and deploy

`.github/workflows/pages.yml` deploys on every push to `main` (or manually via *Run workflow*). It runs:

```bash
pip install -e ".[dev]"
npm ci --prefix desktop
deploy/build-demo.sh        # output: desktop/dist
```

Run the same commands to build locally. To preview with the same sub-path as Pages, serve a folder that contains `clps -> desktop/dist` and open `http://127.0.0.1:<port>/clps/`.

Repo setting: **Settings → Pages → Source: GitHub Actions**.

## Cesium ion token

The 3D first-person view needs a Cesium ion token in the browser. Nothing is injected at build time: visitors paste their own free token on the *3D first-person* screen (stored in their `localStorage`). Without a token the view falls back to the 2D horizon panorama.
