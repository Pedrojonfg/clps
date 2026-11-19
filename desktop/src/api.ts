import {
  energyOn,
  type DeepSearchRequest,
  type MissionTemplate,
  type PlannerForm,
  type RegionSearchSummary,
  type SearchWarning,
  type SitePayload,
} from "./types";

/** Static browser demo (GitHub Pages): no API; reads JSON exported from the API's mock mode. */
export const STATIC_DEMO = import.meta.env.VITE_STATIC_DEMO === "1";
const BASE = import.meta.env.BASE_URL;
/**
 * Origin of the evaluator API: the engine the desktop app bundles (set at startup), or a build-time
 * `VITE_API_BASE`. Empty = same origin, i.e. the Vite dev proxy to a local API.
 */
export let API_BASE = ((import.meta.env.VITE_API_BASE as string | undefined) ?? "").replace(/\/$/, "");
/** Set once at startup by the Tauri shell to the bundled engine's loopback origin. */
export function setApiBase(origin: string): void {
  API_BASE = origin.replace(/\/$/, "");
}
export const apiUrl = (path: string) => `${API_BASE}${path}`;

function toUtcIso(localValue: string): string {
  if (!localValue) return "";
  return `${localValue}:00Z`;
}

/** Readable text for the three 422 shapes: string, FastAPI list, {error, field, message}. */
export function errorText(detail: unknown, fallback = "Request failed"): string {
  if (typeof detail === "string") return detail || fallback;
  if (Array.isArray(detail)) {
    const parts = detail.map((d) => {
      const loc = Array.isArray(d?.loc) ? d.loc.filter((x: unknown) => x !== "query" && x !== "body").join(".") : "";
      const msg = typeof d?.msg === "string" ? d.msg : typeof d === "string" ? d : "invalid value";
      return loc ? `${loc}: ${msg}` : msg;
    });
    return parts.join("; ") || fallback;
  }
  if (detail && typeof detail === "object") {
    const d = detail as { message?: unknown; error?: unknown; field?: unknown };
    const msg = typeof d.message === "string" ? d.message : typeof d.error === "string" ? d.error : "";
    if (msg) return typeof d.field === "string" && !msg.includes(d.field) ? `${d.field}: ${msg}` : msg;
  }
  return fallback;
}

/** The app covers the south polar cap only (lat -90 .. -60); returns a message when the latitude is outside it. */
export function latitudeProblem(lat: string): string | null {
  const v = Number(lat);
  if (lat.trim() === "" || !Number.isFinite(v)) return null;
  if (v > -60) return "The app covers the south polar cap only (latitude between -90 and -60).";
  if (v < -90) return "Latitude cannot be below -90.";
  return null;
}

/** Schedule fields GET /site and POST /deep-search both validate: integer ones and the 0..max ranges. */
const REQUIREMENT_RULES: { key: RequirementKey; label: string; int: boolean; max?: number }[] = [
  { key: "max_night_h", label: "Night limit", int: true },
  { key: "max_no_earth_h", label: "No-Earth gap limit", int: true },
  { key: "min_continuous_lit_h", label: "Min light in a row", int: true },
  { key: "sun_lit_percent", label: "Sun lit %", int: false, max: 100 },
  { key: "earth_lit_percent", label: "Earth lit %", int: false, max: 100 },
  { key: "bridge_h", label: "Shadow bridge", int: true, max: 48 },
];
export type RequirementKey =
  | "max_night_h"
  | "max_no_earth_h"
  | "min_continuous_lit_h"
  | "sun_lit_percent"
  | "earth_lit_percent"
  | "bridge_h";

/**
 * Problems with the schedule fields, by field (empty object = all valid). Each is required (no silent
 * template or server default), a number >= 0, whole hours where the API takes an integer, and within
 * the API range. Shared by the planner form, fetchSite and requirementFields so /site and /deep-search
 * reject exactly the same input with the same message.
 */
export function requirementProblems(form: PlannerForm): Partial<Record<RequirementKey, string>> {
  const out: Partial<Record<RequirementKey, string>> = {};
  for (const r of REQUIREMENT_RULES) {
    const raw = String(form[r.key] ?? "").trim();
    const v = Number(raw);
    if (raw === "") out[r.key] = "Required: enter a number.";
    else if (!Number.isFinite(v)) out[r.key] = "Enter a number.";
    else if (v < 0) out[r.key] = "Cannot be negative.";
    else if (r.int && !Number.isInteger(v)) out[r.key] = "Whole hours only (no decimals).";
    else if (r.max !== undefined && v > r.max) out[r.key] = `At most ${r.max}.`;
  }
  return out;
}

/** Throws one readable message when any schedule field is invalid (see requirementProblems). */
export function assertRequirements(form: PlannerForm): void {
  const probs = requirementProblems(form);
  const lines = REQUIREMENT_RULES.filter((r) => probs[r.key]).map((r) => `${r.label}: ${probs[r.key]}`);
  if (lines.length) throw new Error(`Fix the mission needs first. ${lines.join(" ")}`);
}

/**
 * GET /site query for the form. A pure serializer (also used for iframe URLs and change detection),
 * so it never throws: fetchSite validates first with assertRequirements, like requirementFields does
 * for /deep-search. Values are sent as typed, never replaced by a default.
 */
export function buildSiteQuery(form: PlannerForm): string {
  const p = new URLSearchParams();
  p.set("lat", form.lat);
  p.set("lon", form.lon);
  p.set("start", toUtcIso(form.start));
  p.set("end", toUtcIso(form.end));
  p.set("step_min", form.step_min || "10");
  // Always send every schedule field (D-20261118-pj-70ec); template_id only while the form still matches
  // it exactly (PlannerScreen keeps form.template_id in sync, "" = Custom).
  if (form.template_id) p.set("template_id", form.template_id);
  // Same numbers requirementFields sends ("10.0" -> "10"); an invalid value is sent as typed (the
  // engine answers 422), never replaced by a default.
  const num = (v: string) => (v.trim() !== "" && Number.isFinite(Number(v)) ? String(Number(v)) : v);
  p.set("max_night_h", num(form.max_night_h));
  p.set("max_no_earth_h", num(form.max_no_earth_h));
  p.set("min_continuous_lit_h", num(form.min_continuous_lit_h));
  p.set("require_both", form.require_both ? "true" : "false");
  p.set("sun_lit_percent", num(form.sun_lit_percent));
  p.set("earth_lit_percent", num(form.earth_lit_percent));
  p.set("bridge_h", num(form.bridge_h));
  if (Number(form.min_total_lit_h) > 0) p.set("min_total_lit_h", form.min_total_lit_h);
  // Energy mode only when tier 1 is complete; the rest are optional refinements (D-20261117-pj-7b2d).
  if (energyOn(form)) {
    p.set("battery_wh", form.battery_wh);
    p.set("array_w", form.array_w);
    if (Number(form.dark_w) > 0) p.set("dark_w", form.dark_w);
    else p.set("endurance_h", form.endurance_h);
    p.set("panel", form.panel || "tracking_vertical");
    if (form.panel === "fixed_vertical") p.set("panel_az_deg", form.panel_az_deg || "0");
    if (form.lit_w !== "") p.set("lit_w", form.lit_w);
    if (form.reserve_pct !== "") p.set("reserve_pct", form.reserve_pct);
    if (form.charge_eff !== "") p.set("charge_eff", form.charge_eff);
  }
  // Always explicit: an empty value switches that limit off (D-20261117-pj-0c5e).
  p.set("max_temperature_k", form.max_temperature_k ?? "320");
  p.set("min_temperature_k", form.min_temperature_k ?? "");
  p.set("min_soil_resistance", form.min_soil_resistance ?? "0");
  p.set("hazards_enabled", form.hazards_enabled ? "true" : "false");
  if (form.local_search) p.set("local_search", "1");
  if (form.mock) p.set("mock", "1");
  return p.toString();
}

export type DownloadProgress = {
  active: boolean;
  file: string | null;
  done: number;
  total: number;
  files_done: number;
  bytes_done: number;
};

/** Data-store download in flight on the engine; null when unavailable (demo, old engine). */
export async function fetchProgress(): Promise<DownloadProgress | null> {
  if (STATIC_DEMO) return null;
  try {
    const res = await fetch(apiUrl("/progress"));
    return res.ok ? ((await res.json()) as DownloadProgress) : null;
  } catch {
    return null;
  }
}

/** Data version the engine serves now (GET /store-status `version`); null when unknown or on any failure. */
export async function fetchStoreVersion(): Promise<string | null> {
  if (STATIC_DEMO) return null;
  try {
    const res = await fetch(apiUrl("/store-status"));
    if (!res.ok) return null;
    const v = ((await res.json()) as { version?: unknown })?.version;
    return typeof v === "string" && v ? v : null;
  } catch {
    return null;
  }
}

export async function fetchTemplates(): Promise<MissionTemplate[]> {
  const res = await fetch(STATIC_DEMO ? `${BASE}demo/mission-templates.json` : apiUrl("/mission-templates"));
  if (!res.ok) throw new Error(`templates HTTP ${res.status}`);
  const body = (await res.json()) as { templates: MissionTemplate[] };
  return body.templates ?? [];
}

export async function fetchSite(form: PlannerForm, signal?: AbortSignal): Promise<SitePayload> {
  assertRequirements(form);
  // ponytail: the API's mock ignores the form too, so one exported payload is faithful.
  const res = await fetch(
    STATIC_DEMO ? `${BASE}demo/site-mock.json` : apiUrl(`/site?${buildSiteQuery(form)}`),
    { signal },
  );
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(errorText(body?.detail, res.statusText));
  // The exported demo payload always carries the local search; the API only adds it when asked,
  // so drop it here when "Single window" is selected and the mode toggle behaves the same.
  if (STATIC_DEMO && !form.local_search) delete body.local_search;
  return body as SitePayload;
}

/** Same-origin URLs via Vite proxy — localStorage ion token is shared with the iframe. */
export function firstPersonUrl(form: PlannerForm, mode2d = false, preferIon = false): string {
  const p = new URLSearchParams(buildSiteQuery(form));
  if (STATIC_DEMO) p.set("static", "1");
  if (API_BASE) p.set("api", API_BASE);
  if (mode2d) p.set("mode", "2d");
  if (preferIon) p.set("terrain", "ion");
  return `${BASE}firstperson.html?${p.toString()}`;
}

export function regionMapUrl(form: PlannerForm, demo = false, moon = false): string {
  const p = new URLSearchParams(buildSiteQuery(form));
  if (demo || STATIC_DEMO) p.set("demo", "1");
  if (moon) p.set("moon", "1");
  if (STATIC_DEMO) p.set("static", "1");
  if (API_BASE) p.set("api", API_BASE);
  return `${BASE}map.html?${p.toString()}`;
}

/** Key the embedded region map (web/map.js) reads its last search from. */
const REGION_MAP_REQUEST_KEY = "moonpark:regionMapRequest";

type DeepRow = {
  site: { lat_deg: number; lon_deg: number };
  feasible: boolean;
  score: number;
  companion_score: number;
};

/**
 * The user's requirements as /deep-search JSON fields: the same fields, rules and names as
 * buildSiteQuery sends to GET /site, read from the same planner form (D-20261118-pj-75f1).
 * Throws on the same invalid input fetchSite rejects (assertRequirements): no silent defaults.
 */
export function requirementFields(form: PlannerForm): Record<string, unknown> {
  assertRequirements(form);
  const out: Record<string, unknown> = {
    template_id: form.template_id || null,
    max_night_h: Number(form.max_night_h),
    max_no_earth_h: Number(form.max_no_earth_h),
    min_continuous_lit_h: Number(form.min_continuous_lit_h),
    require_both: form.require_both,
    sun_lit_percent: Number(form.sun_lit_percent),
    earth_lit_percent: Number(form.earth_lit_percent),
    bridge_h: Number(form.bridge_h),
    min_total_lit_h: Number(form.min_total_lit_h) > 0 ? Number(form.min_total_lit_h) : 0,
    // Always explicit: an empty value switches that limit off (D-20261117-pj-0c5e).
    max_temperature_k: form.max_temperature_k ?? "320",
    min_temperature_k: form.min_temperature_k ?? "",
    min_soil_resistance: form.min_soil_resistance ?? "0",
    hazards_enabled: form.hazards_enabled,
  };
  if (energyOn(form)) {
    out.battery_wh = Number(form.battery_wh);
    out.array_w = Number(form.array_w);
    if (Number(form.dark_w) > 0) out.dark_w = Number(form.dark_w);
    else out.endurance_h = Number(form.endurance_h);
    out.panel = form.panel || "tracking_vertical";
    if (form.panel === "fixed_vertical") out.panel_az_deg = Number(form.panel_az_deg || "0");
    if (form.lit_w !== "") out.lit_w = Number(form.lit_w);
    if (form.reserve_pct !== "") out.reserve_pct = Number(form.reserve_pct);
    if (form.charge_eff !== "") out.charge_eff = Number(form.charge_eff);
  }
  return out;
}

/** Validate the rectangle/window and build the /deep-search body from the planner form. */
export function buildDeepSearchRequest(
  form: PlannerForm,
  rect: { lat_min: string; lat_max: string; lon_min: string; lon_max: string },
  mode: "optimized" | "total_coverage",
  mock = false,
  stepMin = 60,
): DeepSearchRequest {
  const start = toUtcIso(form.start);
  const end = toUtcIso(form.end);
  const hours = Math.floor((Date.parse(end) - Date.parse(start)) / 3_600_000);
  if (!Number.isFinite(hours) || hours < 1) throw new Error("The time window must span at least 1 h.");
  const nums = Object.values(rect).map(Number);
  if (Object.values(rect).some((v) => v.trim() === "") || nums.some((n) => !Number.isFinite(n))) {
    throw new Error("The rectangle needs four numbers.");
  }
  // Coverage is the one hard limit (D-20261118-pj-cd33); the server answers 422 too.
  const latMsg = latitudeProblem(rect.lat_max) ?? latitudeProblem(rect.lat_min);
  if (latMsg) throw new Error(latMsg);
  return {
    ...requirementFields(form),
    mode,
    lat_min: Number(rect.lat_min),
    lat_max: Number(rect.lat_max),
    lon_min: Number(rect.lon_min),
    lon_max: Number(rect.lon_max),
    start,
    end,
    window_hours: Math.min(hours, 168),
    step_min: stepMin,
    mock,
    hazards_enabled: form.hazards_enabled,
  };
}

/** Ask the engine to stop a running search (D-20261118-pj-1454); true when the job was found and told to stop. */
export async function stopRegionSearch(jobId: string): Promise<boolean> {
  const res = await fetch(apiUrl("/deep-search/stop"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(errorText(body?.detail, res.statusText));
  return Boolean(body?.stopped);
}

/** Hand evaluated rows to the embedded region map (web/map.js reads this key). */
export function storeRegionMapRows(summary: RegionSearchSummary): void {
  const label =
    (summary.mock ? "MOCK · " : "") +
    (summary.request.mode === "total_coverage" ? "Total coverage" : "Optimized search") +
    (summary.state === "stopped" ? " · stopped" : "");
  try {
    localStorage.setItem(
      REGION_MAP_REQUEST_KEY,
      JSON.stringify({
        rows: summary.rows,
        search_partial: summary.state === "stopped" || summary.request.mode !== "total_coverage",
        best: summary.best,
        label,
      }),
    );
  } catch {
    /* storage full or blocked: the map then shows its previous result */
  }
}

/**
 * Deep search over a lat/lon rectangle for the planner's time window, then hand the evaluated
 * rows to the region map (D-85bf: paint what the search evaluated; induce only when partial).
 * `jobId` lets POST /deep-search/stop halt it; `resume` continues a stopped run (D-20261118-pj-1454).
 */
export async function runRegionSearch(
  request: DeepSearchRequest,
  opts: { jobId?: string; resume?: Record<string, unknown> | null; signal?: AbortSignal } = {},
): Promise<RegionSearchSummary> {
  const res = await fetch(apiUrl("/deep-search"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...request, job_id: opts.jobId ?? null, resume: opts.resume ?? null }),
    signal: opts.signal,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(errorText(body?.detail, res.statusText));
  }
  const rows = ((body.export_rows ?? []) as DeepRow[]).map((r) => ({
    lat_deg: r.site.lat_deg,
    lon_deg: r.site.lon_deg,
    score: r.score,
    feasible: r.feasible,
    companion_score: r.companion_score,
  }));
  const best = body.best?.site
    ? { lat_deg: body.best.site.lat_deg, lon_deg: body.best.site.lon_deg }
    : null;
  const warnings = (Array.isArray(body.warnings) ? body.warnings : [])
    .filter((w: unknown): w is SearchWarning => !!w && typeof (w as SearchWarning).message === "string")
    .map((w: SearchWarning) => ({ ...w, code: String(w.code ?? "") }));
  const summary: RegionSearchSummary = {
    rows_evaluated: Number(body.rows_evaluated ?? rows.length),
    n_sites: Number(body.n_sites ?? 0),
    runtime_s: Number(body.runtime_s ?? 0),
    claim: String(body.claim ?? ""),
    provisional: Boolean(body.provisional),
    mock: body.data_source === "mock",
    window_start: request.start.replace(":00Z", "Z").replace("T", " "),
    window_hours: request.window_hours,
    requirements: body.requirements && typeof body.requirements === "object" ? body.requirements : null,
    warnings,
    dropped_cells: Number(body.dropped_cells ?? 0) || 0,
    state: body.state === "stopped" ? "stopped" : "complete",
    checkpoint: body.checkpoint && typeof body.checkpoint === "object" ? body.checkpoint : null,
    request,
    rows,
    best,
  };
  storeRegionMapRows(summary);
  return summary;
}
