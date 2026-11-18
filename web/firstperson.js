/* S10 first-person view — moonpark
 * D-ac34 hybrid (third-party backdrop + our mask/sky), D-7d58 CesiumJS + Cesium Moon,
 * D-f2d3 2 m observer / look-around only, D-e062 same site×time query as the planner,
 * D-671e provenance one-liner + details, D-ac74 2D mask panorama when Cesium is unavailable.
 * 2026-11-16: D-26d2 playback + follow, D-7304 brightness follows our Sun-disc fraction,
 * D-08e8 Earth-link indicator (chips, compass strip, time strip), D-ce2e max backdrop quality,
 * D-b43a mask azimuth convention.
 * 2026-11-18: default backdrop is our own LOLA relief from the API's /terrain (no token);
 * the Cesium ion Moon tileset stays as an opt-in (?terrain=ion) and as the fallback when
 * the API has no DEM for the site.
 */

(function () {
  const OBSERVER_HEIGHT_M = 2; // per D-f2d3
  const CESIUM_MOON_ION_ASSET = 2684829; // per D-7d58
  const FAR_RING_M = 250000; // outer edge of the own-relief mesh: where our mask's DEM schedule ends
  const OVERLAY_DISTANCE_M = 20000; // our mask/sky are directions; drawn on a far shell, never depth-hidden
  const SUN = "#c9a227";
  const EARTH = "#6a8faa";
  const MASK_LINE = "#c4b8a8";
  const MASK_FILL = "#4a4650";
  const PITCH_MIN = -25;
  const PITCH_MAX = 70;
  const SUN_RADIUS_DEG = 0.2665;
  const EARTH_RADIUS_DEG = 0.95;
  const NIGHT_FLOOR = 0.07; // per D-7304
  const RELIEF_LIGHT_EL_DEG = 20; // cosmetic: true polar sun is too grazing for relief to read
  const OK = "#72ca9b";
  const BAD = "#fa999c";

  const EMBEDDED = window.parent !== window;
  // Hosted API origin passed by the app (?api=https://…); empty = same origin (dev proxy / local API).
  const API_BASE = (new URLSearchParams(window.location.search).get("api") || "").replace(/\/$/, "");
  const $ = (id) => document.getElementById(id);

  const state = {
    data: null,
    t: 0, // fractional index into data.sky; playback interpolates between samples (D-26d2)
    playing: false,
    speed: 2, // hours of window per second
    follow: "off", // off | sun | earth
    now: null, // interpolated sky at t
    mode: "loading",
    viewer: null,
    query: "",
    lat: -89.46316,
    lon: 222.51045,
    look: { heading: 0, pitch: 4, fov: 60 },
    cesium: null, // { origin, enu, sun, earth }
    battery: null, // { kind: soc | autonomy, values, reserve }
  };

  function parseQuery() {
    // per D-e062: same query string as the S8 horizon planner
    const p = new URLSearchParams(window.location.search);
    if (p.has("lat")) state.lat = Number(p.get("lat"));
    if (p.has("lon")) state.lon = Number(p.get("lon"));
    const q = new URLSearchParams(p);
    q.delete("ion_token");
    q.delete("api");
    q.delete("mode");
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
      // Built directly in geographic azimuth, unlike API masks (D-b43a).
      mask: { elevation_deg: mask_elev, azimuth_zero_deg: 0, azimuth_sign: 1, lat: state.lat, lon: state.lon },
      sky,
    };
  }

  async function fetchSiteData() {
    const status = $("load-status");
    try {
      // ?static=1 → browser demo without API: the exported mock payload.
      const isStatic = new URLSearchParams(state.query).get("static") === "1";
      const res = await fetch(isStatic ? "demo/site-mock.json" : API_BASE + "/site?" + state.query);
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

  /** Horizon elevation at a geographic azimuth; the array has its own azimuth (D-b43a). */
  function maskAt(azDeg) {
    const m = state.data.mask;
    const el = m.elevation_deg;
    const n = el.length;
    const zero = m.azimuth_zero_deg ?? 180;
    const sign = m.azimuth_sign ?? -1;
    const idxAz = (((sign * (azDeg - zero)) % 360) + 360) % 360;
    const f = (idxAz / 360) * n;
    const i = Math.floor(f) % n;
    const t = f - Math.floor(f);
    return el[i] * (1 - t) + el[(i + 1) % n] * t;
  }

  /** Visible fraction of a disc of the given radius whose centre is `clearDeg` above the mask. */
  function discFraction(clearDeg, radiusDeg) {
    const x = Math.max(-1, Math.min(1, clearDeg / radiusDeg));
    return 1 - (Math.acos(x) - x * Math.sqrt(1 - x * x)) / Math.PI;
  }

  /** Per-sample fractions: the planner's own series when present, else from mask and sky. */
  function fractionsFor(i) {
    const d = state.data;
    const s = d.sky[i];
    const sf = d.series?.sun_fraction?.[i];
    const ef = d.series?.earth_fraction?.[i];
    return {
      sun: Number.isFinite(sf) ? sf : discFraction(s.sun_el_deg - maskAt(s.sun_az_deg), SUN_RADIUS_DEG),
      earth: Number.isFinite(ef) ? ef : discFraction(s.earth_el_deg - maskAt(s.earth_az_deg), EARTH_RADIUS_DEG),
    };
  }

  function thresholds() {
    const n = state.data.needs || {};
    return { sun: Number(n.sun_lit_threshold ?? 0), earth: Number(n.earth_lit_threshold ?? 0) };
  }

  function lerpAz(a, b, f) {
    const d = ((b - a + 540) % 360) - 180; // shortest way round
    return (((a + d * f) % 360) + 360) % 360;
  }

  /** Sky at fractional index t: linear between the hourly samples the planner scored (D-26d2). */
  function skyAt(t) {
    const sky = state.data.sky;
    const i0 = Math.max(0, Math.min(sky.length - 1, Math.floor(t)));
    const i1 = Math.min(sky.length - 1, i0 + 1);
    const f = Math.max(0, Math.min(1, t - i0));
    const a = sky[i0];
    const b = sky[i1];
    const fa = fractionsFor(i0);
    const fb = fractionsFor(i1);
    const thr = thresholds();
    const sunFrac = fa.sun + (fb.sun - fa.sun) * f;
    const earthFrac = fa.earth + (fb.earth - fa.earth) * f;
    const ms = Date.parse(a.time_utc) + (Date.parse(b.time_utc) - Date.parse(a.time_utc)) * f;
    return {
      timeMs: ms,
      sunAz: lerpAz(a.sun_az_deg, b.sun_az_deg, f),
      sunEl: a.sun_el_deg + (b.sun_el_deg - a.sun_el_deg) * f,
      earthAz: lerpAz(a.earth_az_deg, b.earth_az_deg, f),
      earthEl: a.earth_el_deg + (b.earth_el_deg - a.earth_el_deg) * f,
      sunFrac,
      earthFrac,
      sunLit: sunFrac > thr.sun,
      earthLink: earthFrac > thr.earth,
    };
  }

  const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  function compass(azDeg) {
    return COMPASS[Math.round((((azDeg % 360) + 360) % 360) / 45) % 8];
  }

  function pctText(frac) {
    if (frac >= 0.999) return "full disc";
    if (frac <= 0.001) return "hidden";
    return `${Math.round(frac * 100)} % of disc`;
  }

  function bodyText(az, el, frac) {
    return `${el.toFixed(1)}° el · az ${az.toFixed(0)}° ${compass(az)} · ${pctText(frac)}`;
  }

  function fmtTimeMs(ms) {
    return new Date(ms).toISOString().slice(0, 16).replace("T", " ") + " UTC";
  }

  /**
   * Battery readout (D-20261117-pj-7b2d). With the energy model the planner sends the state of charge;
   * without it we show an autonomy estimate relative to the user's "Max night" (dark run vs that limit,
   * refilled by any light) and say so, never a % of a real battery.
   */
  function buildBattery(data) {
    const soc = data.series?.soc;
    const needs = data.needs || {};
    if (Array.isArray(soc) && soc.length === data.sky.length) {
      return { kind: "soc", values: soc, reserve: Number(needs.reserve_pct ?? 10) / 100 };
    }
    const maxNight = Number(needs.max_night_h);
    const sf = data.series?.sun_fraction;
    if (!Array.isArray(sf) || !(maxNight > 0)) return null;
    const stepH = (Number(data.series?.step_min) || 60) / 60;
    const thr = thresholds();
    let run = 0;
    const values = sf.map((f) => {
      run = f > thr.sun ? 0 : run + stepH;
      return Math.max(0, 1 - run / maxNight);
    });
    return { kind: "autonomy", values, reserve: 0 };
  }

  function updateBattery(t) {
    const b = state.battery;
    const box = $("battery");
    if (!b) {
      box.hidden = true;
      return;
    }
    const v = b.values;
    const i0 = Math.max(0, Math.min(v.length - 1, Math.floor(t)));
    const i1 = Math.min(v.length - 1, i0 + 1);
    const frac = Math.max(0, Math.min(1, v[i0] + (v[i1] - v[i0]) * Math.max(0, Math.min(1, t - i0))));
    const pct = Math.round(frac * 100);
    box.hidden = false;
    $("battery-fill").setAttribute("width", String(14.5 * frac));
    $("battery-text").textContent = b.kind === "soc" ? `${pct} %` : `~${pct} % autonomy`;
    box.classList.toggle("bad", frac < b.reserve || (b.kind === "autonomy" && frac <= 0));
    box.classList.toggle("warn", !box.classList.contains("bad") && frac < b.reserve + 0.1);
    box.title =
      b.kind === "soc"
        ? `Estimated battery state of charge from your capacity, array and load. Reserve ${Math.round(b.reserve * 100)} %.`
        : "Estimated autonomy: time in darkness relative to your Max night, refilled by any light. Not a battery model — add battery data in the planner for that.";
  }

  function updateReadouts() {
    const n = state.now;
    if (!n) return;
    updateBattery(state.t);
    $("hour-label").textContent = fmtTimeMs(n.timeMs);
    $("sun-state").textContent = bodyText(n.sunAz, n.sunEl, n.sunFrac);
    $("earth-state").textContent = bodyText(n.earthAz, n.earthEl, n.earthFrac);
  }

  /** Strip under the slider (one cell per sample): Sun-disc fraction and Earth link over the window. */
  function drawTimeStrip() {
    const c = $("time-strip");
    const W = c.clientWidth;
    const H = c.clientHeight;
    if (!W || !H) return;
    const dpr = window.devicePixelRatio || 1;
    c.width = Math.round(W * dpr);
    c.height = Math.round(H * dpr);
    const ctx = c.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = state.data.sky.length;
    const thr = thresholds();
    const pad = 8; // range thumb half-width, so cells line up with thumb positions
    const cw = (W - 2 * pad) / Math.max(1, n - 1);
    const rowH = (H - 3) / 2;
    for (let i = 0; i < n; i++) {
      const f = fractionsFor(i);
      const x = pad + (i - 0.5) * cw;
      ctx.fillStyle = "#2f343c";
      ctx.fillRect(x, 0, cw + 0.5, rowH);
      ctx.fillRect(x, rowH + 3, cw + 0.5, rowH);
      ctx.globalAlpha = Math.max(0, Math.min(1, f.sun));
      ctx.fillStyle = SUN;
      ctx.fillRect(x, 0, cw + 0.5, rowH);
      ctx.globalAlpha = f.earth > thr.earth ? 0.35 + 0.65 * f.earth : 0;
      ctx.fillStyle = EARTH;
      ctx.fillRect(x, rowH + 3, cw + 0.5, rowH);
      ctx.globalAlpha = 1;
    }
    const x = pad + state.t * cw;
    ctx.fillStyle = "#f6f7f9";
    ctx.fillRect(x - 1, 0, 2, H);
  }

  function setTime(t, fromSlider) {
    const max = state.data.sky.length - 1;
    state.t = Math.max(0, Math.min(max, t));
    state.now = skyAt(state.t);
    if (!fromSlider) $("hour-range").value = String(state.t);
    refresh();
  }

  function setPlaying(on) {
    state.playing = on && state.data.sky.length > 1;
    const b = $("play-toggle");
    b.textContent = state.playing ? "❚❚ Pause" : "▶ Play";
    b.setAttribute("aria-pressed", String(state.playing));
  }

  function setFollow(which) {
    state.follow = which;
    $("follow-select").value = which;
  }

  let lastFrame = null;
  function playbackTick(now) {
    requestAnimationFrame(playbackTick);
    const dt = lastFrame === null ? 0 : Math.min(0.1, (now - lastFrame) / 1000);
    lastFrame = now;
    if (!state.data) return;
    if (state.playing) {
      const sky = state.data.sky;
      const stepH = (Date.parse(sky[1].time_utc) - Date.parse(sky[0].time_utc)) / 3_600_000 || 1;
      let t = state.t + (dt * state.speed) / stepH;
      if (t >= sky.length - 1) t = 0; // loop
      setTime(t, false);
    }
    if (state.mode === "cesium") {
      if (state.follow !== "off" && state.now) {
        const n = state.now;
        state.look.heading = state.follow === "sun" ? n.sunAz : n.earthAz;
        state.look.pitch = Math.min(PITCH_MAX, Math.max(4, state.follow === "sun" ? n.sunEl : n.earthEl));
        applyLook();
      }
      drawCompass();
      const ts = state.cesium?.tileset;
      $("terrain-loading").hidden = !ts || ts.tilesLoaded;
    }
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
      range.step = "any";
      range.value = String(state.t);
    }
    range.addEventListener("input", () => {
      setPlaying(false);
      setTime(Number(range.value), true);
    });
    $("play-toggle").addEventListener("click", () => setPlaying(!state.playing));
    $("speed-select").addEventListener("change", (ev) => {
      state.speed = Number(ev.target.value) || 2;
    });
    $("follow-select").addEventListener("change", (ev) => setFollow(ev.target.value));
    window.addEventListener("keydown", (ev) => {
      if (ev.code !== "Space" || /^(INPUT|SELECT|BUTTON|TEXTAREA)$/.test(ev.target.tagName)) return;
      ev.preventDefault();
      setPlaying(!state.playing);
    });
    new ResizeObserver(() => drawTimeStrip()).observe($("time-strip"));

    const toggle = $("details-toggle");
    toggle.addEventListener("click", () => {
      const open = $("details").hidden;
      $("details").hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
    });
    state.battery = buildBattery(data);
    state.now = skyAt(state.t);
    updateReadouts();
    drawTimeStrip();
    requestAnimationFrame(playbackTick);
  }

  function refresh() {
    updateReadouts();
    drawTimeStrip();
    if (state.mode === "cesium") updateCesiumSky();
    else if (state.mode === "fallback") drawFallback2D();
  }

  /** per D-08e8: where the Sun and the Earth are relative to the current heading. */
  function drawCompass() {
    const c = $("compass");
    const W = c.clientWidth;
    const H = c.clientHeight;
    const n = state.now;
    if (!W || !H || !n) return;
    const dpr = window.devicePixelRatio || 1;
    if (c.width !== Math.round(W * dpr)) {
      c.width = Math.round(W * dpr);
      c.height = Math.round(H * dpr);
    }
    const ctx = c.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const SPAN = 180; // degrees of heading across the strip
    const head = ((state.look.heading % 360) + 360) % 360;
    const rel = (az) => ((az - head + 540) % 360) - 180;
    const X = (az) => W / 2 + (rel(az) / SPAN) * W;
    ctx.font = "11px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    for (let az = 0; az < 360; az += 15) {
      const x = X(az);
      if (x < 4 || x > W - 4) continue;
      const major = az % 45 === 0;
      ctx.fillStyle = major ? "#abb3bf" : "#5f6b7c";
      ctx.fillRect(Math.round(x), H - (major ? 9 : 5), 1, major ? 9 : 5);
      if (major) {
        ctx.fillStyle = az % 90 === 0 ? "#f6f7f9" : "#abb3bf";
        ctx.fillText(COMPASS[az / 45], x, H - 12);
      }
    }
    ctx.fillStyle = "#f6f7f9";
    ctx.beginPath();
    ctx.moveTo(W / 2 - 5, 0);
    ctx.lineTo(W / 2 + 5, 0);
    ctx.lineTo(W / 2, 6);
    ctx.fill();

    const body = (az, color, on, letter) => {
      const r = rel(az);
      const off = Math.abs(r) > SPAN / 2 - 4;
      const x = off ? (r < 0 ? 12 : W - 12) : X(az);
      const y = 12;
      ctx.beginPath();
      ctx.arc(x, y, 6.5, 0, Math.PI * 2);
      ctx.fillStyle = on ? color : "#1c2127";
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
      if (!on) {
        ctx.beginPath();
        ctx.moveTo(x - 5, y + 5);
        ctx.lineTo(x + 5, y - 5);
        ctx.stroke();
      }
      ctx.fillStyle = "#f6f7f9";
      ctx.textAlign = off ? (r < 0 ? "left" : "right") : "left";
      const label = off ? (r < 0 ? `◀ ${letter}` : `${letter} ▶`) : letter;
      ctx.fillText(label, off ? (r < 0 ? x + 10 : x - 10) : x + 10, y + 4);
      ctx.textAlign = "center";
    };
    body(n.earthAz, EARTH, n.earthLink, "Earth");
    body(n.sunAz, SUN, n.sunLit, "Sun");
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
      setFollow("off"); // manual look-around wins over follow (D-26d2)
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
      setFollow("off");
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
    const ring = [];
    for (let az = 0; az < 360; az += 0.5) ring.push(dirToWorld(az, maskAt(az), OVERLAY_DISTANCE_M));
    ring.push(ring[0]);
    line(ring, MASK_LINE, 2.5, 0.95);

    ["N", "E", "S", "W"].forEach((name, i) => {
      ents.add({
        position: dirToWorld(i * 90, maskAt(i * 90) + 3, OVERLAY_DISTANCE_M),
        label: { ...labelStyle(name, "#abb3bf"), pixelOffset: new Cesium.Cartesian2(0, 0) },
      });
    });

    for (const seg of trackSegments("sun_az_deg", "sun_el_deg")) line(seg, SUN, 1.5, 0.55);
    for (const seg of trackSegments("earth_az_deg", "earth_el_deg")) line(seg, EARTH, 1.5, 0.55);

    // Soft glow so the Sun reads as a light source; scaled by the visible fraction.
    const glow = document.createElement("canvas");
    glow.width = glow.height = 128;
    const g = glow.getContext("2d");
    const grad = g.createRadialGradient(64, 64, 2, 64, 64, 64);
    grad.addColorStop(0, "rgba(255, 244, 200, 0.9)");
    grad.addColorStop(0.25, "rgba(255, 220, 120, 0.35)");
    grad.addColorStop(1, "rgba(255, 200, 80, 0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, 128, 128);

    const marker = (css, size, withGlow) =>
      ents.add({
        position: state.cesium.origin,
        point: {
          pixelSize: size,
          color: Cesium.Color.fromCssColorString(css),
          outlineColor: Cesium.Color.fromCssColorString("#111418"),
          outlineWidth: 2,
          disableDepthTestDistance: always,
        },
        billboard: withGlow ? { image: glow, disableDepthTestDistance: always } : undefined,
        label: labelStyle("", css),
      });
    state.cesium.sun = marker("#fff1b8", 14, true);
    state.cesium.earth = marker(EARTH, 13, false);
    state.cesium.light = new Cesium.DirectionalLight({ direction: new Cesium.Cartesian3(0, 0, -1), intensity: 3.0 });
    state.viewer.scene.light = state.cesium.light;
  }

  function updateCesiumSky() {
    const Cesium = window.Cesium;
    const n = state.now;
    if (!n || !state.cesium) return;
    const put = (ent, name, az, el, frac, on, text) => {
      ent.position = dirToWorld(az, el, OVERLAY_DISTANCE_M);
      if (ent.label.text?.getValue?.() !== text) ent.label.text = text;
      ent.point.color = Cesium.Color.fromCssColorString(name === "Sun" ? "#fff1b8" : EARTH).withAlpha(on ? 0.4 + 0.6 * frac : 0.4);
      if (ent.billboard) {
        ent.billboard.scale = 0.4 + 1.4 * frac;
        ent.billboard.color = Cesium.Color.WHITE.withAlpha(frac);
      }
    };
    put(
      state.cesium.sun, "Sun", n.sunAz, n.sunEl, n.sunFrac, n.sunLit,
      n.sunFrac <= 0.001 ? "Sun · behind our mask" : n.sunFrac >= 0.999 ? "Sun · ours" : `Sun · ours · ${Math.round(n.sunFrac * 100)} % of disc`,
    );
    put(
      state.cesium.earth, "Earth", n.earthAz, n.earthEl, n.earthFrac, n.earthLink,
      n.earthLink ? "Earth · ours · link" : "Earth · ours · behind our mask",
    );

    // per D-7304: backdrop brightness follows OUR visible Sun-disc fraction, with a dim night
    // floor. Direction is our Sun azimuth at a fixed relief angle; no shadows are cast.
    try {
      const toSun = Cesium.Cartesian3.subtract(
        dirToWorld(n.sunAz, RELIEF_LIGHT_EL_DEG, 1000),
        state.cesium.origin,
        new Cesium.Cartesian3(),
      );
      Cesium.Cartesian3.normalize(Cesium.Cartesian3.negate(toSun, toSun), state.cesium.light.direction);
      state.cesium.shader?.setUniform("u_sun", NIGHT_FLOOR + (1 - NIGHT_FLOOR) * n.sunFrac);
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

  /** Our own relief for the site: the API computes it from the LOLA DEMs (static demo: demo/terrain.json). */
  async function fetchTerrain(lat, lon, params) {
    try {
      const isStatic = params.get("static") === "1";
      const url = isStatic ? "demo/terrain.json" : `${API_BASE}/terrain?lat=${lat}&lon=${lon}`;
      const res = await fetch(url);
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = body.detail?.message || body.detail?.error || res.statusText;
        return { data: null, why: `Our relief is not available for this site (${msg}).` };
      }
      return { data: body, why: "" };
    } catch (e) {
      return { data: null, why: `Our relief could not be loaded (${e.message}).` };
    }
  }

  /**
   * Mesh the ring-grid relief (radii × azimuths, heights above the site's tangent plane) in the
   * observer's east-north-up frame and add it to the scene. Returns an object with setUniform so
   * the Sun-fraction brightness (D-7304) drives it the same way as the ion tileset's shader.
   */
  function addTerrainMesh(viewer, terrain, enu) {
    const Cesium = window.Cesium;
    // Beyond the meshed 30 km the ground continues out to the horizon our mask already knows, so
    // one far ring follows the mask elevation: no black gap between the mesh and the mask line.
    // A centre point under the observer closes the hole inside the innermost ring (looking straight down).
    const radii = [0, ...terrain.radii_m, FAR_RING_M];
    const nr = radii.length;
    const naz = terrain.naz;
    const raw = atob(terrain.heights_f32_b64);
    const bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    const h0 = new Float32Array(bytes.buffer);
    const h = new Float32Array(nr * naz); // ring 0 is the centre point; the last ring is overwritten by farZ
    h.set(h0, naz);
    let centre = 0;
    for (let j = 0; j < naz; j++) centre += h0[j] / naz;
    h.fill(centre, 0, naz);
    const farZ = (j) => FAR_RING_M * Math.tan((maskAt((j * 360) / naz) * Math.PI) / 180);

    const pos = new Float64Array(nr * naz * 3);
    for (let i = 0; i < nr; i++) {
      for (let j = 0; j < naz; j++) {
        const az = (j * 2 * Math.PI) / naz;
        const k = (i * naz + j) * 3;
        pos[k] = radii[i] * Math.sin(az); // east
        pos[k + 1] = radii[i] * Math.cos(az); // north
        // the frame sits at the eye; the mask angle is already measured from it
        pos[k + 2] = i === nr - 1 ? farZ(j) : h[i * naz + j] - OBSERVER_HEIGHT_M;
      }
    }
    const idx = new Uint32Array((nr - 1) * naz * 6);
    let m = 0;
    for (let i = 0; i < nr - 1; i++) {
      for (let j = 0; j < naz; j++) {
        const a = i * naz + j;
        const b = i * naz + ((j + 1) % naz);
        const c = (i + 1) * naz + j;
        const d = (i + 1) * naz + ((j + 1) % naz);
        idx[m++] = a; idx[m++] = b; idx[m++] = c;
        idx[m++] = b; idx[m++] = d; idx[m++] = c;
      }
    }
    const st = new Float32Array(nr * naz * 2); // east/north metres: the procedural surface below keys on them
    for (let v = 0; v < nr * naz; v++) {
      st[v * 2] = pos[v * 3];
      st[v * 2 + 1] = pos[v * 3 + 1];
    }
    const nrm = new Float32Array(pos.length);
    for (let t = 0; t < idx.length; t += 3) {
      const ia = idx[t] * 3, ib = idx[t + 1] * 3, ic = idx[t + 2] * 3;
      const ux = pos[ib] - pos[ia], uy = pos[ib + 1] - pos[ia + 1], uz = pos[ib + 2] - pos[ia + 2];
      const vx = pos[ic] - pos[ia], vy = pos[ic + 1] - pos[ia + 1], vz = pos[ic + 2] - pos[ia + 2];
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      for (const k of [ia, ib, ic]) { nrm[k] += nx; nrm[k + 1] += ny; nrm[k + 2] += nz; }
    }
    for (let k = 0; k < nrm.length; k += 3) {
      const l = Math.hypot(nrm[k], nrm[k + 1], nrm[k + 2]) || 1;
      nrm[k] /= l; nrm[k + 1] /= l; nrm[k + 2] /= l;
    }

    const geometry = new Cesium.Geometry({
      attributes: {
        position: new Cesium.GeometryAttribute({ componentDatatype: Cesium.ComponentDatatype.DOUBLE, componentsPerAttribute: 3, values: pos }),
        normal: new Cesium.GeometryAttribute({ componentDatatype: Cesium.ComponentDatatype.FLOAT, componentsPerAttribute: 3, values: nrm }),
        st: new Cesium.GeometryAttribute({ componentDatatype: Cesium.ComponentDatatype.FLOAT, componentsPerAttribute: 2, values: st }),
      },
      indices: idx,
      primitiveType: Cesium.PrimitiveType.TRIANGLES,
      boundingSphere: Cesium.BoundingSphere.fromVertices(Array.from(pos)),
    });
    // Procedural regolith: we have no albedo imagery, so tone and grain are synthetic (and labelled
    // so). Grain is a screen-space bump on the normal, which the grazing Sun turns into texture;
    // it fades with distance so it never shimmers.
    const material = new Cesium.Material({
      fabric: {
        uniforms: { u_sun: 1.0 },
        source: `
          float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
          float vnoise(vec2 p) {
            vec2 i = floor(p), f = fract(p);
            f = f * f * (3.0 - 2.0 * f);
            return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
          }
          float fbm(vec2 p) {
            float a = 0.5, s = 0.0;
            for (int k = 0; k < 4; k++) { s += a * vnoise(p); p *= 2.03; a *= 0.5; }
            return s;
          }
          czm_material czm_getMaterial(czm_materialInput materialInput) {
            czm_material material = czm_getDefaultMaterial(materialInput);
            vec2 p = materialInput.st;
            vec3 pe = materialInput.positionToEyeEC;
            float dist = length(pe);
            float near = 1.0 - smoothstep(60.0, 700.0, dist);

            // Micro-relief in metres (hummocks and pits), faded with distance.
            float h = ((fbm(p / 0.9) - 0.5) * 0.6 + (fbm(p / 7.0) - 0.5) * 2.5) * near;
            vec3 n = normalize(materialInput.normalEC);
            vec3 dpdx = dFdx(pe), dpdy = dFdy(pe);
            vec3 r1 = cross(dpdy, n), r2 = cross(n, dpdx);
            float det = dot(dpdx, r1);
            vec3 grad = sign(det) * (dFdx(h) * r1 + dFdy(h) * r2);
            material.normal = normalize(abs(det) * n - grad);

            // Tone: slow patches of brighter and darker regolith plus a little grain.
            float tone = 0.72 + 0.55 * fbm(p / 60.0) + 0.18 * (fbm(p / 2.5) - 0.5) * near;
            vec3 tint = mix(vec3(0.72, 0.82, 1.0), vec3(1.0), u_sun);
            material.diffuse = vec3(0.31, 0.30, 0.285) * tone * tint * u_sun;
            material.specular = 0.0;
            return material;
          }
        `,
      },
    });
    viewer.scene.primitives.add(
      new Cesium.Primitive({
        geometryInstances: new Cesium.GeometryInstance({ geometry }),
        appearance: new Cesium.MaterialAppearance({ material, materialSupport: Cesium.MaterialAppearance.MaterialSupport.TEXTURED, translucent: false, closed: false }),
        modelMatrix: enu,
        asynchronous: false,
        compressVertices: false,
        allowPicking: false,
      }),
    );
    return { setUniform: (name, v) => { material.uniforms[name] = v; } };
  }

  async function tryCesium(source, token, terrain) {
    const Cesium = window.Cesium;
    if (source === "ion") Cesium.Ion.defaultAccessToken = token;
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
        // per D-ce2e: native device pixels (capped) and multisampling
        msaaSamples: 4,
        useBrowserRecommendedResolution: false,
      });
      viewer.resolutionScale = Math.min(window.devicePixelRatio || 1, 2);
      viewer.scene.postProcessStages.fxaa.enabled = false; // MSAA does the work; FXAA only blurs
      viewer.scene.highDynamicRange = false;
      // Cesium's own Sun and Moon would contradict our site×time geometry.
      if (viewer.scene.sun) viewer.scene.sun.show = false;
      if (viewer.scene.moon) viewer.scene.moon.show = false;

      let tileset = null;
      let shader = null;
      if (source === "ion") {
        tileset = await Cesium.Cesium3DTileset.fromIonAssetId(CESIUM_MOON_ION_ASSET, {
          enableCollision: true,
          // per D-ce2e: fine level of detail everywhere in view (no foveation), from a 2 m eye
          maximumScreenSpaceError: 2,
          dynamicScreenSpaceError: false,
          foveatedScreenSpaceError: false,
          skipLevelOfDetail: false,
          cacheBytes: 1024 * 1024 * 1024,
          maximumCacheOverflowBytes: 512 * 1024 * 1024,
        });
        // Polar imagery has its shadows baked in and reads almost black from 2 m; lift the albedo
        // a little so the backdrop is legible, then scale by our Sun-disc fraction (D-7304), with a
        // slightly cool tint toward night. Visual context only (D-671e) — not a photometric model.
        shader = new Cesium.CustomShader({
          uniforms: {
            u_gain: { type: Cesium.UniformType.FLOAT, value: 1.35 },
            u_sun: { type: Cesium.UniformType.FLOAT, value: 1.0 },
          },
          fragmentShaderText: `
            void fragmentMain(FragmentInput fsInput, inout czm_modelMaterial material) {
              vec3 lifted = clamp(pow(material.diffuse, vec3(0.75)) * u_gain + 0.03, 0.0, 1.0);
              vec3 tint = mix(vec3(0.72, 0.82, 1.0), vec3(1.0), u_sun);
              material.diffuse = lifted * tint * u_sun;
            }
          `,
        });
        tileset.customShader = shader;
        viewer.scene.primitives.add(tileset);
      }
      state.viewer = viewer;

      const lat = Number(state.data.mask?.lat ?? state.lat);
      const lon = Number(state.data.mask?.lon ?? state.lon);
      const ground = source === "own" ? terrain.ground_m : await terrainHeight(viewer, lon, lat);
      const origin = Cesium.Cartesian3.fromDegrees(lon, lat, (ground ?? 0) + OBSERVER_HEIGHT_M, Cesium.Ellipsoid.MOON);
      state.cesium = {
        origin,
        tileset,
        shader,
        enu: Cesium.Transforms.eastNorthUpToFixedFrame(origin, Cesium.Ellipsoid.MOON),
      };
      if (source === "own") {
        // No ion data is in view, so swap the "Cesium ion" logo for a plain, accurate credit.
        container.classList.add("own-credit");
        viewer.creditDisplay.addStaticCredit(
          new Cesium.Credit('Rendered with <a href="https://cesium.com/platform/cesiumjs/" target="_blank" rel="noreferrer">CesiumJS</a> · relief: NASA LRO / LOLA', true),
        );
        state.cesium.shader = addTerrainMesh(viewer, terrain, state.cesium.enu);
      }
      if (ground === null) {
        showNotice(["Terrain height at the site could not be sampled; the eye point sits 2 m above the reference sphere, so it may float or clip."]);
      }

      installLookControls(viewer);
      buildCesiumOverlays();
      state.mode = "cesium";
      updateCesiumSky();

      // Start facing the Sun if it clears our mask, else the Earth, else north.
      const n0 = state.now;
      if (n0 && n0.sunFrac > 0) face(n0.sunAz, 4);
      else if (n0 && n0.earthLink) face(n0.earthAz, 4);
      else applyLook();

      if (source === "own") {
        $("mode-tag").textContent = "Our LOLA relief + our mask & sky";
        $("provenance-oneliner").textContent = "Backdrop: our LOLA DEM relief, procedural surface"; // per D-671e
        $("prov-backdrop").innerHTML =
          "<strong>Ours (relief):</strong> the ground is meshed from the same LOLA elevation models the horizon mask comes from (" +
          terrain.dem.join(", ") +
          "), finest under the observer and coarser with distance, out to 30 km, and from there the ground simply follows our horizon mask. Its colour and grain are procedural, not imagery (we hold no albedo data), so it is visual context only: the mask, not the mesh, is what is scored.";
        $("prov-attrib").innerHTML = "<strong>Attribution:</strong> NASA LRO / LOLA (PGDA).";
      } else {
        $("mode-tag").textContent = "Cesium Moon backdrop + our mask & sky";
        $("provenance-oneliner").textContent = "Backdrop: Cesium Moon — not our model"; // per D-671e
      }
      $("look-readout").hidden = false;
      $("compass").hidden = false;
      $("follow-wrap").hidden = false;
      for (const [id, which] of [["face-sun", "sun"], ["face-earth", "earth"]]) {
        $(id).hidden = false;
        $(id).addEventListener("click", () => {
          const n = state.now;
          setFollow("off");
          if (n) face(which === "sun" ? n.sunAz : n.earthAz, which === "sun" ? n.sunEl : n.earthEl);
        });
      }
      return true;
    } catch (e) {
      console.warn("Cesium Moon backdrop failed:", e);
      if (viewer && !viewer.isDestroyed()) viewer.destroy();
      state.viewer = null;
      state.cesium = null;
      container.hidden = true;
      showNotice(["The 3D backdrop could not start (" + (e?.message || e) + ")."]);
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
    // per D-7304: the plot brightens with our visible Sun-disc fraction.
    const lit = state.now ? state.now.sunFrac : 0;
    ctx.fillStyle = `rgba(120, 140, 170, ${(0.16 * lit).toFixed(3)})`;
    ctx.fillRect(pad.l, pad.t, pw, ph);

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
    for (let az = 0; az <= 360; az += 0.5) ctx.lineTo(toX(az), toY(maskAt(az)));
    ctx.lineTo(toX(360), pad.t + ph);
    ctx.closePath();
    const shade = Math.round(40 + 70 * lit);
    ctx.fillStyle = `rgb(${shade + 8}, ${shade + 4}, ${shade + 12})`;
    ctx.fill();
    ctx.beginPath();
    for (let az = 0; az <= 360; az += 0.5) {
      const x = toX(az);
      const y = toY(maskAt(az));
      if (az === 0) ctx.moveTo(x, y);
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
    function body(az, el, color, text, visible, r) {
      const x = toX(az);
      const y = toY(el);
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = visible ? color : "#111418";
      ctx.fill();
      ctx.strokeStyle = visible ? "#111418" : color;
      ctx.lineWidth = 2;
      ctx.stroke();
      const tw = ctx.measureText(text).width;
      const right = x + r + 8 + tw < pad.l + pw;
      const tx = right ? x + r + 8 : x - r - 8 - tw;
      const ty = Math.max(pad.t + 12, y - r - 6);
      ctx.fillStyle = "rgba(28, 33, 39, 0.9)";
      ctx.fillRect(tx - 4, ty - 12, tw + 8, 17);
      ctx.fillStyle = "#f6f7f9";
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(text, tx, ty);
    }
    const n = state.now;
    if (n) {
      body(n.earthAz, n.earthEl, EARTH, n.earthLink ? "Earth · link" : "Earth · behind mask", n.earthLink, 7);
      body(n.sunAz, n.sunEl, SUN, `Sun · ${pctText(n.sunFrac)}`, n.sunFrac > 0.001, 8);
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
    state.t = skyIndexForStart(state.data, params);
    setupChrome(state.data, params);

    // Backdrop order: our own LOLA relief (no token) → Cesium ion Moon with a token → 2D panorama.
    // ?terrain=ion asks for the ion tileset first; it is also the fallback when the API has no DEM.
    const token = getIonToken(params);
    const preferIon = params.get("terrain") === "ion";
    let ok = false;
    if (params.get("mode") === "2d") {
      // The user chose the light 2D view (slow GPU): never start Cesium.
      showNotice(["2D view selected. Use “Switch to 3D” above for the 3D backdrop."]);
    } else if (!window.Cesium) {
      showNotice(["CesiumJS could not be loaded (offline?). Showing the 2D mask panorama."]);
    } else {
      const tryIon = async () => {
        const probe = await probeIon(token);
        if (probe === "ok") return tryCesium("ion", token, null);
        showNotice(ION_NOTICES[probe]);
        return false;
      };
      if (preferIon && token) ok = await tryIon();
      if (!ok && !(preferIon && token)) {
        const lat = Number(state.data.mask?.lat ?? state.lat);
        const lon = Number(state.data.mask?.lon ?? state.lon);
        const terrain = await fetchTerrain(lat, lon, params);
        if (terrain.data) ok = await tryCesium("own", "", terrain.data);
        else if (token) {
          showNotice([terrain.why + " Trying the Cesium ion Moon instead."]);
          ok = await tryIon();
        } else {
          showNotice([terrain.why + " Add a Cesium ion token for a 3D backdrop meanwhile; showing the 2D mask panorama."]);
        }
      }
    }
    if (!ok) showFallback();
  }

  main();
})();
