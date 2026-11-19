// Copy the embedded pages (first-person view, region map) next to the built UI so the desktop app
// serves them from its own origin (shared localStorage with the shell, no server needed for them).
//
// D-20261118-pj-d99f: the desktop build also bundles Cesium and Three.js (from node_modules) and
// rewrites the CDN URLs in the COPIED html to local vendor/ paths, so the viewers load offline.
// web/*.html keeps its CDN URLs (GitHub Pages demo and engine API serve those as-is).
// The Pages demo build sets VITE_STATIC_DEMO=1 (deploy/build-demo.sh; same `=== "1"` test as
// vite.config.ts and src/api.ts) and keeps the CDN: no vendor files in that artifact.
//
// Paths are written as "./vendor/...": import-map addresses must start with "/", "./", "../" or be
// absolute URLs, otherwise the browser ignores the entry and `import "three"` fails.
import { cpSync, existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

const web = new URL("../../web/", import.meta.url);
const dist = new URL("../dist/", import.meta.url);
const nm = new URL("../node_modules/", import.meta.url);
const bundle = process.env.VITE_STATIC_DEMO !== "1";

const CESIUM_CDN = "https://cdn.jsdelivr.net/npm/cesium@1.121.1/Build/Cesium/";
const THREE_CDN = "https://cdn.jsdelivr.net/npm/three@0.160.0/";

/** Fail the build loudly when a file the viewers need is missing. */
function need(url) {
  if (!existsSync(url)) throw new Error(`copy-web: expected file not found: ${fileURLToPath(url)}`);
  return url;
}

for (const f of ["map.html", "map.js", "firstperson.html", "firstperson.js"]) {
  cpSync(need(new URL(f, web)), new URL(f, dist));
}
cpSync(need(new URL("assets/", web)), new URL("assets/", dist), { recursive: true });

if (bundle) {
  const rewrite = (file, from, to) => {
    const p = new URL(file, dist);
    const src = readFileSync(p, "utf8");
    if (!src.includes(from)) throw new Error(`copy-web: ${file}: expected ${from} not found`);
    writeFileSync(p, src.replaceAll(from, to));
  };
  rewrite("firstperson.html", CESIUM_CDN, "./vendor/cesium/");
  rewrite("map.html", THREE_CDN + "build/", "./vendor/three/build/");
  rewrite("map.html", THREE_CDN + "examples/jsm/", "./vendor/three/examples/jsm/");
  for (const file of ["map.html", "firstperson.html"]) {
    const left = readFileSync(new URL(file, dist), "utf8").match(/https?:\/\/cdn\.[^"'\s)]+/g);
    if (left) throw new Error(`copy-web: ${file} still references a CDN: ${left.join(", ")}`);
  }

  const cesium = new URL("cesium/Build/Cesium/", nm);
  for (const d of ["Cesium.js", "Widgets", "Workers", "Assets", "ThirdParty"]) {
    cpSync(need(new URL(d, cesium)), new URL(`vendor/cesium/${d}`, dist), { recursive: true });
  }
  need(new URL("Widgets/widgets.css", cesium));
  mkdirSync(new URL("vendor/three/build/", dist), { recursive: true });
  cpSync(need(new URL("three/build/three.module.js", nm)), new URL("vendor/three/build/three.module.js", dist));
  // Every three/addons/ module map.js imports must be listed here (the build fails if one is missing).
  for (const addon of ["controls/OrbitControls.js"]) {
    const to = new URL(`vendor/three/examples/jsm/${addon}`, dist);
    mkdirSync(new URL(".", to), { recursive: true });
    cpSync(need(new URL(`three/examples/jsm/${addon}`, nm)), to);
  }
  const addons = [...readFileSync(new URL("map.js", dist), "utf8").matchAll(/from\s+["']three\/addons\/([^"']+)["']/g)].map((m) => m[1]);
  for (const a of addons) need(new URL(`vendor/three/examples/jsm/${a}`, dist));
}
