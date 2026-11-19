// Saved analyses: one JSON file each in Documents/Moonpark (desktop app, Rust commands in
// src-tauri/src/analyses.rs). Outside Tauri (browser dev, STATIC_DEMO) the old localStorage store is used.
// Analyses stored in the browser by earlier versions are not migrated and not deleted. # per D-20261118-pj-8625
// Stopped region searches are kept in the same folder and envelope with kind "search" and a checkpoint
// (D-20261118-pj-1454); they are listed with the analyses and continued from the region map.
import { fetchStoreVersion } from "../api";
import type {
  PlannerForm,
  RegionSearchSummary,
  SavedAnalysis,
  SearchResume,
  SitePayload,
  StoredAnalysis,
} from "../types";

const STORAGE_KEY = "moonpark_analyses_v1";
const MAX_SAVED_BROWSER = 40; // browser fallback only; the file store has no maximum
export const FORMAT_VERSION = 1;

export type AnalysisFileError = { file: string; error: string };
export type AnalysesListing = { items: SavedAnalysis[]; errors: AnalysisFileError[] };

export const inTauri = (): boolean => typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

async function call<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  try {
    return await invoke<T>(cmd, args);
  } catch (e) {
    throw new Error(typeof e === "string" ? e : e instanceof Error ? e.message : String(e));
  }
}

// ---- browser fallback -------------------------------------------------------------------

function browserLoad(): StoredAnalysis[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredAnalysis[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function browserPersist(list: StoredAnalysis[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_SAVED_BROWSER)));
}

/** Browser fallback for stopped searches whose checkpoint does not fit in localStorage: this session only. */
const memorySearches = new Map<string, StoredSearch>();

// ---- shared -----------------------------------------------------------------------------

function summarize(payload: SitePayload): SavedAnalysis["summary"] {
  return {
    feasible: Boolean(payload.score?.feasible),
    score: Number(payload.score?.score ?? 0),
    data_source: payload.data_source,
    longest_night_h: payload.series?.longest_night_h,
    longest_no_earth_h: payload.series?.longest_no_earth_h,
    longest_lit_h: payload.series?.longest_lit_h,
  };
}

/** Data version the payload was computed with: provenance.data_version (top-level data_version as a fallback). */
function payloadDataVersion(payload: SitePayload): string | null {
  const ok = (v: unknown): v is string => typeof v === "string" && v !== "";
  const p = payload.provenance?.data_version;
  if (ok(p)) return p;
  const top = (payload as { data_version?: unknown }).data_version;
  return ok(top) ? top : null;
}

/** The list row for a full record: the envelope plus the few form inputs the list shows (as Rust does). */
function listEntry(a: StoredAnalysis | StoredSearch): SavedAnalysis {
  const { payload: _p, checkpoint: _c, form, ...rest } = a as StoredAnalysis & { checkpoint?: unknown };
  const f = (form ?? {}) as Partial<PlannerForm>;
  const str = (v: unknown) => (typeof v === "string" ? v : typeof v === "number" ? String(v) : null);
  return {
    ...rest,
    start: str(f.start),
    end: str(f.end),
    lat: str(f.lat),
    lon: str(f.lon),
    templateId: str(f.template_id),
  };
}

export async function loadAnalyses(): Promise<AnalysesListing> {
  if (!inTauri()) {
    const stored = browserLoad();
    const extra = [...memorySearches.values()].filter((m) => !stored.some((a) => a.id === m.id));
    const items = [...extra, ...stored]
      .filter((a) => a && typeof a === "object" && typeof a.id === "string")
      .map((a) => listEntry(a))
      .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
    return { items, errors: [] };
  }
  return call<AnalysesListing>("list_analyses");
}

export async function saveAnalysis(
  form: PlannerForm,
  payload: SitePayload,
  label?: string,
  meta?: { dataVersion?: string | null },
): Promise<SavedAnalysis> {
  const id = `a_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
  const record: StoredAnalysis = {
    formatVersion: FORMAT_VERSION,
    id,
    createdAt: new Date().toISOString(),
    label:
      label?.trim() || `Site ${Number(form.lat).toFixed(3)}°, ${Number(form.lon).toFixed(3)}°`,
    appVersion: null, // filled in by the desktop shell on write
    dataVersion: meta?.dataVersion ?? payloadDataVersion(payload),
    form: { ...form },
    payload,
    summary: summarize(payload),
  };
  if (inTauri()) {
    await call<string>("save_analysis", { json: JSON.stringify(record), id });
  } else {
    browserPersist([record, ...browserLoad()]);
  }
  return listEntry(record);
}

/** Delete one analysis; resolves true when something was deleted. */
export async function deleteAnalysis(id: string): Promise<boolean> {
  if (inTauri()) return call<boolean>("delete_analysis", { id });
  const inMemory = memorySearches.delete(id);
  const list = browserLoad();
  const next = list.filter((a) => a.id !== id);
  if (next.length !== list.length) browserPersist(next);
  return inMemory || next.length !== list.length;
}

/** The full stored record, including the stored result. */
export async function openAnalysis(id: string): Promise<StoredAnalysis> {
  if (!inTauri()) {
    const a = browserLoad().find((x) => x.id === id);
    if (!a || !a.payload) throw new Error("This saved analysis has no stored result (saved by an older version); use Recalculate.");
    return a;
  }
  const text = await call<string>("read_analysis", { id });
  let rec: StoredAnalysis;
  try {
    rec = JSON.parse(text) as StoredAnalysis;
  } catch (e) {
    throw new Error(`the saved file is damaged: ${e instanceof Error ? e.message : e}`);
  }
  if (!rec || typeof rec !== "object" || !rec.payload || !rec.form) {
    throw new Error("the saved file is damaged: no stored result");
  }
  if (rec.kind === "search") {
    throw new Error("this is a stopped region search, not a site analysis; use Continue");
  }
  if (typeof rec.formatVersion === "number" && rec.formatVersion > FORMAT_VERSION) {
    throw new Error(`this analysis was saved by a newer version of the app (file format ${rec.formatVersion})`);
  }
  return rec;
}

/** Folder the analyses are saved in (desktop only). */
export async function analysesDir(): Promise<string | null> {
  return inTauri() ? call<string>("analyses_dir") : null;
}

/** Browser fallback only: removes every analysis in localStorage. */
export function clearBrowserAnalyses(): void {
  localStorage.removeItem(STORAGE_KEY);
}

// ---- stopped region searches (D-20261118-pj-1454) ------------------------------------------

/** One stopped search file: the analysis envelope plus kind "search" and the engine's checkpoint. */
export type StoredSearch = Omit<StoredAnalysis, "payload" | "kind"> & {
  kind: "search";
  /** What was computed up to the stop (no checkpoint copy) and the exact request to repeat on resume. */
  payload: Omit<RegionSearchSummary, "checkpoint">;
  checkpoint: Record<string, unknown>;
};

export const newSearchId = (): string =>
  `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;

/**
 * Save a stopped search so it can be continued later. Pass `id` to overwrite the file of a search
 * that was resumed and stopped again. Outside Tauri it falls back to localStorage, then to memory.
 */
export async function saveStoppedSearch(
  form: PlannerForm,
  result: RegionSearchSummary,
  opts: { id?: string; label?: string } = {},
): Promise<{ id: string; persisted: "file" | "browser" | "memory" }> {
  if (!result.checkpoint) throw new Error("this search has no checkpoint to save");
  const id = opts.id ?? newSearchId();
  const { checkpoint, ...payload } = result;
  const r = result.request;
  // The engine's data version now (best effort; null when unknown): a stopped search has no payload provenance.
  const dataVersion = await fetchStoreVersion();
  const record: StoredSearch = {
    formatVersion: FORMAT_VERSION,
    kind: "search",
    id,
    createdAt: new Date().toISOString(),
    label:
      opts.label?.trim() ||
      `Search ${r.mode === "total_coverage" ? "total coverage" : "optimized"} · lat ${r.lat_min}..${r.lat_max}, lon ${r.lon_min}..${r.lon_max}`,
    appVersion: null, // filled in by the desktop shell on write
    dataVersion,
    form: { ...form },
    payload,
    // Minimal summary: a stopped search has no verdict yet; the list labels it "Search (stopped)".
    summary: {
      feasible: false,
      score: 0,
      data_source: result.mock ? "mock" : "real",
    },
    checkpoint,
  };
  if (inTauri()) {
    await call<string>("save_analysis", { json: JSON.stringify(record), id });
    return { id, persisted: "file" };
  }
  try {
    const rest = browserLoad().filter((a) => a.id !== id);
    browserPersist([record as unknown as StoredAnalysis, ...rest]);
    memorySearches.delete(id);
    return { id, persisted: "browser" };
  } catch {
    memorySearches.set(id, record);
    return { id, persisted: "memory" };
  }
}

/** Read a stopped search back for Continue. */
export async function openStoppedSearch(id: string): Promise<SearchResume & { form: PlannerForm }> {
  let rec: StoredSearch | undefined;
  if (inTauri()) {
    const text = await call<string>("read_analysis", { id });
    try {
      rec = JSON.parse(text) as StoredSearch;
    } catch (e) {
      throw new Error(`the saved file is damaged: ${e instanceof Error ? e.message : e}`);
    }
  } else {
    rec =
      memorySearches.get(id) ??
      (browserLoad().find((a) => a.id === id) as unknown as StoredSearch | undefined);
    if (!rec) throw new Error("this stopped search is no longer stored");
  }
  if (!rec || typeof rec !== "object" || rec.kind !== "search") {
    throw new Error("the saved file is not a stopped search");
  }
  if (typeof rec.formatVersion === "number" && rec.formatVersion > FORMAT_VERSION) {
    throw new Error(`this search was saved by a newer version of the app (file format ${rec.formatVersion})`);
  }
  const request = rec.payload?.request;
  if (!request || typeof request !== "object" || !rec.checkpoint || typeof rec.checkpoint !== "object" || !rec.form) {
    throw new Error("the saved file is damaged: no request or checkpoint to continue from");
  }
  return { id: rec.id, label: rec.label, request, checkpoint: rec.checkpoint, form: rec.form };
}
