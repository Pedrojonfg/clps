/**
 * S9 region score map — orbitable Moon with the score layer painted on it.
 * Decisions: D-4126 3D Moon, D-7227 absolute RYG (colours come from the API), D-834a lift a
 * solid cell on focus, D-85bf paint what the search evaluated.
 * 2026-11-16 — D-2325: evaluated cells are markers with a minimum on-screen size, infeasibles
 * are violet (not black), the pointer snaps to the nearest evaluated cell, best-cells list.
 * D-1df2: a distance-faded estimate layer fills between evaluated cells by
 * four-quadrant inverse distance; it replaces drawing the API's four-neighbour induced copies.
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
const CELL = 1 / MOON_R_KM; // the cap grid is 1 km
const ESTIMATE_ALPHA = 0.6; // at an evaluated cell; falls to 0 at reach (D-1df2)
const PICK_PX = 24; // pointer snaps to the nearest evaluated cell within this radius (D-2325)
const TOP_N = 8;
const INFEASIBLE_RGB = [176, 131, 240];
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

/** samples = evaluated cells only; spacing = their typical separation (Moon radii). */
let data = { samples: [], spacing: CELL, hash: new Map(), best: null, ceiling: 1.4, estimate: null };
let hovered = null;
let selected = null;
let markers = null;
const tiles = { hover: null, selected: null };

function estimateSpacing(samples) {
  // Median nearest-neighbour spacing of evaluated cells.
  if (samples.length < 2) return CELL;
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
  if (!nn.length) return CELL;
  return Math.min(Math.max(nn[Math.floor(nn.length / 2)], 0.2 * CELL), 60 * CELL);
}

/** Integer grid key (string keys made the estimate pass several times slower). */
function hashKey(ix, iy) {
  return (ix + 32768) * 65536 + (iy + 32768);
}

function buildHash(samples, cell) {
  const hash = new Map();
  samples.forEach((s, i) => {
    const k = hashKey(Math.floor(s.x / cell), Math.floor(s.y / cell));
    if (!hash.has(k)) hash.set(k, []);
    hash.get(k).push(i);
  });
  return hash;
}

function neighbours(x, y, reach) {
  const { spacing, hash } = data;
  const ix = Math.floor(x / spacing);
  const iy = Math.floor(y / spacing);
  const out = [];
  for (let dy = -reach; dy <= reach; dy++) {
    for (let dx = -reach; dx <= reach; dx++) {
      const b = hash.get(hashKey(ix + dx, iy + dy));
      if (b) for (const i of b) out.push(i);
    }
  }
  return out;
}

function nearestSample(x, y, maxDist) {
  let best = null;
  let bestD = maxDist;
  for (const i of neighbours(x, y, Math.min(5, Math.ceil(maxDist / data.spacing) + 1))) {
    const s = data.samples[i];
    const d = Math.hypot(s.x - x, s.y - y);
    if (d < bestD) {
      bestD = d;
      best = s;
    }
  }
  return best;
}

/** Same absolute ramp as lunar_eval.region_map.feasible_score_to_rgb (D-7227). */
function scoreRgb(score) {
  const c = data.ceiling;
  const mid = c / 2;
  const v = Math.max(0, Math.min(c, score));
  return v <= mid ? [255, Math.round((255 * v) / mid), 0] : [Math.round(255 * (1 - (v - mid) / (c - mid))), 255, 0];
}

/* ---------- view scale ---------- */

function pxWorld() {
  // Moon radii per CSS pixel at the surface under the camera.
  return (2 * view.alt * Math.tan((FOV_DEG * Math.PI) / 360)) / Math.max(1, host.clientHeight);
}

/** Marker diameter in CSS px: never below a readable minimum, true cell size once larger (D-2325). */
function markerPx() {
  const w = pxWorld();
  const spacingPx = data.spacing / w;
  const minPx = Math.min(11, Math.max(7, 0.9 * spacingPx));
  return Math.max(minPx, Math.min(0.9 * spacingPx, (0.94 * CELL) / w));
}

/* ---------- evaluated cells: always-visible markers (D-2325) ---------- */

const MARKER_VERT = `
  attribute vec3 aColor;
  attribute float aKind;
  attribute float aBad;
  uniform float uSize;
  varying vec3 vColor;
  varying float vKind;
  varying float vBad;
  void main() {
    vColor = aColor;
    vKind = aKind;
    vBad = aBad;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = uSize;
  }
`;
const MARKER_FRAG = `
  const float MARKER_ALPHA = 0.85; // D-a3f1: let the relief show through
  uniform float uSize;
  varying vec3 vColor;
  varying float vKind;
  varying float vBad;
  void main() {
    vec2 p = gl_PointCoord * 2.0 - 1.0;
    float r = length(p);
    float px = 2.0 / uSize;
    if (r > 1.0) discard;
    float edge = smoothstep(1.0, 1.0 - 0.8 * px, r);
    float ring = smoothstep(1.0 - 1.9 * px, 1.0 - 1.0 * px, r);
    vec3 col = vColor;
    if (vKind > 0.5) {
      // Infeasible: violet with a cross; inner dot grows with badness within this query.
      float cross = min(abs(p.x - p.y), abs(p.x + p.y)) * 0.7071;
      float arm = (1.0 - smoothstep(0.55 * px, 1.1 * px, cross)) * step(r, 0.6) * step(12.0, uSize);
      col = mix(col, vec3(0.07, 0.08, 0.1), arm);
      float dot = step(26.0, uSize) * (1.0 - smoothstep(0.0, px, r - (0.1 + 0.22 * vBad)));
      col = mix(col, vec3(0.96, 0.97, 0.98), dot);
    }
    col = mix(col, vec3(0.07, 0.08, 0.1), ring);
    gl_FragColor = vec4(col, edge * MARKER_ALPHA);
  }
`;

function buildMarkers() {
  // Draw order: infeasible first, then feasible by ascending score, so the best sit on top.
  const order = [...data.samples].sort((a, b) =>
    a.feasible !== b.feasible ? (a.feasible ? 1 : -1) : a.score - b.score);
  const n = order.length;
  const pos = new Float32Array(n * 3);
  const col = new Float32Array(n * 3);
  const kind = new Float32Array(n);
  const bad = new Float32Array(n);
  const v = new THREE.Vector3();
  order.forEach((s, i) => {
    stereoToVec3(s.x, s.y, MARK_R, v);
    pos.set([v.x, v.y, v.z], 3 * i);
    col.set([s.rgba[0] / 255, s.rgba[1] / 255, s.rgba[2] / 255], 3 * i);
    kind[i] = s.feasible ? 0 : 1;
    bad[i] = s.marker_t == null ? 0 : 1 - Math.min(1, Math.max(0, Number(s.marker_t)));
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  g.setAttribute("aColor", new THREE.BufferAttribute(col, 3));
  g.setAttribute("aKind", new THREE.BufferAttribute(kind, 1));
  g.setAttribute("aBad", new THREE.BufferAttribute(bad, 1));
  markers = new THREE.Points(g, new THREE.ShaderMaterial({
    uniforms: { uSize: { value: 8 } },
    vertexShader: MARKER_VERT,
    fragmentShader: MARKER_FRAG,
    transparent: true,
    depthWrite: false,
  }));
  markers.renderOrder = 4;
  markers.frustumCulled = false;
  overlay.add(markers);
}

/* ---------- estimate layer between evaluated cells (D-1df2) ---------- */

/**
 * Four-quadrant inverse distance (the rule of D-affb): the nearest evaluated cell in each
 * quadrant, weights 1/d². Returns null beyond `reach` of every evaluated cell.
 */
function estimateAt(x, y, reach) {
  const near = [null, null, null, null];
  const nd = [Infinity, Infinity, Infinity, Infinity];
  let dMin = Infinity;
  for (const i of neighbours(x, y, Math.ceil(reach / data.spacing))) {
    const s = data.samples[i];
    const dx = s.x - x;
    const dy = s.y - y;
    const d = Math.hypot(dx, dy);
    if (d > reach) continue;
    const q = (dx >= 0 ? 1 : 0) + (dy >= 0 ? 2 : 0);
    if (d < nd[q]) {
      nd[q] = d;
      near[q] = s;
    }
    if (d < dMin) dMin = d;
  }
  if (!Number.isFinite(dMin)) return null;
  const soft = (0.05 * data.spacing) ** 2;
  let w = 0, wf = 0, sc = 0, n = 0;
  for (let q = 0; q < 4; q++) {
    const s = near[q];
    if (!s) continue;
    n += 1;
    const wq = 1 / (nd[q] * nd[q] + soft);
    w += wq;
    if (s.feasible) {
      wf += wq;
      sc += wq * s.score;
    }
  }
  const pFeasible = wf / w;
  return { dMin, n, pFeasible, feasible: pFeasible >= 0.5, score: wf > 0 ? sc / wf : 0 };
}

function buildEstimate() {
  const { samples, spacing } = data;
  const reach = Math.min(60 * CELL, Math.max(3 * CELL, 3 * spacing));
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const s of samples) {
    x0 = Math.min(x0, s.x); x1 = Math.max(x1, s.x);
    y0 = Math.min(y0, s.y); y1 = Math.max(y1, s.y);
  }
  x0 -= reach; x1 += reach; y0 -= reach; y1 += reach;
  const px = Math.max(spacing / 4, Math.max(x1 - x0, y1 - y0) / 420);
  const w = Math.max(2, Math.round((x1 - x0) / px));
  const h = Math.max(2, Math.round((y1 - y0) / px));

  // Straight RGBA (a 2D canvas would premultiply and band the faint edges).
  const tex = new Uint8Array(w * h * 4);
  for (let j = 0; j < h; j++) {
    const y = y0 + ((j + 0.5) / h) * (y1 - y0); // DataTexture row 0 = v 0 = y0
    for (let i = 0; i < w; i++) {
      const e = estimateAt(x0 + ((i + 0.5) / w) * (x1 - x0), y, reach);
      if (!e) continue;
      const rgb = e.feasible ? scoreRgb(e.score) : INFEASIBLE_RGB;
      const t = Math.max(0, 1 - e.dMin / reach);
      const k = 4 * (j * w + i);
      tex[k] = rgb[0]; tex[k + 1] = rgb[1]; tex[k + 2] = rgb[2];
      // Quadratic fade: already weak at half reach, so far-from-data colour never looks solid.
      tex[k + 3] = Math.round(255 * ESTIMATE_ALPHA * (e.feasible ? 1 : 0.6) * t * t);
    }
  }
  const map = new THREE.DataTexture(tex, w, h, THREE.RGBAFormat);
  map.colorSpace = THREE.SRGBColorSpace;
  map.magFilter = map.minFilter = THREE.LinearFilter;
  map.needsUpdate = true;
  const spanKm = Math.max(x1 - x0, y1 - y0) * MOON_R_KM;
  const mesh = new THREE.Mesh(
    stereoPatchGeometry(x0, x1, y0, y1, spanKm > 120 ? 128 : 48, FIELD_R),
    new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, side: THREE.DoubleSide }),
  );
  mesh.renderOrder = 3;
  mesh.visible = !evaluatedOnly();
  overlay.add(mesh);
  data.estimate = { mesh, reach };
}

function evaluatedOnly() {
  return $("evaluated-only").checked;
}

function clearOverlay() {
  for (const c of [...overlay.children]) {
    overlay.remove(c);
    c.traverse?.((o) => {
      o.geometry?.dispose();
      for (const m of [].concat(o.material ?? [])) {
        m.map?.dispose();
        m.dispose();
      }
    });
  }
  markers = null;
  tiles.hover = tiles.selected = null;
  hovered = selected = null;
}

/* ---------- focus: lifted solid cell (D-834a), sized with the markers ---------- */

function makeTile(sample, strong) {
  const color = new THREE.Color().setRGB(sample.rgba[0] / 255, sample.rgba[1] / 255, sample.rgba[2] / 255, THREE.SRGBColorSpace);
  const top = new THREE.MeshBasicMaterial({ color });
  const wall = new THREE.MeshBasicMaterial({ color: color.clone().multiplyScalar(0.55) });
  const lift = strong ? 0.7 : 0.45;
  const geo = new THREE.BoxGeometry(1, 1, lift);
  geo.translate(0, 0, lift / 2);
  const box = new THREE.Mesh(geo, [wall, wall, wall, wall, top, top]);
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0xf6f7f9 }));
  // Offset ground shadow: from straight above it is what makes the cell read as lifted.
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(1.12, 1.12),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.5, depthWrite: false }),
  );
  shadow.position.set(0.16, -0.16, 0);
  const group = new THREE.Group();
  group.add(shadow, box, edges);
  group.matrixAutoUpdate = false;
  group.userData = { frame: frameAt(sample.x, sample.y, MARK_R), k: strong ? 1.35 : 1.2 };
  group.renderOrder = 5;
  overlay.add(group);
  sizeTile(group);
  return group;
}

const tileScale = new THREE.Matrix4();
function sizeTile(group) {
  if (!group) return;
  const side = markerPx() * pxWorld() * group.userData.k;
  group.matrix.copy(group.userData.frame).multiply(tileScale.makeScale(side, side, side));
  group.matrixWorldNeedsUpdate = true;
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
  const est = Boolean(sample.estimate);
  $("readout-chip").style.background = `rgb(${sample.rgba[0]},${sample.rgba[1]},${sample.rgba[2]})`;
  $("readout-chip").style.opacity = est ? "0.6" : "1";
  $("readout-title").textContent = est
    ? "Estimate — not scored"
    : sample.is_best ? "Best evaluated cell" : "Evaluated cell";
  $("readout-lat").textContent = fmtLat(sample.lat_deg);
  $("readout-lon").textContent = fmtLon(sample.lon_deg);
  $("readout-score-label").textContent = est ? "Estimated score" : "Score";
  $("readout-score").textContent = est
    ? sample.feasible ? `≈ ${sample.score.toFixed(2)}` : "likely infeasible"
    : sample.feasible ? Number(sample.score).toFixed(3) : "0 · infeasible";
  $("readout-note").textContent = est
    ? `Interpolated from ${sample.n} evaluated cell${sample.n === 1 ? "" : "s"}; the nearest is ${(sample.dMin * MOON_R_KM).toFixed(1)} km away. The search did not evaluate this spot` +
      (pinned ? " — open it in the planner to score it." : ". Click to pin.")
    : !sample.feasible && sample.marker_t != null
      ? `Does not meet the mission needs. Relative badness in this query: ${Math.round(100 * (1 - sample.marker_t))} %.`
      : pinned ? "" : "Click to pin this cell.";
  $("readout-note").hidden = !$("readout-note").textContent;
  $("open-planner").textContent = est ? "Evaluate in planner" : "Open in planner";
  $("readout-actions").hidden = !pinned;
}

function setHovered(sample) {
  if (sample === hovered) return;
  if (sample?.estimate && hovered?.estimate && sample.key === hovered.key) return;
  hovered = sample;
  dropTile("hover");
  if (sample && !sample.estimate && sample !== selected) tiles.hover = makeTile(sample, false);
  canvas.classList.toggle("over-cell", Boolean(sample));
  const shown = sample ?? selected;
  showReadout(shown, Boolean(shown) && shown === selected);
}

function setSelected(sample) {
  selected = sample;
  dropTile("selected");
  dropTile("hover");
  if (sample && !sample.estimate) tiles.selected = makeTile(sample, true);
  showReadout(sample, Boolean(sample));
  for (const li of $("top-list").children) li.classList.toggle("active", li.sample === sample);
}

/* ---------- picking: evaluated cells first (D-2325) ---------- */

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const unitSphere = new THREE.Sphere(new THREE.Vector3(), 1);
const hit = new THREE.Vector3();

function estimateSample(x, y) {
  const est = data.estimate;
  if (!est || evaluatedOnly()) return null;
  const e = estimateAt(x, y, est.reach);
  if (!e) return null;
  const rho = Math.hypot(x, y);
  const lat = (2 * Math.atan(rho / 2) * 180) / Math.PI - 90;
  const lon = (((Math.atan2(x, y) * 180) / Math.PI) % 360 + 360) % 360;
  return {
    estimate: true,
    key: `${Math.round(x / (0.25 * CELL))},${Math.round(y / (0.25 * CELL))}`,
    x, y, lat_deg: lat, lon_deg: lon,
    feasible: e.feasible, score: e.score, n: e.n, dMin: e.dMin,
    rgba: e.feasible ? scoreRgb(e.score) : INFEASIBLE_RGB,
  };
}

function pickSample(clientX, clientY) {
  if (!data.samples.length) return null;
  const r = canvas.getBoundingClientRect();
  pointer.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
  raycaster.setFromCamera(pointer, camera);
  if (!raycaster.ray.intersectSphere(unitSphere, hit)) return null;
  const [x, y] = vec3ToStereo(hit);
  // Snap to the nearest evaluated cell within a generous screen radius; only when none is that
  // close does the pointer read the estimate layer.
  const w = pxWorld();
  return nearestSample(x, y, Math.max(PICK_PX * w, 0.6 * markerPx() * w)) ?? estimateSample(x, y);
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

/* ---------- best evaluated cells list (D-2325) ---------- */

function buildTopList() {
  const list = $("top-list");
  list.replaceChildren();
  const top = data.samples.filter((s) => s.feasible).sort((a, b) => b.score - a.score).slice(0, TOP_N);
  $("top-panel").hidden = top.length === 0;
  $("top-count").textContent = String(top.length);
  top.forEach((s, i) => {
    const li = document.createElement("li");
    li.sample = s;
    const btn = document.createElement("button");
    btn.type = "button";
    const chip = document.createElement("i");
    chip.style.background = `rgb(${s.rgba[0]},${s.rgba[1]},${s.rgba[2]})`;
    const rank = document.createElement("span");
    rank.className = "rank";
    rank.textContent = `${i + 1}`;
    const score = document.createElement("b");
    score.textContent = Number(s.score).toFixed(3);
    const where = document.createElement("span");
    where.className = "where";
    where.textContent = `${Math.abs(s.lat_deg).toFixed(2)}° S, ${fmtLon(s.lon_deg).replace(/(\.\d{2})\d+/, "$1")}`;
    btn.append(rank, chip, score, where);
    btn.addEventListener("click", () => {
      setSelected(s);
      flyTo(stereoToVec3(s.x, s.y), Math.min(view.alt, Math.max(0.02, 16 * data.spacing))); // ~12 spacings across
    });
    li.append(btn);
    list.append(li);
  });
}

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
  const span = 2 * Math.max(ang + 1.5 * data.spacing, 4 * CELL);
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
  if (markers) {
    const range = renderer.getContext().getParameter(renderer.getContext().ALIASED_POINT_SIZE_RANGE);
    markers.material.uniforms.uSize.value = Math.min(range[1], markerPx() * renderer.getPixelRatio());
  }
  sizeTile(tiles.hover);
  sizeTile(tiles.selected);
  renderer.render(scene, camera);
  updateBestPin();
}

/* ---------- loading ---------- */

function showSamples(payload, label) {
  clearOverlay();
  setSelected(null);
  // Evaluated cells only: the API's four-neighbour induced copies are superseded by the
  // estimate layer (D-1df2) and no longer drawn.
  const samples = (payload.samples || []).filter((s) => !s.induced).map((s) => {
    const [x, y] = latLonToStereo(s.lat_deg, s.lon_deg);
    return { ...s, x, y };
  });
  data = { samples, spacing: CELL, hash: new Map(), best: null, ceiling: Number(payload.score_ceiling ?? 1.4), estimate: null };
  data.spacing = estimateSpacing(samples);
  data.hash = buildHash(samples, data.spacing);
  data.best = samples.find((s) => s.is_best) ?? null;

  $("ramp-mid").textContent = (data.ceiling / 2).toFixed(1);
  $("ramp-max").textContent = `${data.ceiling.toFixed(1)}+`;
  $("legend-infeasible").hidden = !samples.some((s) => !s.feasible);
  $("empty").hidden = samples.length > 0;
  if (data.best) $("best-pin-label").textContent = `Best ${Number(data.best.score).toFixed(2)}`;
  buildTopList();

  if (!samples.length) {
    setStatus("No cells in this result");
    return;
  }
  buildEstimate();
  buildMarkers();
  fitData(true);

  const nFeasible = samples.filter((s) => s.feasible).length;
  setStatus(
    `${label ? label + " · " : ""}${samples.length} evaluated cells (${nFeasible} feasible) · ` +
      (payload.search_partial ? "partial search — the rest is estimated, not scored" : "full coverage"),
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

try {
  $("evaluated-only").checked = localStorage.getItem("clps:mapEvaluatedOnly") === "1";
} catch (_) {
  /* storage blocked */
}
$("evaluated-only").addEventListener("change", () => {
  const only = evaluatedOnly();
  try {
    localStorage.setItem("clps:mapEvaluatedOnly", only ? "1" : "0");
  } catch (_) {
    /* storage blocked */
  }
  if (data.estimate) data.estimate.mesh.visible = !only;
  $("legend-estimate").hidden = only;
  if (hovered?.estimate) setHovered(null);
  if (selected?.estimate) setSelected(null);
});
$("legend-estimate").hidden = evaluatedOnly();

resize();
new ResizeObserver(resize).observe(host);
requestAnimationFrame(tick);

if (STATIC || QUERY.get("demo") === "1") loadDemo();
else loadStoredSearch();
