/**
 * S9 region score map — orbitable Moon with score overlay.
 * Decisions: D-4126 3D Moon, D-8acb infeasible black, D-7227 API colours,
 * D-834a interpolate overview / solid on lift, D-85bf induced alpha from API.
 */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const MOON_R = 1;
const LIFT = 0.04;
const PLANNER_KEYS = [
  "start", "end", "step_h", "template_id",
  "max_night_h", "max_no_earth_h", "min_continuous_lit_h",
  "require_both", "sun_lit_percent", "earth_lit_percent", "bridge_h",
  "hazards_enabled", "local_search",
];

/** South-pole-ish demo rows for POST /region-map (no prior search). */
const DEMO_ROWS = [
  { lat_deg: -89.46316, lon_deg: 222.51045, score: 1.05, feasible: true, companion_score: 1.05 },
  { lat_deg: -89.52, lon_deg: 205.0, score: 0.62, feasible: true, companion_score: 0.62 },
  { lat_deg: -89.48, lon_deg: 248.0, score: 0.22, feasible: true, companion_score: 0.22 },
  { lat_deg: -89.56, lon_deg: 218.0, score: 0, feasible: false, companion_score: 0.38 },
  { lat_deg: -89.5, lon_deg: 238.0, score: 0, feasible: false, companion_score: 0.12 },
];
const DEMO_BEST = DEMO_ROWS[0];
/** ?static=1 → browser demo without API: demo rows only, from the exported region-map JSON. */
const STATIC = new URLSearchParams(location.search).get("static") === "1";
if (STATIC) document.querySelector('a[href="/"]')?.remove();

const statusEl = document.getElementById("status");
const host = document.getElementById("canvas-host");

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
host.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 50);
camera.position.set(0.15, -2.4, 0.35);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, -0.35, 0);
controls.minDistance = 1.4;
controls.maxDistance = 6;

scene.add(new THREE.AmbientLight(0x404050, 0.35));
const key = new THREE.DirectionalLight(0xfff5e6, 1.1);
key.position.set(3, 2, 4);
scene.add(key);

const texLoader = new THREE.TextureLoader();
const moonTex = texLoader.load("assets/moon.jpg");
moonTex.colorSpace = THREE.SRGBColorSpace;

const moon = new THREE.Mesh(
  new THREE.SphereGeometry(MOON_R, 64, 64),
  new THREE.MeshStandardMaterial({ map: moonTex, roughness: 0.95, metalness: 0.02 }),
);
scene.add(moon);

/** Equirectangular score wash — D-834a overview interpolation. */
const paintCanvas = document.createElement("canvas");
paintCanvas.width = 1024;
paintCanvas.height = 512;
const paintCtx = paintCanvas.getContext("2d");
const paintTex = new THREE.CanvasTexture(paintCanvas);
paintTex.colorSpace = THREE.SRGBColorSpace;

const paintShell = new THREE.Mesh(
  new THREE.SphereGeometry(MOON_R * 1.003, 48, 48),
  new THREE.MeshBasicMaterial({
    map: paintTex,
    transparent: true,
    depthWrite: false,
    blending: THREE.NormalBlending,
  }),
);
scene.add(paintShell);

const markers = new THREE.Group();
scene.add(markers);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let markerRecords = [];
let hovered = null;
let selected = null;

function setStatus(msg, err = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("err", err);
}

function latLonToVec3(latDeg, lonDeg, r = MOON_R) {
  const lat = (latDeg * Math.PI) / 180;
  const lon = (lonDeg * Math.PI) / 180;
  return new THREE.Vector3(
    r * Math.cos(lat) * Math.cos(lon),
    r * Math.sin(lat),
    r * Math.cos(lat) * Math.sin(lon),
  );
}

function latLonToCanvasXY(latDeg, lonDeg, w, h) {
  const x = ((lonDeg % 360) + 360) % 360 / 360 * w;
  const y = (0.5 - latDeg / 180) * h;
  return [x, y];
}

function rgbaCss(rgba, alphaOverride) {
  // API sends r,g,b in 0..255 and a in 0..1 (D-7227 / D-8acb)
  const [r, g, b, a] = rgba;
  const alpha = alphaOverride ?? a;
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${alpha})`;
}

function paintOverview(samples) {
  const w = paintCanvas.width;
  const h = paintCanvas.height;
  paintCtx.clearRect(0, 0, w, h);
  for (const s of samples) {
    const [cx, cy] = latLonToCanvasXY(s.lat_deg, s.lon_deg, w, h);
    const spread = s.induced ? 72 : 56;
    const g = paintCtx.createRadialGradient(cx, cy, 0, cx, cy, spread);
    const mid = rgbaCss(s.rgba);
    const edge = rgbaCss(s.rgba, 0);
    g.addColorStop(0, mid);
    g.addColorStop(1, edge);
    paintCtx.fillStyle = g;
    paintCtx.beginPath();
    paintCtx.arc(cx, cy, spread, 0, Math.PI * 2);
    paintCtx.fill();
    // wrap longitude
    if (cx < spread) {
      paintCtx.beginPath();
      paintCtx.arc(cx + w, cy, spread, 0, Math.PI * 2);
      paintCtx.fill();
    } else if (cx > w - spread) {
      paintCtx.beginPath();
      paintCtx.arc(cx - w, cy, spread, 0, Math.PI * 2);
      paintCtx.fill();
    }
  }
  paintTex.needsUpdate = true;
}

function makeMarker(sample) {
  const pos = latLonToVec3(sample.lat_deg, sample.lon_deg, MOON_R * 1.006);
  const normal = pos.clone().normalize();
  const color = new THREE.Color().setRGB(
    sample.rgba[0] / 255,
    sample.rgba[1] / 255,
    sample.rgba[2] / 255,
  );
  const opacity = sample.rgba[3];

  const disc = new THREE.Mesh(
    new THREE.CircleGeometry(0.018, 20),
    new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      side: THREE.DoubleSide,
      depthTest: true,
    }),
  );
  disc.position.copy(pos);
  disc.lookAt(pos.clone().multiplyScalar(2));
  disc.userData.sample = sample;
  disc.userData.baseOpacity = opacity;
  markers.add(disc);

  const record = { disc, sample, ring: null, badDot: null };
  // per D-8acb: in-query relative badness dot on black (infeasible) cells
  if (!sample.feasible && sample.marker_t != null) {
    const t = Math.min(1, Math.max(0, Number(sample.marker_t)));
    const badDot = new THREE.Mesh(
      new THREE.CircleGeometry(0.004 + 0.01 * t, 12),
      new THREE.MeshBasicMaterial({
        color: 0xf0f0f0,
        transparent: true,
        opacity: 0.9,
        side: THREE.DoubleSide,
        depthTest: true,
      }),
    );
    badDot.position.copy(pos.clone().add(normal.clone().multiplyScalar(0.003)));
    badDot.lookAt(pos.clone().multiplyScalar(2));
    markers.add(badDot);
    record.badDot = badDot;
  }
  if (sample.is_best) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.026, 0.034, 28),
      new THREE.MeshBasicMaterial({
        color: 0xc9a227,
        transparent: true,
        opacity: 0.95,
        side: THREE.DoubleSide,
      }),
    );
    ring.position.copy(pos.clone().add(normal.clone().multiplyScalar(0.002)));
    ring.lookAt(pos.clone().multiplyScalar(2));
    markers.add(ring);
    record.ring = ring;
  }
  return record;
}

function clearMarkers() {
  while (markers.children.length) {
    const c = markers.children[0];
    markers.remove(c);
    c.geometry?.dispose();
    c.material?.dispose?.();
  }
  markerRecords = [];
  hovered = null;
  selected = null;
}

function applyLift(record, on) {
  if (!record) return;
  const { disc, sample, ring, badDot } = record;
  const base = latLonToVec3(sample.lat_deg, sample.lon_deg, MOON_R * 1.006);
  const n = base.clone().normalize();
  if (on) {
    disc.position.copy(base.clone().add(n.multiplyScalar(LIFT)));
    disc.material.opacity = 1; // D-834a solid center on lift
    disc.scale.setScalar(1.85);
    if (ring) {
      ring.position.copy(disc.position.clone().add(n.clone().multiplyScalar(0.002)));
      ring.scale.setScalar(1.2);
    }
    if (badDot) {
      badDot.position.copy(disc.position.clone().add(n.clone().multiplyScalar(0.003)));
      badDot.scale.setScalar(1.2);
    }
  } else {
    disc.position.copy(base);
    disc.material.opacity = disc.userData.baseOpacity;
    disc.scale.setScalar(1);
    if (ring) {
      ring.position.copy(base.clone().add(n.clone().multiplyScalar(0.002)));
      ring.scale.setScalar(1);
    }
    if (badDot) {
      badDot.position.copy(base.clone().add(n.clone().multiplyScalar(0.003)));
      badDot.scale.setScalar(1);
    }
  }
}

function focusMarker(record) {
  if (hovered && hovered !== record) applyLift(hovered, false);
  hovered = record;
  if (!record) {
    if (!selected) setStatus("Drag to orbit · click a cell for site chart");
    return;
  }
  applyLift(record, true);
  const s = record.sample;
  setStatus(
    `lat ${s.lat_deg.toFixed(3)}° lon ${s.lon_deg.toFixed(3)}° · ` +
      `score ${s.feasible ? s.score.toFixed(2) : "infeasible"}` +
      (s.is_best ? " · best" : "") +
      (s.induced ? " · induced" : ""),
  );
}

function readPlannerContext() {
  const q = new URLSearchParams();
  const stored = localStorage.getItem("clps:plannerQuery");
  if (stored) {
    for (const [k, v] of new URLSearchParams(stored)) q.set(k, v);
  }
  for (const k of PLANNER_KEYS) {
    if (new URLSearchParams(location.search).has(k)) {
      q.set(k, new URLSearchParams(location.search).get(k));
    }
  }
  return q;
}

function openSiteChart(sample) {
  if (STATIC) return; // no standalone planner page in the browser demo
  const q = readPlannerContext();
  q.set("lat", String(sample.lat_deg));
  q.set("lon", String(sample.lon_deg));
  if (!q.has("start")) q.set("start", "2027-01-01T00:00:00Z");
  if (!q.has("end")) q.set("end", "2027-01-01T23:00:00Z");
  if (!q.has("step_h")) q.set("step_h", "1");
  location.href = "/?" + q.toString();
}

async function postRegionMap(body) {
  if (STATIC) {
    const res = await fetch("demo/region-map-demo.json");
    if (!res.ok) throw new Error(`demo data HTTP ${res.status}`);
    return res.json();
  }
  const res = await fetch("/region-map", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail?.message || data.detail || res.statusText);
  }
  return data;
}

function showSamples(payload) {
  clearMarkers();
  paintOverview(payload.samples || []);
  for (const s of payload.samples || []) {
    markerRecords.push(makeMarker(s));
  }
  const n = payload.n_evaluated ?? 0;
  const ni = payload.n_induced ?? 0;
  setStatus(`Loaded ${n} evaluated${ni ? ` + ${ni} induced` : ""} · orbit / hover / click`);
}

async function loadDemo() {
  setStatus("POST /region-map …");
  try {
    const payload = await postRegionMap({
      rows: DEMO_ROWS,
      search_partial: true,
      best: DEMO_BEST,
    });
    showSamples(payload);
  } catch (e) {
    setStatus("Region map failed: " + e.message, true);
  }
}

async function loadFromPlannerStorage() {
  const raw = localStorage.getItem("clps:regionMapRequest");
  if (!raw) return;
  try {
    const body = JSON.parse(raw);
    setStatus("Loading search results…");
    showSamples(await postRegionMap(body));
  } catch (e) {
    setStatus("Stored region map request invalid: " + e.message, true);
  }
}

function resize() {
  const w = host.clientWidth;
  const h = host.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

function pickMarker(clientX, clientY) {
  const r = renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - r.left) / r.width) * 2 - 1;
  pointer.y = -((clientY - r.top) / r.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(
    markerRecords.map((m) => m.disc),
    false,
  );
  if (!hits.length) return null;
  return markerRecords.find((m) => m.disc === hits[0].object) || null;
}

renderer.domElement.addEventListener("pointermove", (ev) => {
  if (ev.buttons) return;
  focusMarker(pickMarker(ev.clientX, ev.clientY));
});

renderer.domElement.addEventListener("pointerleave", () => {
  if (!selected) focusMarker(null);
});

renderer.domElement.addEventListener("click", (ev) => {
  const rec = pickMarker(ev.clientX, ev.clientY);
  if (!rec) return;
  selected = rec;
  focusMarker(rec);
  openSiteChart(rec.sample);
});

document.getElementById("load-demo").addEventListener("click", () => loadDemo());

function tick() {
  requestAnimationFrame(tick);
  controls.update();
  renderer.render(scene, camera);
}

resize();
window.addEventListener("resize", resize);
tick();

if (STATIC || new URLSearchParams(location.search).get("demo") === "1") {
  loadDemo();
} else {
  loadFromPlannerStorage();
}