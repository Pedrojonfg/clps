import type { MissionTemplate, PlannerForm, SitePayload } from "./types";

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
