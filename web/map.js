/**
 * S9 region score map — orbitable Moon with the score layer painted on it.
 * Decisions: D-4126 3D Moon, D-8acb infeasible black + in-query dots, D-7227 absolute RYG
 * (colours come from the API), D-834a interpolate overview / lift solid cell on focus,
 * D-85bf induced cells fainter than evaluated.
 *
 * Everything that is data lives in south-polar stereographic metres (the cap grid of
 * lunar_eval.horizon.polar_stereo_xy), so 1 km cells stay square at the pole.
 */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const MOON_R_KM = 1737.4;
const FOV_DEG = 40;
const ALT_MIN = 0.006; // ~10 km above the surface; closer only magnifies the 50 m/px relief
const ALT_MAX = 4;
const FIELD_ALPHA = 0.92;
const PLANNER_KEYS = [
  "start", "end", "step_h", "template_id",
  "max_night_h", "max_no_earth_h", "min_continuous_lit_h",
  "require_both", "sun_lit_percent", "earth_lit_percent", "bridge_h",
  "hazards_enabled", "local_search", "mock",
];

/** South-pole demo rows for POST /region-map (no prior search). */
const DEMO_ROWS = [
  { lat_deg: -89.46316, lon_deg: 222.51045, score: 1.05, feasible: true, companion_score: 1.05 },
  { lat_deg: -89.52, lon_deg: 205.0, score: 0.62, feasible: true, companion_score: 0.62 },
  { lat_deg: -89.48, lon_deg: 248.0, score: 0.22, feasible: true, companion_score: 0.22 },
  { lat_deg: -89.56, lon_deg: 218.0, score: 0, feasible: false, companion_score: 0.38 },
  { lat_deg: -89.5, lon_deg: 238.0, score: 0, feasible: false, companion_score: 0.12 },
];

const QUERY = new URLSearchParams(location.search);
/** ?static=1 → browser demo without API: demo rows only, from the exported region-map JSON. */
const STATIC = QUERY.get("static") === "1";
const EMBEDDED = window.parent !== window;

const $ = (id) => document.getElementById(id);
const statusEl = $("status");
const host = $("canvas-host");

if (!EMBEDDED && !STATIC) $("back-link").hidden = false;
if (EMBEDDED) {
  $("load-demo").hidden = true;
  $("empty-text").textContent = STATIC
    ? "Demo samples failed to load."
    : "Set the search rectangle above and press Run region search.";
}

function setStatus(msg, err = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("err", err);
}

/* ---------- geometry: stereographic plane <-> unit sphere ---------- */

/** lat/lon → south-polar stereographic (x, y) in Moon radii (x → 90°E, y → 0°E). */
function latLonToStereo(latDeg, lonDeg) {
  const rho = 2 * Math.tan(((90 + latDeg) * Math.PI) / 360);
  const lon = (lonDeg * Math.PI) / 180;
  return [rho * Math.sin(lon), rho * Math.cos(lon)];
}

/** Stereographic (x, y) in Moon radii → point on the sphere of radius r.
 *  Axes: +X = 0°E on the equator, +Y = north pole, −Z = 90°E (matches the equirect texture). */
function stereoToVec3(x, y, r = 1, out = new THREE.Vector3()) {
  const rho = Math.hypot(x, y);
  if (rho < 1e-12) return out.set(0, -r, 0);
  const c = 2 * Math.atan(rho / 2);
  const s = Math.sin(c) / rho;
  return out.set(r * s * y, -r * Math.cos(c), -r * s * x);
}

function vec3ToStereo(v) {
  const n = v.clone().normalize();
  const c = Math.acos(Math.max(-1, Math.min(1, -n.y)));
  const rho = 2 * Math.tan(c / 2);
  const h = Math.hypot(n.x, n.z);
  if (h < 1e-12) return [0, 0];
  return [(-n.z / h) * rho, (n.x / h) * rho];
}

/** Sphere patch over a stereographic rectangle; uv spans the rectangle (v up = +y). */
function stereoPatchGeometry(x0, x1, y0, y1, segs, r) {
  const nx = segs;
  const ny = segs;
  const pos = new Float32Array((nx + 1) * (ny + 1) * 3);
  const uv = new Float32Array((nx + 1) * (ny + 1) * 2);
  const v = new THREE.Vector3();
  let p = 0;
  let q = 0;
  for (let j = 0; j <= ny; j++) {
    for (let i = 0; i <= nx; i++) {
      const u = i / nx;
      const w = j / ny;
      stereoToVec3(x0 + u * (x1 - x0), y0 + w * (y1 - y0), r, v);
      pos[p++] = v.x; pos[p++] = v.y; pos[p++] = v.z;
      uv[q++] = u; uv[q++] = w;
    }
  }
  const idx = [];
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const a = j * (nx + 1) + i;
      const b = a + 1;
      const c = a + nx + 1;
      const d = c + 1;
      idx.push(a, b, d, a, d, c);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g;
}

/** Orthonormal frame at a stereographic point: columns = (+x, +y, outward). */
function frameAt(x, y, r) {
  const h = 1e-5;
  const p = stereoToVec3(x, y, r);
  const ex = stereoToVec3(x + h, y, r).sub(p).normalize();
  const n = p.clone().normalize();
  const ey = new THREE.Vector3().crossVectors(n, ex).normalize();
  const m = new THREE.Matrix4().makeBasis(ex, ey, n);
  m.setPosition(p);
  return m;
}

/* ---------- scene ---------- */

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x111418);
host.appendChild(renderer.domElement);
const canvas = renderer.domElement;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(FOV_DEG, 1, 0.01, 10);
// Up = 0°E on the equator: the south pole sits mid-control-sphere, so dragging there pans
// like a map (lon 0° up, 90°E right) instead of spinning on OrbitControls' pole singularity.
camera.up.set(1, 0, 0);
const view = { dir: new THREE.Vector3(0.0001, -1, 0).normalize(), alt: 0.9, fly: null };
camera.position.copy(view.dir).multiplyScalar(1 + view.alt);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.12;
controls.enableZoom = false; // zoom is altitude above the surface, handled below
controls.enablePan = false;
controls.target.set(0, 0, 0);

const texLoader = new THREE.TextureLoader();
function loadTex(url) {
  const t = texLoader.load(url);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return t;
}

// Unlit: the textures already carry relief shading, and a terminator would hide scores.
const moon = new THREE.Mesh(
  new THREE.SphereGeometry(1, 128, 96),
  new THREE.MeshBasicMaterial({ map: loadTex("assets/moon.jpg"), color: 0xb4b4b4 }),
);
scene.add(moon);

/** Radial alpha so a polar patch blends into the layer below instead of ending on a seam. */
function edgeFadeTexture() {
  const n = 256;
  const c = document.createElement("canvas");
  c.width = c.height = n;
  const ctx = c.getContext("2d");
  const img = ctx.createImageData(n, n);
  for (let j = 0; j < n; j++) {
    for (let i = 0; i < n; i++) {
      const r = Math.hypot(i - (n - 1) / 2, j - (n - 1) / 2) / ((n - 1) / 2);
      const a = 1 - Math.min(1, Math.max(0, (r - 0.86) / 0.12));
      const v = Math.round(255 * a * a * (3 - 2 * a));
      const k = 4 * (j * n + i);
      img.data[k] = img.data[k + 1] = img.data[k + 2] = v;
      img.data[k + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return new THREE.CanvasTexture(c);
}
const fadeTex = edgeFadeTexture();

function addPolarPatch(url, halfKm, radius, order) {
  const half = halfKm / MOON_R_KM;
  const mesh = new THREE.Mesh(
    stereoPatchGeometry(-half, half, -half, half, 96, radius),
    new THREE.MeshBasicMaterial({
      map: loadTex(url),
      alphaMap: fadeTex,
      color: 0xb4b4b4,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    }),
  );
  mesh.renderOrder = order;
  scene.add(mesh);
}
addPolarPatch("assets/southpole_80s.jpg", 304, 1.00002, 1);
addPolarPatch("assets/southpole_87s.jpg", 100, 1.00004, 2);

const FIELD_R = 1.00007;
const MARK_R = 1.0001;
const overlay = new THREE.Group();
scene.add(overlay);

/* ---------- data state ---------- */

/** @type {{samples: any[], cell: number, hash: Map<string, number[]>, best: any|null}} */
let data = { samples: [], cell: 1 / MOON_R_KM, hash: new Map(), best: null };
let hovered = null;
let selected = null;
const tiles = { hover: null, selected: null };

function estimateCell(samples) {
  // Median nearest-neighbour spacing; the cap grid is 1 km, demo rows are sparser.
  const fallback = 1 / MOON_R_KM;
  if (samples.length < 2) return fallback;
  const pick = samples.length > 400 ? samples.filter((_, i) => i % Math.ceil(samples.length / 400) === 0) : samples;
  const nn = pick.map((a) => {
    let best = Infinity;
    for (const b of samples) {
      if (a === b) continue;
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      if (d > 1e-9 && d < best) best = d;
    }
    return best;
  }).filter(Number.isFinite).sort((a, b) => a - b);
  if (!nn.length) return fallback;
  return Math.min(Math.max(nn[Math.floor(nn.length / 2)], 0.2 / MOON_R_KM), 20 / MOON_R_KM);
}

function buildHash(samples, cell) {
  const hash = new Map();
  samples.forEach((s, i) => {
    const k = `${Math.floor(s.x / cell)},${Math.floor(s.y / cell)}`;
    if (!hash.has(k)) hash.set(k, []);
    hash.get(k).push(i);
  });
  return hash;
}

function neighbours(x, y, reach) {
  const { cell, hash } = data;
  const ix = Math.floor(x / cell);
  const iy = Math.floor(y / cell);
  const out = [];
  for (let dy = -reach; dy <= reach; dy++) {
    for (let dx = -reach; dx <= reach; dx++) {
      const b = hash.get(`${ix + dx},${iy + dy}`);
      if (b) out.push(...b);
    }
  }
  return out;
}

function nearestSample(x, y, maxDist) {
  let best = null;
  let bestD = maxDist;
  for (const i of neighbours(x, y, Math.max(1, Math.ceil(maxDist / data.cell)))) {
    const s = data.samples[i];
    const d = Math.hypot(s.x - x, s.y - y);
    if (d < bestD) {
      bestD = d;
      best = s;
    }
  }
  return best;
}

/* ---------- overview field (D-834a interpolate; D-8acb black; D-85bf induced alpha) ---------- */

function buildField() {
  const { samples, cell } = data;
  const pad = 2.5 * cell;
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const s of samples) {
    x0 = Math.min(x0, s.x); x1 = Math.max(x1, s.x);
    y0 = Math.min(y0, s.y); y1 = Math.max(y1, s.y);
  }
  x0 -= pad; x1 += pad; y0 -= pad; y1 += pad;
  const cellsX = (x1 - x0) / cell;
  const cellsY = (y1 - y0) / cell;
  const ppc = Math.max(2, Math.min(10, Math.floor(1536 / Math.max(cellsX, cellsY))));
  const w = Math.max(2, Math.round(cellsX * ppc));
  const h = Math.max(2, Math.round(cellsY * ppc));

  // Straight RGBA (a 2D canvas would premultiply and band the faint edges).
  const px = new Uint8Array(w * h * 4);
  const reachD = 2.2 * cell;
  const soft = (0.2 * cell) ** 2;

  for (let j = 0; j < h; j++) {
    const y = y0 + ((j + 0.5) / h) * (y1 - y0); // DataTexture row 0 = v 0 = y0
    for (let i = 0; i < w; i++) {
      const x = x0 + ((i + 0.5) / w) * (x1 - x0);
      let dMin = Infinity;
      let near = null;
      let wSum = 0, r = 0, g = 0, b = 0, aSum = 0, aW = 0;
      for (const si of neighbours(x, y, 3)) {
        const s = samples[si];
        const d2 = (s.x - x) ** 2 + (s.y - y) ** 2;
        const d = Math.sqrt(d2);
        if (d < dMin) {
          dMin = d;
          near = s;
        }
        if (d >= reachD) continue;
        const wgt = (1 - d / reachD) ** 2 / (d2 + soft);
        aSum += wgt * s.rgba[3];
        aW += wgt;
        if (!s.feasible) continue;
        wSum += wgt;
        r += wgt * s.rgba[0]; g += wgt * s.rgba[1]; b += wgt * s.rgba[2];
      }
      if (!near || !aW) continue;
      // Coverage: solid inside the cell, gone 1.8 cells from the closest sample.
      const t = Math.min(1, Math.max(0, (1.8 * cell - dMin) / (1.1 * cell)));
      const alpha = FIELD_ALPHA * (aSum / aW) * t * t * (3 - 2 * t);
      const k = 4 * (j * w + i);
      if (near.feasible && wSum > 0) {
        // The API ramp always has max(r, g) = 255; renormalise so blends stay on the ramp.
        const m = Math.max(r, g, 1e-9);
        px[k] = Math.round((255 * r) / m);
        px[k + 1] = Math.round((255 * g) / m);
        px[k + 2] = Math.round((255 * b) / m);
      } // else infeasible: stays black (D-8acb)
      px[k + 3] = Math.round(255 * alpha);
    }
  }

  const tex = new THREE.DataTexture(px, w, h, THREE.RGBAFormat);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.magFilter = tex.minFilter = THREE.LinearFilter;
  tex.needsUpdate = true;
  const spanKm = Math.max(x1 - x0, y1 - y0) * MOON_R_KM;
  const mesh = new THREE.Mesh(
    stereoPatchGeometry(x0, x1, y0, y1, spanKm > 120 ? 128 : 48, FIELD_R),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, side: THREE.DoubleSide }),
  );
  mesh.renderOrder = 3;
  overlay.add(mesh);
}

/** D-8acb: white dot on evaluated infeasible cells, size = badness relative to this query. */
function buildInfeasibleDots() {
  const list = data.samples.filter((s) => !s.feasible && !s.induced && s.marker_t != null);
  if (!list.length) return;
  const mesh = new THREE.InstancedMesh(
    new THREE.CircleGeometry(1, 20),
    new THREE.MeshBasicMaterial({ color: 0xf6f7f9, side: THREE.DoubleSide, depthWrite: false, transparent: true }),
    list.length,
  );
  const scale = new THREE.Matrix4();
  list.forEach((s, i) => {
    // marker_t is 1 for the best companion score among infeasibles: bigger dot = worse.
    const badness = 1 - Math.min(1, Math.max(0, Number(s.marker_t)));
    const rad = data.cell * (0.1 + 0.24 * badness);
    mesh.setMatrixAt(i, frameAt(s.x, s.y, MARK_R).multiply(scale.makeScale(rad, rad, 1)));
  });
  mesh.renderOrder = 4;
  overlay.add(mesh);
}

function clearOverlay() {
  for (const c of [...overlay.children]) {
    overlay.remove(c);
    c.geometry?.dispose();
    for (const m of [].concat(c.material ?? [])) {
      m.map?.dispose();
      m.dispose();
    }
  }
  tiles.hover = tiles.selected = null;
  hovered = selected = null;
}

/* ---------- focus: lifted solid cell (D-834a) ---------- */

function makeTile(sample, strong) {
  const { cell } = data;
  const side = cell * 0.94;
  const lift = cell * (strong ? 0.7 : 0.45);
  const color = new THREE.Color().setRGB(sample.rgba[0] / 255, sample.rgba[1] / 255, sample.rgba[2] / 255, THREE.SRGBColorSpace);
  const top = new THREE.MeshBasicMaterial({ color });
  const wall = new THREE.MeshBasicMaterial({ color: color.clone().multiplyScalar(0.55) });
  const geo = new THREE.BoxGeometry(side, side, lift);
  const box = new THREE.Mesh(geo, [wall, wall, wall, wall, top, top]);
  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geo),
    new THREE.LineBasicMaterial({ color: 0xf6f7f9 }),
  );
  // Offset ground shadow: from straight above it is what makes the cell read as lifted.
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(side * 1.12, side * 1.12),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.5, depthWrite: false }),
  );
  shadow.position.set(side * 0.16, -side * 0.16, -lift / 2);
  const group = new THREE.Group();
  group.add(shadow, box, edges);
  group.applyMatrix4(frameAt(sample.x, sample.y, MARK_R + lift / 2));
  group.renderOrder = 5;
  overlay.add(group);
  return group;
}

function dropTile(slot) {
  const g = tiles[slot];
  if (!g) return;
  overlay.remove(g);
  g.traverse((o) => {
    o.geometry?.dispose();
    for (const m of [].concat(o.material ?? [])) m.dispose();
  });
  tiles[slot] = null;
}

function fmtLat(v) { return `${Math.abs(v).toFixed(4)}° ${v < 0 ? "S" : "N"}`; }
function fmtLon(v) { return `${(((v % 360) + 360) % 360).toFixed(4)}° E`; }

function showReadout(sample, pinned) {
  const box = $("readout");
  if (!sample) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  $("readout-chip").style.background = `rgb(${sample.rgba[0]},${sample.rgba[1]},${sample.rgba[2]})`;
  $("readout-title").textContent = sample.induced
    ? "Induced cell"
    : sample.is_best ? "Best evaluated cell" : "Evaluated cell";
  $("readout-lat").textContent = fmtLat(sample.lat_deg);
  $("readout-lon").textContent = fmtLon(sample.lon_deg);
  $("readout-score").textContent = sample.induced
    ? "not scored"
    : sample.feasible ? Number(sample.score).toFixed(3) : "0 · infeasible";
  $("readout-note").textContent = sample.induced
    ? "Shown from the nearest evaluated cell to mark where the search moved."
    : !sample.feasible && sample.marker_t != null
      ? `Relative badness in this query: ${Math.round(100 * (1 - sample.marker_t))} % (dot size).`
      : pinned ? "" : "Click to pin this cell.";
  $("readout-note").hidden = !$("readout-note").textContent;
  $("readout-actions").hidden = !pinned;
}

function setHovered(sample) {
  if (sample === hovered) return;
  hovered = sample;
  dropTile("hover");
  if (sample && sample !== selected) tiles.hover = makeTile(sample, false);
  canvas.classList.toggle("over-cell", Boolean(sample));
  const shown = sample ?? selected;
  showReadout(shown, Boolean(shown) && shown === selected);
}

function setSelected(sample) {
  selected = sample;
  dropTile("selected");
  dropTile("hover");
  if (sample) tiles.selected = makeTile(sample, true);
  showReadout(sample, Boolean(sample));
}

/* ---------- picking ---------- */

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const unitSphere = new THREE.Sphere(new THREE.Vector3(), 1);
const hit = new THREE.Vector3();

function pickSample(clientX, clientY) {
  if (!data.samples.length) return null;
  const r = canvas.getBoundingClientRect();
  pointer.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
  raycaster.setFromCamera(pointer, camera);
  if (!raycaster.ray.intersectSphere(unitSphere, hit)) return null;
  const [x, y] = vec3ToStereo(hit);
  // At least ~9 px on screen so sparse cells stay reachable when zoomed out.
  const pxWorld = (2 * view.alt * Math.tan((FOV_DEG * Math.PI) / 360)) / r.height;
  return nearestSample(x, y, Math.max(0.72 * data.cell, 9 * pxWorld));
}

let downAt = null;
canvas.addEventListener("pointerdown", (ev) => {
  downAt = [ev.clientX, ev.clientY];
  canvas.classList.add("dragging");
  view.fly = null;
});
window.addEventListener("pointerup", () => canvas.classList.remove("dragging"));
canvas.addEventListener("pointermove", (ev) => {
  if (ev.buttons) return;
  setHovered(pickSample(ev.clientX, ev.clientY));
});
canvas.addEventListener("pointerleave", () => setHovered(null));
canvas.addEventListener("click", (ev) => {
  if (downAt && Math.hypot(ev.clientX - downAt[0], ev.clientY - downAt[1]) > 4) return; // was a drag
  setSelected(pickSample(ev.clientX, ev.clientY));
});

/* ---------- camera ---------- */

function clampAlt(a) { return Math.min(ALT_MAX, Math.max(ALT_MIN, a)); }

canvas.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  view.fly = null;
  view.alt = clampAlt(view.alt * Math.exp(ev.deltaY * 0.0015));
}, { passive: false });

function flyTo(dir, alt) {
  view.fly = {
    t0: performance.now(),
    fromDir: camera.position.clone().normalize(),
    toDir: dir.clone().normalize(),
    fromAlt: view.alt,
    toAlt: clampAlt(alt),
  };
}

function fitData(animate = true) {
  if (!data.samples.length) return;
  const c = new THREE.Vector3();
  const pts = data.samples.map((s) => stereoToVec3(s.x, s.y));
  pts.forEach((p) => c.add(p));
  c.normalize();
  let ang = 0;
  for (const p of pts) ang = Math.max(ang, c.angleTo(p));
  const span = 2 * Math.max(ang + 2.5 * data.cell, 4 * data.cell);
  const aspect = Math.min(1, camera.aspect);
  const alt = (span * 1.35) / (2 * Math.tan((FOV_DEG * Math.PI) / 360) * aspect);
  if (animate) flyTo(c, alt);
  else {
    view.alt = clampAlt(alt);
    camera.position.copy(c).multiplyScalar(1 + view.alt);
  }
}

$("zoom-in").addEventListener("click", () => flyTo(camera.position, view.alt * 0.6));
$("zoom-out").addEventListener("click", () => flyTo(camera.position, view.alt / 0.6));
$("fit-data").addEventListener("click", () => fitData());
$("whole-moon").addEventListener("click", () => flyTo(camera.position, 2.6));

const bestPin = $("best-pin");
const tmp = new THREE.Vector3();

function updateBestPin() {
  const b = data.best;
  if (!b) {
    bestPin.hidden = true;
    return;
  }
  stereoToVec3(b.x, b.y, 1, tmp);
  const facing = tmp.dot(camera.position) > 1; // on the visible side of the limb
  tmp.project(camera);
  bestPin.hidden = !facing || Math.abs(tmp.x) > 1 || Math.abs(tmp.y) > 1;
  if (bestPin.hidden) return;
  bestPin.style.left = `${((tmp.x + 1) / 2) * host.clientWidth}px`;
  bestPin.style.top = `${((1 - tmp.y) / 2) * host.clientHeight}px`;
}

function resize() {
  const w = host.clientWidth;
  const h = host.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

function tick(now) {
  requestAnimationFrame(tick);
  if (view.fly) {
    const f = view.fly;
    const u = Math.min(1, (now - f.t0) / 700);
    const e = u * u * (3 - 2 * u);
    const q = new THREE.Quaternion().setFromUnitVectors(f.fromDir, f.toDir);
    const dir = f.fromDir.clone().applyQuaternion(new THREE.Quaternion().slerp(q, e));
    view.alt = Math.exp(Math.log(f.fromAlt) + (Math.log(f.toAlt) - Math.log(f.fromAlt)) * e);
    camera.position.copy(dir).multiplyScalar(1 + view.alt);
    if (u >= 1) view.fly = null;
  }
  // Keep the surface under the cursor while dragging, at any zoom.
  controls.rotateSpeed = Math.min(1, (view.alt * 2 * Math.tan((FOV_DEG * Math.PI) / 360)) / (2 * Math.PI));
  controls.update();
  camera.position.setLength(1 + view.alt);
  camera.near = Math.max(view.alt * 0.2, 1e-4);
  camera.far = view.alt + 2.5;
  camera.updateProjectionMatrix();
  camera.lookAt(0, 0, 0);
  renderer.render(scene, camera);
  updateBestPin();
}

/* ---------- loading ---------- */

function showSamples(payload, label) {
  clearOverlay();
  setSelected(null);
  const samples = (payload.samples || []).map((s) => {
    const [x, y] = latLonToStereo(s.lat_deg, s.lon_deg);
    return { ...s, x, y };
  });
  const cell = estimateCell(samples);
  data = { samples, cell, hash: buildHash(samples, cell), best: samples.find((s) => s.is_best) ?? null };

  const ceiling = Number(payload.score_ceiling ?? 1.4);
  $("ramp-mid").textContent = (ceiling / 2).toFixed(1);
  $("ramp-max").textContent = `${ceiling.toFixed(1)}+`;
  $("legend-induced").hidden = !(payload.n_induced > 0);
  $("empty").hidden = samples.length > 0;
  if (data.best) $("best-pin-label").textContent = `Best ${Number(data.best.score).toFixed(2)}`;

  if (!samples.length) {
    setStatus("No cells in this result");
    return;
  }
  buildField();
  buildInfeasibleDots();
  fitData(true);

  const n = payload.n_evaluated ?? samples.length;
  const ni = payload.n_induced ?? 0;
  setStatus(
    `${label ? label + " · " : ""}${n} evaluated${ni ? ` + ${ni} induced` : ""} · ` +
      (payload.search_partial ? "partial search" : "full coverage"),
  );
}

async function postRegionMap(body) {
  if (STATIC) {
    // ?moon=1 → the exported whole-Moon mock search instead of the five hand-placed rows.
    const res = await fetch(QUERY.get("moon") === "1" ? "demo/region-map-moon-mock.json" : "demo/region-map-demo.json");
    if (!res.ok) throw new Error(`demo data HTTP ${res.status}`);
    return res.json();
  }
  const res = await fetch("/region-map", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const body2 = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = body2.detail;
    throw new Error(d?.message || (typeof d === "string" ? d : res.statusText));
  }
  return body2;
}

async function loadDemo() {
  setStatus("Loading demo samples…");
  try {
    showSamples(
      await postRegionMap({ rows: DEMO_ROWS, search_partial: true, best: DEMO_ROWS[0] }),
      QUERY.get("moon") === "1" ? "MOCK · Whole Moon total coverage" : "Demo samples",
    );
  } catch (e) {
    $("empty").hidden = false;
    setStatus("Region map failed: " + e.message, true);
  }
}

/** Last search handed over by the planner / desktop shell (same origin, localStorage). */
async function loadStoredSearch() {
  let raw = null;
  try {
    raw = localStorage.getItem("clps:regionMapRequest");
  } catch (_) {
    /* storage blocked */
  }
  if (!raw) {
    $("empty").hidden = false;
    setStatus("No search results yet");
    return;
  }
  try {
    const { label, ...body } = JSON.parse(raw);
    setStatus("Painting search results…");
    showSamples(await postRegionMap(body), label);
  } catch (e) {
    $("empty").hidden = false;
    setStatus("Could not paint the stored search: " + e.message, true);
  }
}

function plannerQuery(sample) {
  const q = new URLSearchParams();
  for (const k of PLANNER_KEYS) if (QUERY.has(k)) q.set(k, QUERY.get(k));
  q.set("lat", String(sample.lat_deg));
  q.set("lon", String(sample.lon_deg));
  return q;
}

function openSite(target) {
  if (!selected) return;
  if (EMBEDDED) {
    // The desktop shell owns navigation; never load another page inside its frame.
    window.parent.postMessage(
      { type: "lunar-eval:open-site", target, lat: selected.lat_deg, lon: selected.lon_deg },
      location.origin,
    );
    return;
  }
  const q = plannerQuery(selected);
  location.href = (target === "firstperson" ? "firstperson.html?" : "/?") + q.toString();
}

$("open-planner").addEventListener("click", () => openSite("planner"));
$("open-firstperson").addEventListener("click", () => openSite("firstperson"));
$("load-demo").addEventListener("click", () => loadDemo());

resize();
new ResizeObserver(resize).observe(host);
requestAnimationFrame(tick);

if (STATIC || QUERY.get("demo") === "1") loadDemo();
else loadStoredSearch();
