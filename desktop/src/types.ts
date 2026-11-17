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
    hours_sun_above_threshold?: number;
    hours_earth_above_threshold?: number;
    any_both?: boolean;
    /** Sample spacing in minutes (D-20261117-pj-91c6); the metrics above are in hours. */
    step_min?: number;
    /** Energy mode: state of charge per sample as a fraction of capacity, and its minimum. */
    soc?: number[];
    soc_min?: number;
  };
  needs: Record<string, number | boolean | undefined>;
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

export type SavedAnalysis = {
  id: string;
  createdAt: string;
  label: string;
  form: PlannerForm;
  summary: {
    feasible: boolean;
    score: number;
    data_source?: string;
    longest_night_h?: number;
    longest_no_earth_h?: number;
    longest_lit_h?: number;
  };
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
};
