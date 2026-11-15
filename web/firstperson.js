/* S10 first-person view — lunar-eval */

(function () {
  const OBSERVER_HEIGHT_M = 2; // per D-f2d3
  const CESIUM_MOON_ION_ASSET = 2684829; // per D-7d58
  const HORIZON_DISTANCE_M = 8000;
  const MARKER_DISTANCE_M = 12000;

  /** @type {{ viewer?: import('cesium').Viewer, overlay?: { mask?: object, sun?: object, earth?: object } }} */
  const state = {
    data: null,
    skyIndex: 0,
    mode: "loading",
    viewer: null,
    queryForSite: "",
    queryForBack: "",
    lat: -89.46316,
    lon: 222.51045,
  };

  function parseQuery() {
    // per D-e062: same query string as S8 horizon planner
    const p = new URLSearchParams(window.location.search);
    if (p.has("lat")) state.lat = Number(p.get("lat"));
    if (p.has("lon")) state.lon = Number(p.get("lon"));
    const back = new URLSearchParams(p);
    back.delete("ion_token");
    state.queryForBack = back.toString();
    const site = new URLSearchParams(p);
    site.delete("ion_token");
    state.queryForSite = site.toString();
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
    // per D-3832: inline mock shaped like api mock
    const t0 = new Date("2026-06-21T00:00:00Z");
    const mask_elev = [];
    for (let i = 0; i < 720; i++) {
      const az = i * 0.5;
      let h = 1.6 + 0.85 * Math.sin((az * 2.17 * Math.PI) / 180);
      if (az > 145 && az < 235) {
        h += 2.8 * Math.exp(-((az - 192) ** 2) / 180);
      }
      mask_elev.push(Math.round(h * 1e4) / 1e4);
    }
    const maskAt = (azDeg) => mask_elev[Math.round(azDeg * 2) % 720];

    const sky = [];
    const sun_frac = [];
    const earth_frac = [];
    for (let hr = 0; hr < 24; hr++) {
      const ts = new Date(t0.getTime() + hr * 3600000);
      const sun_az = ((hr / 24) * 360 + 12) % 360;
      const sun_el = -2.4 + 4.8 * Math.max(0, Math.sin(((hr - 6) * 15 * Math.PI) / 180));
      const earth_az = (sun_az + 118) % 360;
      const earth_el = 4.5 + 3.2 * Math.sin(((hr * 18 - 40) * Math.PI) / 180);
      sky.push({
        time_utc: ts.toISOString().replace(".000Z", "Z"),
        sun_az_deg: Math.round(sun_az * 100) / 100,
        sun_el_deg: Math.round(sun_el * 1000) / 1000,
        earth_az_deg: Math.round(earth_az * 100) / 100,
        earth_el_deg: Math.round(earth_el * 1000) / 1000,
      });
      sun_frac.push(sun_el > maskAt(sun_az) ? 1 : 0);
      earth_frac.push(earth_el > 0.5 ? 1 : 0);
    }

    return {
      data_source: "mock",
      mask: {
        elevation_deg: mask_elev,
        schedule_version: "inline-mock",
        lat: state.lat,
        lon: state.lon,
      },
      sky,
      series: { sun_fraction: sun_frac, earth_fraction: earth_frac },
      score: { feasible: true, score: 0.5, provenance: { score_formula: "mock", schedule_version: "inline" } },
      hazards_enabled: false,
      needs: {},
    };
  }

  async function fetchSiteData() {
    const status = document.getElementById("load-status");
    const q = state.queryForSite;
    try {
      const res = await fetch("/site?" + q);
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.detail?.message || body.detail?.error || res.statusText);
      }
      status.textContent = body.data_source === "real" ? "Live site data" : "Mock site data";
      return body;
    } catch (e) {
      status.className = "err";
      status.textContent = "Site fetch failed — using inline mock (" + e.message + ")";
      return mockSitePayload();
    }
  }

  function skyIndexForStart(data, params) {
    const start = params.get("start");
    if (!start || !data.sky?.length) return 0;
    const want = toUtcIso(start);
    const idx = data.sky.findIndex((s) => s.time_utc === want || s.time_utc.startsWith(want.replace(/:00Z$/, "")));
    if (idx >= 0) return idx;
    const tWant = Date.parse(want);
    if (Number.isNaN(tWant)) return 0;
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

  function setupChrome(data) {
    const back = document.getElementById("back-link");
    back.href = "index.html?" + state.queryForBack;

    const meta = document.getElementById("site-meta");
    const mlat = data.mask?.lat ?? state.lat;
    const mlon = data.mask?.lon ?? state.lon;
    meta.textContent = `Site ${Number(mlat).toFixed(5)}°, ${Number(mlon).toFixed(5)}° · observer ${OBSERVER_HEIGHT_M} m · ${data.sky.length} sky samples`;

    const scrub = document.getElementById("hour-scrub");
    const range = document.getElementById("hour-range");
    const out = document.getElementById("hour-label");
    if (data.sky.length > 1) {
      scrub.hidden = false;
      range.min = "0";
      range.max = String(data.sky.length - 1);
      range.value = String(state.skyIndex);
    } else {
      scrub.hidden = true;
    }
    range.oninput = () => {
      state.skyIndex = Number(range.value);
      updateHourLabel(data, out);
      refreshOverlays();
    };
    updateHourLabel(data, out);
  }

  function updateHourLabel(data, out) {
    const s = data.sky[state.skyIndex];
    out.textContent = s ? s.time_utc : "—";
  }

  function setModeTag(text) {
    document.getElementById("mode-tag").textContent = text;
  }

  function hideCesiumCredits(viewer) {
    const el = viewer?.cesiumWidget?.creditContainer;
    if (el) el.style.display = "none";
  }

  /**
   * Local ENU offset from azimuth (deg from north, clockwise) and elevation deg.
   */
  function enuOffset(azDeg, elDeg, distM) {
    const az = (azDeg * Math.PI) / 180;
    const el = (elDeg * Math.PI) / 180;
    const cosEl = Math.cos(el);
    const east = distM * cosEl * Math.sin(az);
    const north = distM * cosEl * Math.cos(az);
    const up = distM * Math.sin(el);
    return { east, north, up };
  }

  function worldPointFromAzEl(viewer, origin, azDeg, elDeg, distM) {
    const Cesium = window.Cesium;
    const off = enuOffset(azDeg, elDeg, distM);
    const local = new Cesium.Cartesian3(off.east, off.north, off.up);
    const transform = Cesium.Transforms.eastNorthUpToFixedFrame(origin, viewer.scene.globe.ellipsoid);
    return Cesium.Matrix4.multiplyByPoint(transform, local, new Cesium.Cartesian3());
  }

  function buildHorizonPositions(viewer, origin, elevation_deg) {
    const Cesium = window.Cesium;
    const positions = [];
    for (let i = 0; i < elevation_deg.length; i++) {
      const az = i * 0.5;
      const el = elevation_deg[i];
      positions.push(worldPointFromAzEl(viewer, origin, az, el, HORIZON_DISTANCE_M));
    }
    positions.push(positions[0]);
    return positions;
  }

  function refreshCesiumOverlays() {
    const viewer = state.viewer;
    const data = state.data;
    if (!viewer || !data) return;
    const Cesium = window.Cesium;

    const lat = data.mask?.lat ?? state.lat;
    const lon = data.mask?.lon ?? state.lon;
    const origin = Cesium.Cartesian3.fromDegrees(
      lon,
      lat,
      OBSERVER_HEIGHT_M,
      viewer.scene.globe.ellipsoid
    );

    const coll = viewer.entities;
    coll.removeAll();

    const maskPts = buildHorizonPositions(viewer, origin, data.mask.elevation_deg);
    coll.add({
      name: "horizon-mask", // per D-ac34 hybrid: our mask on Cesium backdrop
      polyline: {
        positions: maskPts,
        width: 3,
        material: Cesium.Color.fromCssColorString("#c4b8a8").withAlpha(0.95),
        clampToGround: false,
      },
    });

    const fill = maskPts.slice(0, -1).concat([origin]);
    coll.add({
      name: "horizon-fill",
      polygon: {
        hierarchy: fill,
        material: Cesium.Color.fromCssColorString("#6b6370").withAlpha(0.35),
        perPositionHeight: true,
      },
    });

    const sky = data.sky[state.skyIndex];
    if (sky) {
      const sunPos = worldPointFromAzEl(viewer, origin, sky.sun_az_deg, sky.sun_el_deg, MARKER_DISTANCE_M);
      const earthPos = worldPointFromAzEl(viewer, origin, sky.earth_az_deg, sky.earth_el_deg, MARKER_DISTANCE_M);
      coll.add({
        name: "sun",
        position: sunPos,
        point: {
          pixelSize: 14,
          color: Cesium.Color.fromCssColorString("#c9a227"),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 1,
        },
        label: {
          text: "Sun (ours)",
          font: "12px IBM Plex Mono",
          fillColor: Cesium.Color.fromCssColorString("#c9a227"),
          pixelOffset: new Cesium.Cartesian2(0, -18),
          showBackground: true,
          backgroundColor: Cesium.Color.fromCssColorString("#1a1c22").withAlpha(0.75),
        },
      });
      coll.add({
        name: "earth",
        position: earthPos,
        point: {
          pixelSize: 11,
          color: Cesium.Color.fromCssColorString("#6a8faa"),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 1,
        },
        label: {
          text: "Earth (ours)",
          font: "12px IBM Plex Mono",
          fillColor: Cesium.Color.fromCssColorString("#6a8faa"),
          pixelOffset: new Cesium.Cartesian2(0, -18),
          showBackground: true,
          backgroundColor: Cesium.Color.fromCssColorString("#1a1c22").withAlpha(0.75),
        },
      });
    }
  }

  function constrainLookAround(viewer) {
    // per D-f2d3: yaw/pitch look-around, no drone flight
    const Cesium = window.Cesium;
    const ctrl = viewer.scene.screenSpaceCameraController;
    ctrl.enableTranslate = false;
    ctrl.enableZoom = false;
    ctrl.enableTilt = true;
    ctrl.enableLook = true;
    ctrl.enableRotate = true;
    ctrl.minimumZoomDistance = 0.5;
    ctrl.maximumZoomDistance = 500000;
    const minPitch = Cesium.Math.toRadians(-12);
    const maxPitch = Cesium.Math.toRadians(72);
    ctrl.minimumPitchAngle = minPitch;
    ctrl.maximumPitchAngle = maxPitch;
  }

  let Cesium; // eslint-friendly ref set in tryCesium

  async function tryCesium(token, data) {
    Cesium = window.Cesium;
    if (!Cesium || !token) {
      return false;
    }

    Cesium.Ion.defaultAccessToken = token;

    const container = document.getElementById("cesiumContainer");
    const viewer = new Cesium.Viewer(container, {
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
      globe: new Cesium.Globe(Cesium.Ellipsoid.MOON), // per D-7d58 Moon ellipsoid
      terrainProvider: undefined,
    });
    hideCesiumCredits(viewer);
    state.viewer = viewer;

    const lat = data.mask?.lat ?? state.lat;
    const lon = data.mask?.lon ?? state.lon;
    const dest = Cesium.Cartesian3.fromDegrees(lon, lat, OBSERVER_HEIGHT_M, Cesium.Ellipsoid.MOON);

    try {
      const tileset = await Cesium.Cesium3DTileset.fromIonAssetId(CESIUM_MOON_ION_ASSET);
      viewer.scene.primitives.add(tileset);
    } catch (e) {
      viewer.destroy();
      state.viewer = null;
      console.warn("Cesium Moon tileset failed:", e);
      return false;
    }

    viewer.camera.setView({
      destination: dest,
      orientation: {
        heading: 0,
        pitch: Cesium.Math.toRadians(-5),
        roll: 0,
      },
    });
    constrainLookAround(viewer);

    document.getElementById("cesiumContainer").setAttribute("aria-hidden", "false");
    setModeTag("Cesium Moon backdrop + our mask/sky");
    state.mode = "cesium";
    refreshCesiumOverlays();
    return true;
  }

  function resizeFallbackCanvas() {
    const canvas = document.getElementById("fallback-canvas");
    const wrap = document.getElementById("fallback-wrap");
    if (!wrap.classList.contains("active")) return;
    const dpr = window.devicePixelRatio || 1;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
  }

  function drawFallback2D() {
    // per D-ac74: 2D mask panorama on canvas
    const data = state.data;
    if (!data) return;
    resizeFallbackCanvas();
    const canvas = document.getElementById("fallback-canvas");
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.width;
    const H = canvas.height;
    const pad = { l: 48 * dpr, r: 16 * dpr, t: 16 * dpr, b: 40 * dpr };
    const plotW = W - pad.l - pad.r;
    const plotH = H - pad.t - pad.b;

    ctx.fillStyle = "#1a1c22";
    ctx.fillRect(0, 0, W, H);

    const elMax = 12;
    const elev = data.mask.elevation_deg;
    const toX = (az) => pad.l + (az / 360) * plotW;
    const toY = (el) => pad.t + plotH - (Math.max(0, Math.min(el, elMax)) / elMax) * plotH;

    ctx.strokeStyle = "#3f4556";
    ctx.lineWidth = 1;
    ctx.font = `${10 * dpr}px "IBM Plex Mono", monospace`;
    ctx.fillStyle = "#5c6378";
    for (let el = 0; el <= elMax; el += 4) {
      const y = toY(el);
      ctx.beginPath();
      ctx.moveTo(pad.l, y);
      ctx.lineTo(pad.l + plotW, y);
      ctx.stroke();
      ctx.fillText(el + "°", 4 * dpr, y + 3 * dpr);
    }
    ["N 0°", "E 90°", "S 180°", "W 270°"].forEach((lab, i) => {
      const x = toX(i * 90);
      ctx.fillText(lab, x - 12 * dpr, H - 8 * dpr);
    });

    ctx.beginPath();
    ctx.moveTo(toX(0), toY(0));
    for (let i = 0; i < elev.length; i++) {
      ctx.lineTo(toX(i * 0.5), toY(elev[i]));
    }
    ctx.lineTo(toX(360), toY(0));
    ctx.closePath();
    ctx.fillStyle = "rgba(107, 99, 112, 0.85)";
    ctx.fill();
    ctx.strokeStyle = "#c4b8a8";
    ctx.lineWidth = 2 * dpr;
    ctx.stroke();

    const sky = data.sky[state.skyIndex];
    if (sky) {
      function dot(az, el, color, label) {
        const x = toX(az);
        const y = toY(el);
        ctx.beginPath();
        ctx.arc(x, y, 6 * dpr, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = "#1a1c22";
        ctx.lineWidth = 1.5 * dpr;
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.fillText(label, x + 8 * dpr, y - 8 * dpr);
      }
      dot(sky.sun_az_deg, sky.sun_el_deg, "#c9a227", "Sun");
      dot(sky.earth_az_deg, sky.earth_el_deg, "#6a8faa", "Earth");
    }

    ctx.fillStyle = "#8b93a8";
    ctx.font = `${11 * dpr}px "Libre Franklin", sans-serif`;
    ctx.fillText("Azimuth 0–360° (filled silhouette = our horizon mask)", pad.l, pad.t - 4 * dpr);
  }

  function showFallback() {
    // per D-ac74
    document.getElementById("cesiumContainer").style.display = "none";
    const wrap = document.getElementById("fallback-wrap");
    wrap.classList.add("active");
    setModeTag("2D mask panorama (no Cesium)");
    state.mode = "fallback";
    drawFallback2D();
  }

  function refreshOverlays() {
    const range = document.getElementById("hour-range");
    if (range && state.data?.sky?.length > 1) {
      range.value = String(state.skyIndex);
    }
    if (state.data) updateHourLabel(state.data, document.getElementById("hour-label"));
    if (state.mode === "cesium") refreshCesiumOverlays();
    else if (state.mode === "fallback") drawFallback2D();
  }

  async function main() {
    const params = parseQuery();
    document.getElementById("back-link").href = "index.html?" + state.queryForBack;

    const data = await fetchSiteData();
    state.data = data;
    state.skyIndex = skyIndexForStart(data, params);
    setupChrome(data);

    const token = getIonToken(params);
    let cesiumOk = false;
    // per D-7d58 / D-ac74: no token or failed tileset → 2D fallback
    if (token) {
      cesiumOk = await tryCesium(token, data);
    }

    if (!cesiumOk) {
      if (state.viewer) {
        state.viewer.destroy();
        state.viewer = null;
      }
      showFallback();
    }

    window.addEventListener("resize", () => {
      if (state.mode === "fallback") drawFallback2D();
    });
  }

  main();
})();