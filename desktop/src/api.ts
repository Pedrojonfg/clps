import type { MissionTemplate, PlannerForm, RegionSearchSummary, SitePayload } from "./types";

/** Static browser demo (GitHub Pages): no API; reads JSON exported from the API's mock mode. */
export const STATIC_DEMO = import.meta.env.VITE_STATIC_DEMO === "1";
const BASE = import.meta.env.BASE_URL;

function toUtcIso(localValue: string): string {
  if (!localValue) return "";
  return `${localValue}:00Z`;
}

export function buildSiteQuery(form: PlannerForm): string {
  const p = new URLSearchParams();
  p.set("lat", form.lat);
  p.set("lon", form.lon);
  p.set("start", toUtcIso(form.start));
  p.set("end", toUtcIso(form.end));
  p.set("step_h", form.step_h);
  if (form.template_id) {
    p.set("template_id", form.template_id);
  } else {
    p.set("max_night_h", form.max_night_h);
    p.set("max_no_earth_h", form.max_no_earth_h);
    p.set("min_continuous_lit_h", form.min_continuous_lit_h);
    p.set("require_both", form.require_both ? "true" : "false");
    p.set("sun_lit_percent", form.sun_lit_percent);
    p.set("earth_lit_percent", form.earth_lit_percent);
    p.set("bridge_h", form.bridge_h);
  }
  p.set("hazards_enabled", form.hazards_enabled ? "true" : "false");
  if (form.local_search) p.set("local_search", "1");
  if (form.mock) p.set("mock", "1");
  return p.toString();
}

export async function fetchTemplates(): Promise<MissionTemplate[]> {
  const res = await fetch(STATIC_DEMO ? `${BASE}demo/mission-templates.json` : "/mission-templates");
  if (!res.ok) throw new Error(`templates HTTP ${res.status}`);
  const body = (await res.json()) as { templates: MissionTemplate[] };
  return body.templates ?? [];
}

export async function fetchSite(form: PlannerForm): Promise<SitePayload> {
  // ponytail: the API's mock ignores the form too, so one exported payload is faithful.
  const res = await fetch(
    STATIC_DEMO ? `${BASE}demo/site-mock.json` : `/site?${buildSiteQuery(form)}`,
  );
  const body = await res.json();
  if (!res.ok) {
    const msg =
      body?.detail?.message || body?.detail?.error || body?.detail || res.statusText;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return body as SitePayload;
}

/** Same-origin URLs via Vite proxy — localStorage ion token is shared with the iframe. */
export function firstPersonUrl(form: PlannerForm): string {
  const p = new URLSearchParams(buildSiteQuery(form));
  if (STATIC_DEMO) p.set("static", "1");
  return `${BASE}firstperson.html?${p.toString()}`;
}

export function regionMapUrl(form: PlannerForm, demo = false): string {
  const p = new URLSearchParams(buildSiteQuery(form));
  if (demo || STATIC_DEMO) p.set("demo", "1");
  if (STATIC_DEMO) p.set("static", "1");
  return `${BASE}map.html?${p.toString()}`;
}

/** Key the embedded region map (web/map.js) reads its last search from. */
const REGION_MAP_REQUEST_KEY = "clps:regionMapRequest";

type DeepRow = {
  site: { lat_deg: number; lon_deg: number };
  feasible: boolean;
  score: number;
  companion_score: number;
};

/**
 * Deep search over a lat/lon rectangle for the planner's time window, then hand the evaluated
 * rows to the region map (D-85bf: paint what the search evaluated; induce only when partial).
 */
export async function runRegionSearch(
  form: PlannerForm,
  rect: { lat_min: string; lat_max: string; lon_min: string; lon_max: string },
  mode: "optimized" | "total_coverage",
): Promise<RegionSearchSummary> {
  const start = toUtcIso(form.start);
  const end = toUtcIso(form.end);
  const hours = Math.floor((Date.parse(end) - Date.parse(start)) / 3_600_000);
  if (!Number.isFinite(hours) || hours < 1) throw new Error("The time window must span at least 1 h.");
  const window_hours = Math.min(hours, 168);
  const nums = Object.values(rect).map(Number);
  if (nums.some((n) => !Number.isFinite(n))) throw new Error("The rectangle needs four numbers.");

  const res = await fetch("/deep-search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode,
      lat_min: Number(rect.lat_min),
      lat_max: Number(rect.lat_max),
      lon_min: Number(rect.lon_min),
      lon_max: Number(rect.lon_max),
      start,
      end,
      window_hours,
      template_id: form.template_id || null,
    }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = body?.detail;
    throw new Error(d?.message || (typeof d === "string" ? d : res.statusText));
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
  localStorage.setItem(
    REGION_MAP_REQUEST_KEY,
    JSON.stringify({
      rows,
      search_partial: body.mode !== "total_coverage",
      best,
      label: body.mode === "total_coverage" ? "Total coverage" : "Optimized search",
    }),
  );
  return {
    rows_evaluated: body.rows_evaluated,
    n_sites: body.n_sites,
    runtime_s: body.runtime_s,
    claim: body.claim,
    provisional: Boolean(body.provisional),
    window_start: start.replace(":00Z", "Z").replace("T", " "),
    window_hours,
  };
}
