export type MissionTemplate = {
  id: string;
  label: string;
  description?: string;
  max_night_h: number;
  max_no_earth_h: number;
  min_continuous_lit_h?: number;
  min_total_lit_h?: number;
  sun_lit_percent: number;
  earth_lit_percent: number;
  bridge_h: number;
  require_both: boolean;
  max_temperature_k?: number | null;
  min_temperature_k?: number | null;
  min_soil_resistance?: number | null;
};

export type SiteProvenance = {
  engine_version?: string;
  formula_version?: string;
  effective_needs?: Record<string, unknown>;
  step_min?: number;
  observer_height_m?: number;
  data_version?: string | null;
  approximations?: string[];
  mask?: {
    requested_lat: number;
    requested_lon: number;
    lat: number;
    lon: number;
    distance_m: number;
    source: string;
  };
  fill?: { filled_pixels: number; out_of_coverage_samples: number } | null;
};

export type SitePayload = {
  data_source?: string;
  site?: { lat_deg: number; lon_deg: number; name?: string };
  mask: {
    elevation_deg: number[];
    /** geographic_az = azimuth_zero_deg + azimuth_sign × index_az (D-20261116-pj-b43a). */
    azimuth_zero_deg?: number;
    azimuth_sign?: number;
    lat?: number;
    lon?: number;
  };
  sky: Array<{
    time_utc: string;
    sun_az_deg: number;
    sun_el_deg: number;
    earth_az_deg: number;
    earth_el_deg: number;
  }>;
  series: {
    sun_fraction: number[];
    earth_fraction: number[];
    longest_night_h: number;
    longest_no_earth_h: number;
    longest_lit_h?: number;
    /** Pessimistic bounds (D-9413): the night / no-Earth gap is at least this, the lit run at most this. */
    longest_night_h_lower?: number;
    longest_no_earth_h_lower?: number;
    longest_lit_h_upper?: number;
    hours_sun_above_threshold?: number;
    hours_earth_above_threshold?: number;
    any_both?: boolean;
    /** Sample spacing in minutes (D-20261117-pj-91c6); the metrics above are in hours. */
    step_min?: number;
    /** Energy mode: state of charge per sample as a fraction of capacity, and its minimum. */
    soc?: number[];
    soc_min?: number;
  };
  needs: Record<string, number | boolean | undefined | string[]> & { not_evaluated?: string[] };
  hazards_status?: { status: string; unavailable: Record<string, string> };
  warnings?: Array<{ code: string; fields?: string[]; message: string }>;
  provenance?: SiteProvenance;
  score: {
    feasible: boolean;
    score: number;
    companion_score?: number;
    breakdown?: { failing?: string[] };
    provenance?: {
      score_formula?: string;
      schedule_version?: string;
      decisions?: string[];
      sigmas_h?: { night?: number; lit?: number; no_earth?: number };
    };
  };
  hazards_enabled?: boolean;
  hazards?: unknown;
  local_search?: {
    pick?: { window_start?: string; site?: { lat_deg: number } };
    leaderboard: Array<{
      window_start?: string;
      feasible: boolean;
      score: number;
      companion_score: number;
      distance_hours: number;
      distance_km: number;
      hazard_gap_star?: boolean;
      site?: { lat_deg: number };
    }>;
  };
};

export type PlannerForm = {
  lat: string;
  lon: string;
  start: string;
  end: string;
  /** Sample step in minutes: "10" fine, "60" coarse (D-20261117-pj-91c6). */
  step_min: string;
  template_id: string;
  max_night_h: string;
  max_no_earth_h: string;
  min_continuous_lit_h: string;
  /** Minimum total hours of light in the window; 0 = no requirement. */
  min_total_lit_h: string;
  sun_lit_percent: string;
  earth_lit_percent: string;
  bridge_h: string;
  /** Hazard limits in kelvin / resistance units; empty string = no limit (D-20261117-pj-0c5e). */
  max_temperature_k: string;
  min_temperature_k: string;
  min_soil_resistance: string;
  /** Battery model (D-20261117-pj-7b2d); energy mode is on when capacity, array power and a darkness load are filled. */
  battery_wh: string;
  array_w: string;
  endurance_h: string;
  dark_w: string;
  panel: string;
  panel_az_deg: string;
  lit_w: string;
  reserve_pct: string;
  charge_eff: string;
  require_both: boolean;
  hazards_enabled: boolean;
  local_search: boolean;
  mock: boolean;
};

export const ENERGY_DEFAULTS = {
  battery_wh: "",
  array_w: "",
  endurance_h: "",
  dark_w: "",
  panel: "tracking_vertical",
  panel_az_deg: "0",
  lit_w: "",
  reserve_pct: "10",
  charge_eff: "",
};

/** Energy mode: tier 1 complete (capacity, array power, and a darkness load in W or as endurance in hours). */
export function energyOn(f: Pick<PlannerForm, "battery_wh" | "array_w" | "endurance_h" | "dark_w">): boolean {
  return Number(f.battery_wh) > 0 && f.array_w !== "" && Number(f.array_w) >= 0 && (Number(f.dark_w) > 0 || Number(f.endurance_h) > 0);
}

export const HAZARD_LIMIT_DEFAULTS = {
  max_temperature_k: "320",
  min_temperature_k: "",
  min_soil_resistance: "0",
};

export const DEMO_SITE = {
  lat: "-89.46316",
  lon: "222.51045",
  start: "2027-01-01T00:00",
  end: "2027-01-01T23:00",
};

export type AppScreen = "analyses" | "planner" | "firstperson" | "map";

/** Fields every saved file has, in the list and in the full record. */
type AnalysisEnvelope = {
  id: string;
  createdAt: string;
  label: string;
  summary: {
    feasible: boolean;
    score: number;
    data_source?: string;
    longest_night_h?: number;
    longest_no_earth_h?: number;
    longest_lit_h?: number;
  };
  // D-20261118-pj-8625: set for analyses stored as files (absent for browser-demo localStorage ones).
  formatVersion?: number;
  dataVersion?: string | null;
  appVersion?: string | null;
  /** "search" = a stopped region search kept to be continued (D-20261118-pj-1454); absent = a site analysis. */
  kind?: "analysis" | "search";
};

/**
 * One row of the saved-analyses list (Rust `list_analyses`, or the browser fallback). It does NOT carry
 * the form: only the few form inputs the list shows, any of which can be missing in an old or edited file.
 */
export type SavedAnalysis = AnalysisEnvelope & {
  start?: string | null;
  end?: string | null;
  lat?: string | null;
  lon?: string | null;
  templateId?: string | null;
};

/** The full stored record (what one file in Documents/Moonpark holds); read with openAnalysis. */
export type StoredAnalysis = AnalysisEnvelope & { form: PlannerForm; payload: SitePayload };

export type SearchWarning = { code: string; message: string; fields?: string[]; count?: number };

/** POST /deep-search body as the desktop sends it (requirement fields = GET /site names, D-20261118-pj-75f1). */
export type DeepSearchRequest = Record<string, unknown> & {
  mode: "optimized" | "total_coverage";
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
  start: string;
  end: string;
  window_hours: number;
  step_min: number;
  mock: boolean;
  hazards_enabled: boolean;
};

export type RegionSearchSummary = {
  rows_evaluated: number;
  n_sites: number;
  runtime_s: number;
  claim: string;
  provisional: boolean;
  mock?: boolean;
  window_start: string;
  window_hours: number;
  /** Effective requirements the search evaluated (server's response.requirements). */
  requirements: Record<string, unknown> | null;
  warnings: SearchWarning[];
  dropped_cells: number;
  state: "complete" | "stopped";
  /** Opaque resume state of a stopped run (D-20261118-pj-1454). */
  checkpoint: Record<string, unknown> | null;
  /** Exact body sent; a resume must repeat it (the checkpoint is tied to range, window, mode and requirements). */
  request: DeepSearchRequest;
  /** Rows evaluated so far, as handed to the region map. */
  rows: Array<{ lat_deg: number; lon_deg: number; score: number; feasible: boolean; companion_score: number }>;
  best: { lat_deg: number; lon_deg: number } | null;
};

/** What a "Continue" of a stopped search hands the region map. */
export type SearchResume = {
  /** Id of the saved stopped-search file (overwritten if stopped again, removed when it completes). */
  id: string;
  label: string;
  request: DeepSearchRequest;
  checkpoint: Record<string, unknown>;
};

/** Template id whose schedule values all equal the form's, else "" (Custom) (D-20261118-pj-70ec). */
export function matchingTemplateId(form: PlannerForm, templates: MissionTemplate[]): string {
  const num = (a: string, b: number | undefined | null, dflt = 0) => a !== "" && Number(a) === (b ?? dflt);
  const hz = (a: string | undefined, b: number | null | undefined) => (b == null ? (a ?? "") === "" : (a ?? "") !== "" && Number(a) === b);
  const t = templates.find(
    (t) =>
      num(form.max_night_h, t.max_night_h) &&
      num(form.max_no_earth_h, t.max_no_earth_h) &&
      num(form.min_continuous_lit_h, t.min_continuous_lit_h) &&
      num(form.min_total_lit_h, t.min_total_lit_h) &&
      num(form.sun_lit_percent, t.sun_lit_percent) &&
      num(form.earth_lit_percent, t.earth_lit_percent) &&
      num(form.bridge_h, t.bridge_h) &&
      form.require_both === t.require_both &&
      hz(form.max_temperature_k, t.max_temperature_k) &&
      hz(form.min_temperature_k, t.min_temperature_k) &&
      hz(form.min_soil_resistance, t.min_soil_resistance),
  );
  return t?.id ?? "";
}
