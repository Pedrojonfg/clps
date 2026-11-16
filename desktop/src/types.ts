export type MissionTemplate = {
  id: string;
  label: string;
  description?: string;
  max_night_h: number;
  max_no_earth_h: number;
  min_continuous_lit_h?: number;
  sun_lit_percent: number;
  earth_lit_percent: number;
  bridge_h: number;
  require_both: boolean;
};

export type SitePayload = {
  data_source?: string;
  site?: { lat_deg: number; lon_deg: number; name?: string };
  mask: { elevation_deg: number[]; lat?: number; lon?: number };
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
  };
  needs: Record<string, number | boolean | undefined>;
  score: {
    feasible: boolean;
    score: number;
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
  step_h: string;
  template_id: string;
  max_night_h: string;
  max_no_earth_h: string;
  min_continuous_lit_h: string;
  sun_lit_percent: string;
  earth_lit_percent: string;
  bridge_h: string;
  require_both: boolean;
  hazards_enabled: boolean;
  local_search: boolean;
  mock: boolean;
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
  window_start: string;
  window_hours: number;
};
