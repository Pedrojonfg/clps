import { useEffect, useMemo, useState } from "react";
import { Button, Classes, ControlGroup, HTMLSelect, InputGroup, Tag } from "@blueprintjs/core";
import { STATIC_DEMO, regionMapUrl, runRegionSearch } from "../api";
import type { PlannerForm, RegionSearchSummary } from "../types";

type Props = {
  form: PlannerForm;
  onOpenSite: (lat: number, lon: number, target: "planner" | "firstperson") => void;
};

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

const RECT_FIELDS: { key: keyof Rect; label: string }[] = [
  { key: "lat_min", label: "Lat min" },
  { key: "lat_max", label: "Lat max" },
  { key: "lon_min", label: "Lon min" },
  { key: "lon_max", label: "Lon max" },
];

export function RegionMapScreen({ form, onOpenSite }: Props) {
  const [rect, setRect] = useState<Rect>(() => rectAround(form));
  const [mode, setMode] = useState<SearchMode>("optimized");
  const [stepMin, setStepMin] = useState("60"); // bulk search defaults to coarse (D-20261117-pj-91c6)
  const [demo, setDemo] = useState(STATIC_DEMO);
  const [moon, setMoon] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RegionSearchSummary | null>(null);
  const [iframeKey, setIframeKey] = useState(0);
  const src = useMemo(() => regionMapUrl(form, demo, moon), [form, demo, moon, iframeKey]);

  useEffect(() => {
    function onMessage(ev: MessageEvent) {
      if (ev.origin !== window.location.origin) return;
      const m = ev.data as { type?: string; target?: string; lat?: number; lon?: number };
      if (m?.type !== "lunar-eval:open-site" || typeof m.lat !== "number" || typeof m.lon !== "number") return;
      onOpenSite(m.lat, m.lon, m.target === "firstperson" ? "firstperson" : "planner");
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [onOpenSite]);

  async function search() {
    setBusy(true);
    setError(null);
    try {
      const mock = mode === "moon_optimized_mock" || mode === "moon_total_mock";
      if (mock) setRect(WHOLE_MOON);
      setSummary(
        await runRegionSearch(
          form,
          mock ? WHOLE_MOON : rect,
          mode === "optimized" || mode === "moon_optimized_mock" ? "optimized" : "total_coverage",
          mock,
          Number(stepMin),
        ),
      );
      setDemo(false);
      setMoon(false);
      setIframeKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

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
          <Button small intent="primary" icon="search-around" loading={busy} onClick={search}>
            Run region search
          </Button>
          <Button
            small
            minimal
            icon="lab-test"
            disabled={busy}
            onClick={() => {
              setDemo(true);
              setMoon(false);
              setSummary(null);
              setIframeKey((k) => k + 1);
            }}
          >
            Demo samples
          </Button>
        </div>
      )}

      <div className={Classes.TEXT_MUTED} style={{ fontSize: 12, minHeight: 18, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        {error ? (
          <span style={{ color: "#fa999c" }}>Region search failed: {error}</span>
        ) : summary ? (
          <>
            <span>
              {summary.rows_evaluated} site×time evaluations over {summary.n_sites} cells in{" "}
              {summary.runtime_s.toFixed(1)} s · window {summary.window_start} + {summary.window_hours} h ·{" "}
              {summary.claim === "grid_optimum" ? "grid optimum" : "best seen (not exhaustive)"}
            </span>
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

      <iframe
        key={iframeKey}
        title="Region score map"
        src={src}
        style={{ flex: 1, minHeight: 320, width: "100%", border: "1px solid #404854", borderRadius: 4, background: "#111418" }}
      />
    </div>
  );
}
