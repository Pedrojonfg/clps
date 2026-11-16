/* S10 first-person view — lunar-eval
 * D-ac34 hybrid (third-party backdrop + our mask/sky), D-7d58 CesiumJS + Cesium Moon,
 * D-f2d3 2 m observer / look-around only, D-e062 same site×time query as the planner,
 * D-671e provenance one-liner + details, D-ac74 2D mask panorama when Cesium is unavailable.
 */

(function () {
  const OBSERVER_HEIGHT_M = 2; // per D-f2d3
  const CESIUM_MOON_ION_ASSET = 2684829; // per D-7d58
  const OVERLAY_DISTANCE_M = 20000; // our mask/sky are directions; drawn on a far shell, never depth-hidden
  const SUN = "#c9a227";
  const EARTH = "#6a8faa";
  const MASK_LINE = "#c4b8a8";
  const MASK_FILL = "#4a4650";
  const PITCH_MIN = -25;
  const PITCH_MAX = 70;

  const EMBEDDED = window.parent !== window;
  const $ = (id) => document.getElementById(id);

  const state = {
    data: null,
    skyIndex: 0,
    mode: "loading",
    viewer: null,
    query: "",
    lat: -89.46316,
    lon: 222.51045,
    look: { heading: 0, pitch: 4, fov: 60 },
    cesium: null, // { origin, enu, sun, earth }
  };

  function parseQuery() {
    // per D-e062: same query string as the S8 horizon planner
    const p = new URLSearchParams(window.location.search);
    if (p.has("lat")) state.lat = Number(p.get("lat"));
    if (p.has("lon")) state.lon = Number(p.get("lon"));
    const q = new URLSearchParams(p);
    q.delete("ion_token");
    state.query = q.toString();
    return p;
  }

  function getIonToken(params) {
    // per D-7d58: never hardcode; window → query → localStorage
    const fromWin = typeof window.CESIUM_ION_TOKEN === "string" ? window.CESIUM_ION_TOKEN.trim() : "";
    if (fromWin) return fromWin;
    const fromQ = params.get("ion_token");
    if (fromQ && fromQ.trim()) return fromQ.trim();
    try {
      const ls = localStorage.getItem("cesium_ion_token");
      if (ls && ls.trim()) return ls.trim();
    } catch (_) {
      /* private mode */
    }
    return "";
  }

  function toUtcIso(localLike) {
    if (!localLike) return "";
    if (/Z$/.test(localLike) || /[+-]\d{2}:\d{2}$/.test(localLike)) return localLike;
    return localLike + ":00Z";
  }

  function mockSitePayload() {
    // per D-3832: inline mock shaped like the api mock
    const t0 = new Date("2026-06-21T00:00:00Z");
    const mask_elev = [];
    for (let i = 0; i < 720; i++) {
      const az = i * 0.5;
      let h = 1.6 + 0.85 * Math.sin((az * 2.17 * Math.PI) / 180);
      if (az > 145 && az < 235) h += 2.8 * Math.exp(-((az - 192) ** 2) / 180);
      mask_elev.push(Math.round(h * 1e4) / 1e4);
    }
    const sky = [];
    for (let hr = 0; hr < 24; hr++) {
      const ts = new Date(t0.getTime() + hr * 3600000);
      const sun_az = ((hr / 24) * 360 + 12) % 360;
      const sun_el = -2.4 + 4.8 * Math.max(0, Math.sin(((hr - 6) * 15 * Math.PI) / 180));
      sky.push({
        time_utc: ts.toISOString().replace(".000Z", "Z"),
        sun_az_deg: Math.round(sun_az * 100) / 100,
        sun_el_deg: Math.round(sun_el * 1000) / 1000,
        earth_az_deg: Math.round(((sun_az + 118) % 360) * 100) / 100,
        earth_el_deg: Math.round((4.5 + 3.2 * Math.sin(((hr * 18 - 40) * Math.PI) / 180)) * 1000) / 1000,
      });
    }
    return {
      data_source: "mock",
      mask: { elevation_deg: mask_elev, lat: state.lat, lon: state.lon },
      sky,
    };
  }

  async function fetchSiteData() {
    const status = $("load-status");
    try {
      // ?static=1 → browser demo without API: the exported mock payload.
      const isStatic = new URLSearchParams(state.query).get("static") === "1";
      const res = await fetch(isStatic ? "demo/site-mock.json" : "/site?" + state.query);
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail?.message || body.detail?.error || res.statusText);
      const live = body.data_source === "real";
      status.textContent = live ? "Live site data" : "Mock site data";
      status.className = "tag " + (live ? "ok" : "warn");
      return body;
    } catch (e) {
      status.className = "tag warn";
      status.textContent = "Inline mock data";
      showNotice(["Site data could not be loaded (" + e.message + "). Showing an inline mock horizon and sky."]);
      return mockSitePayload();
    }
  }

  function skyIndexForStart(data, params) {
    const start = params.get("start");
    if (!start || !data.sky?.length) return 0;
    const tWant = Date.parse(toUtcIso(start));
    if (Number.isNaN(tWant)) return 0;
    // Start outside the returned series (e.g. mock data on another date) → first sample.
    const tFirst = Date.parse(data.sky[0].time_utc);
    const tLast = Date.parse(data.sky[data.sky.length - 1].time_utc);
    if (tWant < tFirst || tWant > tLast) return 0;
    let best = 0;
    let bestD = Infinity;
    data.sky.forEach((s, i) => {
      const d = Math.abs(Date.parse(s.time_utc) - tWant);
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    });
    return best;
  }

  /* ---------- shared chrome ---------- */

  /** parts: strings and {text, href} links, appended to any earlier notice. */
  function showNotice(parts) {
    const box = $("notice");
    if (!box.hidden) box.appendChild(document.createTextNode(" "));
    for (const part of parts) {
      if (typeof part === "string") box.appendChild(document.createTextNode(part));
      else {
        const a = document.createElement("a");
        a.href = part.href;
        a.target = "_blank";
        a.rel = "noreferrer";
        a.textContent = part.text;
        box.appendChild(a);
      }
    }
    box.hidden = false;
  }

  function maskAt(azDeg) {
    const el = state.data.mask.elevation_deg;
    const n = el.length;
    const f = ((((azDeg % 360) + 360) % 360) / 360) * n;
    const i = Math.floor(f) % n;
    const t = f - Math.floor(f);
    return el[i] * (1 - t) + el[(i + 1) % n] * t;
  }

  const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  function compass(azDeg) {
    return COMPASS[Math.round((((azDeg % 360) + 360) % 360) / 45) % 8];
  }

  function bodyState(az, el) {
    const clear = el - maskAt(az);
    const where = `${el.toFixed(1)}° el · az ${az.toFixed(0)}° ${compass(az)}`;
    return { visible: clear > 0, text: `${where} · ${clear > 0 ? "above" : "behind"} mask` };
  }

  function fmtTime(iso) {
    return iso.replace("T", " ").replace(/:00Z$/, " UTC").replace(/Z$/, " UTC");
  }

  function updateReadouts() {
    const s = state.data.sky[state.skyIndex];
    $("hour-label").textContent = s ? fmtTime(s.time_utc) : "—";
    if (!s) return;
    $("sun-state").textContent = bodyState(s.sun_az_deg, s.sun_el_deg).text;
    $("earth-state").textContent = bodyState(s.earth_az_deg, s.earth_el_deg).text;
  }

  function setupChrome(data, params) {
    if (!EMBEDDED && params.get("static") !== "1") {
      const back = $("back-link");
      back.href = "/?" + state.query;
      back.hidden = false;
    }
    const mlat = Number(data.mask?.lat ?? state.lat);
    const mlon = Number(data.mask?.lon ?? state.lon);
    $("site-meta").textContent =
      `${Math.abs(mlat).toFixed(4)}° ${mlat < 0 ? "S" : "N"}, ${mlon.toFixed(4)}° E · observer ${OBSERVER_HEIGHT_M} m`;

    const range = $("hour-range");
    if (data.sky.length > 1) {
      $("hour-scrub").hidden = false;
      range.max = String(data.sky.length - 1);
      range.value = String(state.skyIndex);
    }
    range.addEventListener("input", () => {
      state.skyIndex = Number(range.value);
      refresh();
    });

    const toggle = $("details-toggle");
    toggle.addEventListener("click", () => {
      const open = $("details").hidden;
      $("details").hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
    });
    updateReadouts();
  }

  function refresh() {
    updateReadouts();
    if (state.mode === "cesium") updateCesiumSky();
    else if (state.mode === "fallback") drawFallback2D();
  }

  /* ---------- Cesium backdrop + our overlays ---------- */

  /** Ask ion directly so a failure can say what to fix. */
  async function probeIon(token) {
    try {
      const res = await fetch(
        `https://api.cesium.com/v1/assets/${CESIUM_MOON_ION_ASSET}/endpoint?access_token=${encodeURIComponent(token)}`,
      );
      if (res.ok) return "ok";
      if (res.status === 401) return "token_invalid";
      if (res.status === 404 || res.status === 403) return "asset_missing";
      return "ion_error";
    } catch (_) {
      return "offline";
    }
  }

  const ION_NOTICES = {
    token_invalid: ["Cesium ion rejected the saved token. Create a new one at ", { text: "ion.cesium.com/tokens", href: "https://ion.cesium.com/tokens" }, " and save it again. Showing the 2D mask panorama."],
    asset_missing: [
      "Your ion token works, but Cesium Moon Terrain (asset 2684829) is not in your ion account yet. Open ",
      { text: "the asset in the ion Asset Depot", href: "https://ion.cesium.com/assetdepot/2684829" },
      ", choose “Add to my assets”, then reload. Showing the 2D mask panorama meanwhile.",
    ],
    ion_error: ["Cesium ion did not answer correctly. Showing the 2D mask panorama."],
    offline: ["Cesium ion is unreachable (offline?). Showing the 2D mask panorama."],
  };

  function dirToWorld(azDeg, elDeg, distM) {
    const Cesium = window.Cesium;
    const az = (azDeg * Math.PI) / 180;
    const el = (elDeg * Math.PI) / 180;
    const local = new Cesium.Cartesian3(
      distM * Math.cos(el) * Math.sin(az), // east
      distM * Math.cos(el) * Math.cos(az), // north
      distM * Math.sin(el), // up
    );
    return Cesium.Matrix4.multiplyByPoint(state.cesium.enu, local, new Cesium.Cartesian3());
  }

  function applyLook() {
    const Cesium = window.Cesium;
    const { heading, pitch, fov } = state.look;
    const cam = state.viewer.camera;
    cam.frustum.fov = Cesium.Math.toRadians(fov);
    cam.setView({
      destination: state.cesium.origin,
      orientation: {
        heading: Cesium.Math.toRadians(heading),
        pitch: Cesium.Math.toRadians(pitch),
        roll: 0,
      },
    });
    const h = ((heading % 360) + 360) % 360;
    $("look-readout").textContent = `Looking ${h.toFixed(0)}° ${compass(h)} · ${pitch >= 0 ? "+" : ""}${pitch.toFixed(0)}° pitch`;
  }

  function face(azDeg, elDeg) {
    state.look.heading = azDeg;
    state.look.pitch = Math.min(PITCH_MAX, Math.max(PITCH_MIN, elDeg));
    applyLook();
  }

  /** per D-f2d3: yaw/pitch look-around from a fixed 2 m eye point; no translation, no flight. */
  function installLookControls(viewer) {
    viewer.scene.screenSpaceCameraController.enableInputs = false;
    const el = $("cesiumContainer");
    let last = null;
    el.addEventListener("pointerdown", (ev) => {
      last = [ev.clientX, ev.clientY];
      el.setPointerCapture(ev.pointerId);
      el.classList.add("dragging");
    });
    el.addEventListener("pointermove", (ev) => {
      if (!last) return;
      const degPerPx = state.look.fov / el.clientHeight;
      state.look.heading -= (ev.clientX - last[0]) * degPerPx;
      state.look.pitch = Math.min(PITCH_MAX, Math.max(PITCH_MIN, state.look.pitch + (ev.clientY - last[1]) * degPerPx));
      last = [ev.clientX, ev.clientY];
      applyLook();
    });
    const end = () => {
      last = null;
      el.classList.remove("dragging");
    };
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
    el.addEventListener(
      "wheel",
      (ev) => {
        ev.preventDefault();
        state.look.fov = Math.min(90, Math.max(20, state.look.fov * Math.exp(ev.deltaY * 0.001)));
        applyLook();
      },
      { passive: false },
    );
    el.tabIndex = 0;
    el.addEventListener("keydown", (ev) => {
      const step = { ArrowLeft: [-5, 0], ArrowRight: [5, 0], ArrowUp: [0, 3], ArrowDown: [0, -3] }[ev.key];
      if (!step) return;
      ev.preventDefault();
      state.look.heading += step[0];
      state.look.pitch = Math.min(PITCH_MAX, Math.max(PITCH_MIN, state.look.pitch + step[1]));
      applyLook();
    });
  }

  function trackSegments(azKey, elKey) {
    // Split where azimuth wraps so the track never cuts across the view.
    const segs = [[]];
    let prev = null;
    for (const s of state.data.sky) {
      if (prev !== null && Math.abs(s[azKey] - prev) > 180) segs.push([]);
      segs[segs.length - 1].push(dirToWorld(s[azKey], s[elKey], OVERLAY_DISTANCE_M));
      prev = s[azKey];
    }
    return segs.filter((g) => g.length > 1);
  }

  function buildCesiumOverlays() {
    const Cesium = window.Cesium;
    const ents = state.viewer.entities;
    const always = Number.POSITIVE_INFINITY;
    const line = (positions, css, width, alpha) => {
      const color = Cesium.Color.fromCssColorString(css).withAlpha(alpha);
      const material = new Cesium.ColorMaterialProperty(color);
      return ents.add({ polyline: { positions, width, material, depthFailMaterial: material, arcType: Cesium.ArcType.NONE } });
    };
    const labelStyle = (text, css) => ({
      text,
      font: "12px sans-serif",
      fillColor: Cesium.Color.fromCssColorString(css),
      showBackground: true,
      backgroundColor: Cesium.Color.fromCssColorString("#1c2127").withAlpha(0.85),
      backgroundPadding: new Cesium.Cartesian2(6, 4),
      pixelOffset: new Cesium.Cartesian2(0, -22),
      disableDepthTestDistance: always,
    });

    // Ours (D-ac34): horizon mask as a line on the sky, drawn over the backdrop.
    const elev = state.data.mask.elevation_deg;
    const ring = elev.map((el, i) => dirToWorld((i * 360) / elev.length, el, OVERLAY_DISTANCE_M));
    ring.push(ring[0]);
    line(ring, MASK_LINE, 2.5, 0.95);

    ["N", "E", "S", "W"].forEach((name, i) => {
      ents.add({
        position: dirToWorld(i * 90, maskAt(i * 90) + 1.5, OVERLAY_DISTANCE_M),
        label: { ...labelStyle(name, "#abb3bf"), pixelOffset: new Cesium.Cartesian2(0, 0) },
      });
    });

    for (const seg of trackSegments("sun_az_deg", "sun_el_deg")) line(seg, SUN, 1.5, 0.55);
    for (const seg of trackSegments("earth_az_deg", "earth_el_deg")) line(seg, EARTH, 1.5, 0.55);

    const marker = (css, size) =>
      ents.add({
        position: state.cesium.origin,
        point: {
          pixelSize: size,
          color: Cesium.Color.fromCssColorString(css),
          outlineColor: Cesium.Color.fromCssColorString("#111418"),
          outlineWidth: 2,
          disableDepthTestDistance: always,
        },
        label: labelStyle("", css),
      });
    state.cesium.sun = marker(SUN, 16);
    state.cesium.earth = marker(EARTH, 13);
  }

  function updateCesiumSky() {
    const Cesium = window.Cesium;
    const s = state.data.sky[state.skyIndex];
    if (!s || !state.cesium) return;
    const put = (ent, name, az, el) => {
      ent.position = dirToWorld(az, el, OVERLAY_DISTANCE_M);
      const visible = bodyState(az, el).visible;
      ent.label.text = visible ? `${name} · ours` : `${name} · ours · behind our mask`;
      ent.point.color = Cesium.Color.fromCssColorString(name === "Sun" ? SUN : EARTH).withAlpha(visible ? 1 : 0.45);
    };
    put(state.cesium.sun, "Sun", s.sun_az_deg, s.sun_el_deg);
    put(state.cesium.earth, "Earth", s.earth_az_deg, s.earth_el_deg);

    // Backdrop relief is lit from our Sun azimuth at a fixed 35° so flat ground still reads.
    // Polar sun is a few degrees high; real grazing light would leave the backdrop black.
    try {
      const toSun = Cesium.Cartesian3.subtract(
        dirToWorld(s.sun_az_deg, 35, 1000),
        state.cesium.origin,
        new Cesium.Cartesian3(),
      );
      state.viewer.scene.light = new Cesium.DirectionalLight({
        direction: Cesium.Cartesian3.normalize(Cesium.Cartesian3.negate(toSun, toSun), toSun),
        intensity: 3.0,
      });
    } catch (_) {
      /* lighting is cosmetic */
    }
  }

  async function terrainHeight(viewer, lon, lat) {
    const Cesium = window.Cesium;
    try {
      const carto = Cesium.Cartographic.fromDegrees(lon > 180 ? lon - 360 : lon, lat);
      const timeout = new Promise((resolve) => setTimeout(() => resolve(null), 15000));
      const out = await Promise.race([viewer.scene.sampleHeightMostDetailed([carto]), timeout]);
      const h = out?.[0]?.height;
      return Number.isFinite(h) ? h : null;
    } catch (_) {
      return null;
    }
  }

  async function tryCesium(token) {
    const Cesium = window.Cesium;
    Cesium.Ion.defaultAccessToken = token;
    if ("default" in Cesium.Ellipsoid) Cesium.Ellipsoid.default = Cesium.Ellipsoid.MOON; // per D-7d58

    const container = $("cesiumContainer");
    container.hidden = false;
    let viewer = null;
    try {
      viewer = new Cesium.Viewer(container, {
        globe: false, // the Moon tileset is the only terrain; no Earth globe or imagery underneath
        baseLayer: false,
        skyAtmosphere: false,
        animation: false,
        timeline: false,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        fullscreenButton: false,
        vrButton: false,
        infoBox: false,
        selectionIndicator: false,
        scene3DOnly: true,
      });
      // Cesium's own Sun and Moon would contradict our site×time geometry.
      if (viewer.scene.sun) viewer.scene.sun.show = false;
      if (viewer.scene.moon) viewer.scene.moon.show = false;

      const tileset = await Cesium.Cesium3DTileset.fromIonAssetId(CESIUM_MOON_ION_ASSET, {
        enableCollision: true,
        maximumScreenSpaceError: 6, // sharper near ground from a 2 m eye
      });
      // Polar imagery has its shadows baked in and reads almost black from 2 m; lift the albedo
      // so the backdrop is legible. Visual context only (D-671e) — this is not a photometric model.
      tileset.customShader = new Cesium.CustomShader({
        uniforms: { u_gain: { type: Cesium.UniformType.FLOAT, value: 1.6 } },
        fragmentShaderText: `
          void fragmentMain(FragmentInput fsInput, inout czm_modelMaterial material) {
            material.diffuse = clamp(pow(material.diffuse, vec3(0.6)) * u_gain + 0.05, 0.0, 1.0);
          }
        `,
      });
      viewer.scene.primitives.add(tileset);
      state.viewer = viewer;

      const lat = Number(state.data.mask?.lat ?? state.lat);
      const lon = Number(state.data.mask?.lon ?? state.lon);
      const ground = await terrainHeight(viewer, lon, lat);
      const origin = Cesium.Cartesian3.fromDegrees(lon, lat, (ground ?? 0) + OBSERVER_HEIGHT_M, Cesium.Ellipsoid.MOON);
      state.cesium = {
        origin,
        enu: Cesium.Transforms.eastNorthUpToFixedFrame(origin, Cesium.Ellipsoid.MOON),
      };
      if (ground === null) {
        showNotice(["Terrain height at the site could not be sampled; the eye point sits 2 m above the reference sphere, so it may float or clip."]);
      }

      installLookControls(viewer);
      buildCesiumOverlays();
      state.mode = "cesium";
      updateCesiumSky();

      // Start facing the Sun if it clears our mask, else the Earth, else north.
      const s = state.data.sky[state.skyIndex];
      if (s && bodyState(s.sun_az_deg, s.sun_el_deg).visible) face(s.sun_az_deg, 4);
      else if (s && bodyState(s.earth_az_deg, s.earth_el_deg).visible) face(s.earth_az_deg, 4);
      else applyLook();

      $("mode-tag").textContent = "Cesium Moon backdrop + our mask & sky";
      $("provenance-oneliner").textContent = "Backdrop: Cesium Moon — not our model"; // per D-671e
      $("look-readout").hidden = false;
      for (const [id, az, el] of [["face-sun", "sun_az_deg", "sun_el_deg"], ["face-earth", "earth_az_deg", "earth_el_deg"]]) {
        $(id).hidden = false;
        $(id).addEventListener("click", () => {
          const now = state.data.sky[state.skyIndex];
          if (now) face(now[az], now[el]);
        });
      }
      return true;
    } catch (e) {
      console.warn("Cesium Moon backdrop failed:", e);
      if (viewer && !viewer.isDestroyed()) viewer.destroy();
      state.viewer = null;
      state.cesium = null;
      container.hidden = true;
      showNotice(["Cesium could not start the Moon backdrop (" + (e?.message || e) + "). Showing the 2D mask panorama."]);
      return false;
    }
  }

  /* ---------- 2D mask panorama (per D-ac74) ---------- */

  function drawFallback2D() {
    const data = state.data;
    const canvas = $("fallback-canvas");
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    if (!data || !W || !H) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

    const pad = { l: 52, r: 20, t: 34, b: 46 };
    const pw = W - pad.l - pad.r;
    const ph = H - pad.t - pad.b;
    const elev = data.mask.elevation_deg;
    const all = data.sky.flatMap((s) => [s.sun_el_deg, s.earth_el_deg]);
    const elMin = Math.max(-10, Math.min(-2, Math.floor(Math.min(...all) - 0.5)));
    const elMax = Math.min(60, Math.max(6, Math.ceil(Math.max(...all, ...elev) + 1)));
    const toX = (az) => pad.l + (az / 360) * pw;
    const toY = (el) => pad.t + ph - ((Math.max(elMin, Math.min(el, elMax)) - elMin) / (elMax - elMin)) * ph;

    ctx.fillStyle = "#111418";
    ctx.fillRect(0, 0, W, H);

    // Grid + axes
    const span = elMax - elMin;
    const step = span > 30 ? 10 : span > 14 ? 4 : 2;
    ctx.lineWidth = 1;
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    for (let el = Math.ceil(elMin / step) * step; el <= elMax; el += step) {
      const y = Math.round(toY(el)) + 0.5;
      ctx.strokeStyle = el === 0 ? "#5f6b7c" : "#2f343c";
      ctx.beginPath();
      ctx.moveTo(pad.l, y);
      ctx.lineTo(pad.l + pw, y);
      ctx.stroke();
      ctx.fillStyle = "#abb3bf";
      ctx.fillText(`${el}°`, pad.l - 8, y);
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let az = 0; az <= 360; az += 45) {
      const x = Math.round(toX(az)) + 0.5;
      ctx.strokeStyle = "#2f343c";
      ctx.beginPath();
      ctx.moveTo(x, pad.t);
      ctx.lineTo(x, pad.t + ph);
      ctx.stroke();
      ctx.fillStyle = az % 90 === 0 ? "#f6f7f9" : "#abb3bf";
      ctx.fillText(`${COMPASS[(az / 45) % 8]} ${az}°`, x, pad.t + ph + 8);
    }
    ctx.fillStyle = "#abb3bf";
    ctx.fillText("Azimuth (from north, clockwise)", pad.l + pw / 2, pad.t + ph + 26);
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    ctx.fillText("Elevation · our horizon mask, with Sun and Earth tracks over the window", pad.l, pad.t - 12);

    // Our mask silhouette: everything under the line is terrain.
    ctx.beginPath();
    ctx.moveTo(toX(0), pad.t + ph);
    for (let i = 0; i <= elev.length; i++) ctx.lineTo(toX((i * 360) / elev.length), toY(elev[i % elev.length]));
    ctx.lineTo(toX(360), pad.t + ph);
    ctx.closePath();
    ctx.fillStyle = MASK_FILL;
    ctx.fill();
    ctx.beginPath();
    for (let i = 0; i <= elev.length; i++) {
      const x = toX((i * 360) / elev.length);
      const y = toY(elev[i % elev.length]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = MASK_LINE;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Tracks over the window, broken where azimuth wraps.
    function track(azKey, elKey, color) {
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.6;
      ctx.beginPath();
      let prev = null;
      for (const s of data.sky) {
        const x = toX(s[azKey]);
        const y = toY(s[elKey]);
        if (prev === null || Math.abs(s[azKey] - prev) > 180) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        prev = s[azKey];
      }
      ctx.stroke();
      for (const s of data.sky) {
        ctx.beginPath();
        ctx.arc(toX(s[azKey]), toY(s[elKey]), 2, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }
    track("earth_az_deg", "earth_el_deg", EARTH);
    track("sun_az_deg", "sun_el_deg", SUN);

    // Bodies at the selected time: solid when clear of our mask, hollow when behind it.
    function body(az, el, color, name, r) {
      const x = toX(az);
      const y = toY(el);
      const visible = bodyState(az, el).visible;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = visible ? color : "#111418";
      ctx.fill();
      ctx.strokeStyle = visible ? "#111418" : color;
      ctx.lineWidth = 2;
      ctx.stroke();
      const text = visible ? name : `${name} (behind mask)`;
      const tw = ctx.measureText(text).width;
      const right = x + r + 8 + tw < pad.l + pw;
      const tx = right ? x + r + 8 : x - r - 8 - tw;
      const ty = Math.max(pad.t + 12, y - r - 6);
      ctx.fillStyle = "rgba(28, 33, 39, 0.9)";
      ctx.fillRect(tx - 4, ty - 12, tw + 8, 17);
      ctx.fillStyle = color;
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(text, tx, ty);
    }
    const s = data.sky[state.skyIndex];
    if (s) {
      body(s.earth_az_deg, s.earth_el_deg, EARTH, "Earth", 7);
      body(s.sun_az_deg, s.sun_el_deg, SUN, "Sun", 8);
    }
  }

  function showFallback() {
    $("fallback-canvas").hidden = false;
    $("mode-tag").textContent = "2D mask panorama";
    $("provenance-oneliner").textContent = "No backdrop — our mask and sky geometry only";
    state.mode = "fallback";
    drawFallback2D();
    new ResizeObserver(() => drawFallback2D()).observe($("stage"));
  }

  async function main() {
    const params = parseQuery();
    state.data = await fetchSiteData();
    state.skyIndex = skyIndexForStart(state.data, params);
    setupChrome(state.data, params);

    // per D-7d58 / D-ac74: no token, no ion asset or a failed start → 2D panorama
    const token = getIonToken(params);
    let ok = false;
    if (!token) {
      showNotice(["No Cesium ion token saved, so there is no 3D backdrop. Showing the 2D mask panorama."]);
    } else if (!window.Cesium) {
      showNotice(["CesiumJS could not be loaded (offline?). Showing the 2D mask panorama."]);
    } else {
      const probe = await probeIon(token);
      if (probe === "ok") ok = await tryCesium(token);
      else showNotice(ION_NOTICES[probe]);
    }
    if (!ok) showFallback();
  }

  main();
})();
