import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { Button, Callout, Classes, ControlGroup, HTMLSelect, InputGroup, Tag } from "@blueprintjs/core";
import {
  STATIC_DEMO,
  buildDeepSearchRequest,
  regionMapUrl,
  runRegionSearch,
  stopRegionSearch,
} from "../api";
import { deleteAnalysis, saveStoppedSearch } from "../lib/analysesStore";
import type { DeepSearchRequest, PlannerForm, RegionSearchSummary, SearchResume } from "../types";

type Props = {
  /** The planner form in App state: the region search sends exactly these requirements (D-20261118-pj-75f1). */
  form: PlannerForm;
  onOpenSite: (lat: number, lon: number, target: "planner" | "firstperson") => void;
  /** A stopped search to continue (from Past analyses); started once, then onResumeHandled is called. */
  resume?: (SearchResume & { form: PlannerForm }) | null;
  onResumeHandled?: () => void;
  /** Called after a stopped-search file is written or removed, so the analyses list refreshes. */
  onSearchStoreChanged?: () => void;
};

// ---- the running search lives outside the component, so leaving the screen does not lose it ----

type JobState = {
  running: boolean;
  stopping: boolean;
  /** Shown while Stop keeps retrying (engine still setting up, or a stop call failed). */
  stopNote: string | null;
  jobId: string | null;
  error: string | null;
  notice: string | null;
  summary: RegionSearchSummary | null;
  /** Stopped-search file this run continues, if any. */
  resumeId: string | null;
};

let job: JobState = {
  running: false,
  stopping: false,
  stopNote: null,
  jobId: null,
  error: null,
  notice: null,
  summary: null,
  resumeId: null,
};
const listeners = new Set<() => void>();
const handledResumes = new WeakSet<object>();

function setJob(patch: Partial<JobState>): void {
  job = { ...job, ...patch };
  listeners.forEach((l) => l());
}
function subscribe(l: () => void): () => void {
  listeners.add(l);
  return () => listeners.delete(l);
}
const getJob = () => job;
const msg = (e: unknown) => (e instanceof Error ? e.message : String(e));
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * Stop keeps asking until the search request settles: the engine registers the job only after its
 * setup (which can take well over 20 s on first use), so an early stop call finds nothing yet.
 * Delay between tries: 1 s, growing to at most 5 s.
 */
const STOP_RETRY_MS = 1000;
const STOP_RETRY_MAX_MS = 5000;

async function startRun(
  request: DeepSearchRequest,
  form: PlannerForm,
  resume: SearchResume | null,
  onStoreChanged?: () => void,
): Promise<void> {
  // One search at a time: `running` stays true until the request settles (it is never aborted from
  // here, so a new search cannot start while the engine may still be running the previous one).
  if (job.running) return;
  const jobId = `job_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  setJob({ running: true, stopping: false, stopNote: null, jobId, error: null, notice: null, resumeId: resume?.id ?? null });
  let error: string | null = null;
  let notice: string | null = null;
  try {
    const summary = await runRegionSearch(request, { jobId, resume: resume?.checkpoint ?? null });
    if (summary.state === "stopped") {
      if (summary.checkpoint) {
        try {
          const saved = await saveStoppedSearch(form, summary, { id: resume?.id, label: resume?.label });
          notice =
            saved.persisted === "file"
              ? "Search stopped and saved; continue it from Past analyses."
              : saved.persisted === "browser"
                ? "Search stopped and kept in this browser; continue it from Past analyses."
                : "Search stopped; its state is kept in memory only until this window closes (browser storage is full or blocked).";
          onStoreChanged?.();
        } catch (e) {
          error = `Search stopped, but its state could not be saved: ${msg(e)}`;
        }
      } else {
        notice = "Search stopped; the engine returned no checkpoint, so it cannot be continued.";
      }
    } else if (resume) {
      // The continued search finished: its stopped-search file is no longer needed.
      try {
        await deleteAnalysis(resume.id);
        onStoreChanged?.();
      } catch (e) {
        notice = `Search completed, but the stopped-search file could not be removed: ${msg(e)}`;
      }
    }
    setJob({ summary, notice, error });
  } catch (e) {
    setJob({ error: msg(e), notice: null });
  } finally {
    setJob({ running: false, stopping: false, stopNote: null, jobId: null });
  }
}

/**
 * Stop button (D-20261118-pj-1454): ask the engine to stop; it then answers the search request itself
 * with state "stopped" and a checkpoint, so the fetch is kept open. The request is never aborted from
 * the UI (that would leave an engine job nobody can stop and let a second search start in parallel):
 * Stop keeps asking until the engine confirms or the search request settles on its own.
 */
async function requestStop(): Promise<void> {
  const id = job.jobId;
  if (!id || job.stopping) return;
  setJob({ stopping: true, stopNote: null });
  let delay = STOP_RETRY_MS;
  for (let tries = 1; job.jobId === id; tries++) {
    try {
      if (await stopRegionSearch(id)) {
        if (job.jobId === id) setJob({ stopNote: null });
        return;
      }
      if (tries >= 5 && job.jobId === id) {
        setJob({ stopNote: "The engine is still preparing the search; it will stop as soon as it starts." });
      }
    } catch (e) {
      if (job.jobId === id) setJob({ stopNote: `Could not reach the engine to stop the search (${msg(e)}); retrying.` });
    }
    await sleep(delay);
    delay = Math.min(STOP_RETRY_MAX_MS, delay * 1.5);
  }
}

const fmt = (v: unknown): string => {
  const n = Number(v);
  return Number.isFinite(n) ? (Number.isInteger(n) ? String(n) : n.toFixed(2)) : String(v);
};

/** Compact line with the requirements the search evaluated (from response.requirements). */
function requirementsLine(req: Record<string, unknown>, hazardsEnabled: boolean): string {
  const has = (k: string) => req[k] !== undefined && req[k] !== null;
  const pos = (k: string) => has(k) && Number(req[k]) > 0;
  const parts: string[] = [];
  if (typeof req.template_id === "string" && req.template_id) parts.push(`template ${req.template_id}`);
  // Maximum limits are strict ("less than"), as in the planner.
  if (has("max_night_h")) parts.push(`night < ${fmt(req.max_night_h)} h`);
  if (has("max_no_earth_h")) parts.push(`no-Earth < ${fmt(req.max_no_earth_h)} h`);
  if (pos("min_continuous_lit_h")) parts.push(`lit run ≥ ${fmt(req.min_continuous_lit_h)} h`);
  if (pos("min_total_lit_h")) parts.push(`total lit ≥ ${fmt(req.min_total_lit_h)} h`);
  if (has("sun_lit_percent")) parts.push(`Sun ≥ ${fmt(req.sun_lit_percent)} %`);
  if (has("earth_lit_percent")) parts.push(`Earth ≥ ${fmt(req.earth_lit_percent)} %`);
  if (req.require_both) parts.push("Sun and Earth together");
  if (req.energy_mode) {
    parts.push(
      `battery ${fmt(req.battery_wh)} Wh · array ${fmt(req.array_w)} W · dark load ${fmt(req.dark_w)} W` +
        (has("reserve_pct") ? ` · reserve ${fmt(req.reserve_pct)} %` : ""),
    );
  } else if (has("bridge_h")) {
    parts.push(`bridge ${fmt(req.bridge_h)} h`);
  }
  if (!hazardsEnabled) parts.push("hazards off");
  else {
    const hz: string[] = [];
    if (has("max_temperature_k")) hz.push(`T < ${fmt(req.max_temperature_k)} K`);
    if (has("min_temperature_k")) hz.push(`T ≥ ${fmt(req.min_temperature_k)} K`);
    if (pos("min_soil_resistance")) hz.push(`soil ≥ ${fmt(req.min_soil_resistance)}`);
    parts.push(hz.length ? hz.join(" · ") : "hazards on, no limits");
  }
  if (has("step_min")) parts.push(`step ${fmt(req.step_min)} min`);
  const ne = Array.isArray(req.not_evaluated) ? (req.not_evaluated as string[]) : [];
  if (ne.length) parts.push(`not evaluated: ${ne.join(", ")}`);
  return parts.join(" · ");
}

/** Every response warning, plus the dropped-cell count when no warning carries it. */
function warningLines(s: RegionSearchSummary): string[] {
  const lines = s.warnings.map((w) => w.message);
  if (s.dropped_cells > 0 && !s.warnings.some((w) => w.code === "cells_dropped_hazard_data")) {
    lines.push(`${s.dropped_cells} cell(s) dropped: the data this search needs is not available there.`);
  }
  return lines;
}

type Rect = { lat_min: string; lat_max: string; lon_min: string; lon_max: string };

/** Wedge around the active site: ±0.25° latitude (~7.5 km), ±25° longitude, clipped at the pole. */
function rectAround(form: PlannerForm): Rect {
  const lat = Number(form.lat);
  const lon = Number(form.lon);
  return {
    lat_min: Math.max(-90, lat - 0.25).toFixed(2),
    lat_max: Math.min(-80, lat + 0.25).toFixed(2),
    lon_min: Math.max(0, lon - 25).toFixed(1),
    lon_max: Math.min(360, lon + 25).toFixed(1),
  };
}

const MODE_HELP: Record<SearchMode, string> = {
  optimized: "Optimized: hill-climbs from several starts — fast, finds good cells, not guaranteed to be the best.",
  total_coverage: "Total coverage: evaluates every cell — slow, and the best result is the grid optimum.",
  moon_optimized_mock: "Whole Moon, optimized: precomputed mock data to check the UI.",
  moon_total_mock: "Whole Moon, total coverage: precomputed mock data to check the UI.",
};

type SearchMode = "optimized" | "total_coverage" | "moon_optimized_mock" | "moon_total_mock";

/** Whole supported region (the 1 km cap index stops at 80°S); the mock modes ignore the rectangle. */
const WHOLE_MOON: Rect = { lat_min: "-90", lat_max: "-80", lon_min: "0", lon_max: "360" };

function rectFromRequest(r: DeepSearchRequest): Rect {
  return { lat_min: String(r.lat_min), lat_max: String(r.lat_max), lon_min: String(r.lon_min), lon_max: String(r.lon_max) };
}

const RECT_FIELDS: { key: keyof Rect; label: string }[] = [
  { key: "lat_min", label: "Lat min" },
  { key: "lat_max", label: "Lat max" },
  { key: "lon_min", label: "Lon min" },
  { key: "lon_max", label: "Lon max" },
];

export function RegionMapScreen({ form, onOpenSite, resume = null, onResumeHandled, onSearchStoreChanged }: Props) {
  const state = useSyncExternalStore(subscribe, getJob);
  const [rect, setRect] = useState<Rect>(() =>
    state.summary ? rectFromRequest(state.summary.request) : rectAround(form),
  );
  const [mode, setMode] = useState<SearchMode>(() =>
    state.summary?.request.mode === "total_coverage" ? "total_coverage" : "optimized",
  );
  // Bulk search defaults to coarse (D-20261117-pj-91c6); the step used is shown in the requirements line.
  const [stepMin, setStepMin] = useState(() => String(state.summary?.request.step_min ?? 60));
  const [demo, setDemo] = useState(STATIC_DEMO);
  const [moon, setMoon] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [iframeKey, setIframeKey] = useState(0);
  const src = useMemo(() => regionMapUrl(form, demo, moon), [form, demo, moon, iframeKey]);
  const busy = state.running;
  const summary = state.summary;
  const error = localError ?? state.error;

  // Repaint the map when a run hands over new rows (also when it ended while this screen was closed).
  const seenSummary = useRef(state.summary);
  useEffect(() => {
    if (summary === seenSummary.current) return;
    seenSummary.current = summary;
    if (!summary) return;
    setDemo(false);
    setMoon(false);
    setIframeKey((k) => k + 1);
  }, [summary]);

  // Continue a stopped search with exactly its saved request (the checkpoint is tied to it).
  useEffect(() => {
    if (!resume || handledResumes.has(resume)) return;
    handledResumes.add(resume);
    onResumeHandled?.();
    if (getJob().running) {
      setLocalError("Another search is running; stop it before continuing a saved one.");
      return;
    }
    setLocalError(null);
    setRect(rectFromRequest(resume.request));
    setMode(resume.request.mode);
    setStepMin(String(resume.request.step_min));
    void startRun(resume.request, resume.form, resume, onSearchStoreChanged);
  }, [resume, onResumeHandled, onSearchStoreChanged]);

  useEffect(() => {
    function onMessage(ev: MessageEvent) {
      if (ev.origin !== window.location.origin) return;
      const m = ev.data as { type?: string; target?: string; lat?: number; lon?: number };
      if (m?.type !== "moonpark:open-site" || typeof m.lat !== "number" || typeof m.lon !== "number") return;
      onOpenSite(m.lat, m.lon, m.target === "firstperson" ? "firstperson" : "planner");
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [onOpenSite]);

  function search() {
    setLocalError(null);
    const mock = mode === "moon_optimized_mock" || mode === "moon_total_mock";
    let request: DeepSearchRequest;
    try {
      request = buildDeepSearchRequest(
        form,
        mock ? WHOLE_MOON : rect,
        mode === "optimized" || mode === "moon_optimized_mock" ? "optimized" : "total_coverage",
        mock,
        Number(stepMin),
      );
    } catch (e) {
      setLocalError(msg(e));
      return;
    }
    if (mock) setRect(WHOLE_MOON);
    void startRun(request, form, null, onSearchStoreChanged);
  }

  const warnings = summary ? warningLines(summary) : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, height: "calc(100vh - 82px)" }}>
      {STATIC_DEMO && (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Button small icon="lab-test" active={!moon} onClick={() => { setMoon(false); setIframeKey((k) => k + 1); }}>
            Demo samples
          </Button>
          <Button small icon="globe" active={moon} onClick={() => { setMoon(true); setIframeKey((k) => k + 1); }}>
            Whole Moon · total coverage (mock)
          </Button>
          <Tag minimal intent="danger">precomputed mock data — not a real search</Tag>
        </div>
      )}
      {!STATIC_DEMO && (
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <ControlGroup>
            {RECT_FIELDS.map((f) => (
              <InputGroup
                key={f.key}
                small
                aria-label={`${f.label} (degrees${f.key.startsWith("lon") ? " east" : ""})`}
                title={`${f.label} (degrees${f.key.startsWith("lon") ? " east" : ""})`}
                leftElement={<Tag minimal>{f.label}</Tag>}
                value={rect[f.key]}
                style={{ width: 124 }}
                onChange={(e) => setRect((r) => ({ ...r, [f.key]: e.target.value }))}
              />
            ))}
          </ControlGroup>
          <Button
            small
            minimal
            icon="locate"
            aria-label="Reset rectangle around the active site"
            title="Reset rectangle around the active site"
            onClick={() => setRect(rectAround(form))}
          />
          <HTMLSelect
            aria-label="Search mode"
            value={mode}
            onChange={(e) => setMode(e.target.value as typeof mode)}
            options={[
              { value: "optimized", label: "Optimized (partial)" },
              { value: "total_coverage", label: "Total coverage" },
              { value: "moon_optimized_mock", label: "Whole Moon · optimized (mock data)" },
              { value: "moon_total_mock", label: "Whole Moon · total coverage (mock data)" },
            ]}
          />
          <HTMLSelect
            aria-label="Time resolution"
            value={stepMin}
            onChange={(e) => setStepMin(e.target.value)}
            options={[
              { value: "60", label: "Coarse · 1 h" },
              { value: "10", label: "Fine · 10 min" },
            ]}
          />
          <Button small intent="primary" icon="search-around" loading={busy} disabled={busy} onClick={search}>
            Run region search
          </Button>
          {busy && (
            <Button
              small
              intent="danger"
              icon="stop"
              disabled={state.stopping}
              title="Stop the engine; the search is saved and can be continued from Past analyses"
              onClick={() => void requestStop()}
            >
              {state.stopping ? "Stopping..." : "Stop"}
            </Button>
          )}
          <Button
            small
            minimal
            icon="lab-test"
            disabled={busy}
            onClick={() => {
              setDemo(true);
              setMoon(false);
              setLocalError(null);
              setJob({ summary: null, notice: null, error: null });
              seenSummary.current = null;
              setIframeKey((k) => k + 1);
            }}
          >
            Demo samples
          </Button>
        </div>
      )}

      <div className={Classes.TEXT_MUTED} style={{ fontSize: 12, minHeight: 18, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        {busy ? (
          <span>
            {state.stopping
              ? `Stopping… the search state will be saved.${state.stopNote ? ` ${state.stopNote}` : ""}`
              : state.resumeId
                ? "Continuing the stopped search… no time limit; Stop saves it again."
                : "Searching… no time limit; Stop halts the engine and saves the search to continue later."}
          </span>
        ) : error ? (
          <span style={{ color: "#fa999c" }}>Region search failed: {error}</span>
        ) : summary ? (
          <>
            <span>
              {summary.rows_evaluated} site×time evaluations over {summary.n_sites} cells in{" "}
              {summary.runtime_s.toFixed(1)} s · window {summary.window_start} + {summary.window_hours} h ·{" "}
              {summary.state === "stopped"
                ? "stopped (partial)"
                : summary.claim === "grid_optimum"
                  ? "grid optimum"
                  : "best seen (not exhaustive)"}
            </span>
            {state.notice && <Tag minimal intent={summary.state === "stopped" ? "primary" : "warning"}>{state.notice}</Tag>}
            {summary.mock ? (
              <Tag minimal intent="danger">mock data — not a real search</Tag>
            ) : (
              summary.provisional && <Tag minimal intent="warning">provisional</Tag>
            )}
          </>
        ) : demo ? (
          <span>Demo samples — five hand-placed rows, not a search result.</span>
        ) : (
          <span>
            Deep search: scores each 1 km cell in the rectangle for the active time window and paints what was
            evaluated. {MODE_HELP[mode]}
          </span>
        )}
      </div>

      {summary && !busy && !error && summary.requirements && (
        <div className={Classes.TEXT_MUTED} style={{ fontSize: 11 }} title="Requirements this search evaluated (from the planner form)">
          Requirements used: {requirementsLine(summary.requirements, summary.request.hazards_enabled)}
        </div>
      )}
      {summary && !busy && !error && warnings.length > 0 && (
        <Callout compact intent="warning" icon="warning-sign" style={{ fontSize: 12, padding: "4px 8px" }}>
          {warnings.join(" ")}
        </Callout>
      )}

      <iframe
        key={iframeKey}
        title="Region score map"
        src={src}
        style={{ flex: 1, minHeight: 320, width: "100%", border: "1px solid #404854", borderRadius: 4, background: "#111418" }}
      />
    </div>
  );
}
