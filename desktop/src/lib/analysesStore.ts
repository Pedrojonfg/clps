import type { PlannerForm, SavedAnalysis, SitePayload } from "../types";

const STORAGE_KEY = "moonpark_analyses_v1";
const MAX_SAVED = 40;

export function loadAnalyses(): SavedAnalysis[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as SavedAnalysis[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persist(list: SavedAnalysis[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_SAVED)));
}

export function saveAnalysis(
  form: PlannerForm,
  payload: SitePayload,
  label?: string,
): SavedAnalysis {
  const entry: SavedAnalysis = {
    id: `a_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    createdAt: new Date().toISOString(),
    label:
      label?.trim() ||
      `Site ${Number(form.lat).toFixed(3)}°, ${Number(form.lon).toFixed(3)}°`,
    form: { ...form },
    summary: {
      feasible: Boolean(payload.score?.feasible),
      score: Number(payload.score?.score ?? 0),
      data_source: payload.data_source,
      longest_night_h: payload.series?.longest_night_h,
      longest_no_earth_h: payload.series?.longest_no_earth_h,
      longest_lit_h: payload.series?.longest_lit_h,
    },
  };
  const next = [entry, ...loadAnalyses().filter((a) => a.id !== entry.id)];
  persist(next);
  return entry;
}

export function deleteAnalysis(id: string): SavedAnalysis[] {
  const next = loadAnalyses().filter((a) => a.id !== id);
  persist(next);
  return next;
}

export function clearAnalyses(): void {
  localStorage.removeItem(STORAGE_KEY);
}
