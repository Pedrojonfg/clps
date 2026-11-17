import { FormEvent, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import {
  Button,
  Callout,
  Checkbox,
  Classes,
  Collapse,
  FormGroup,
  HTMLSelect,
  InputGroup,
  Radio,
  Spinner,
  Tab,
  Tabs,
  Tag,
} from "@blueprintjs/core";
import { STATIC_DEMO, fetchSite, fetchTemplates } from "../api";
import { LocalSearchBoard } from "../LocalSearchBoard";
import { SiteResult } from "../SiteCharts";
import { DEMO_SITE, MissionTemplate, PlannerForm, SitePayload } from "../types";

type Props = {
  form: PlannerForm;
  setForm: Dispatch<SetStateAction<PlannerForm>>;
  data: SitePayload | null;
  setData: (d: SitePayload | null) => void;
  onSaved: (form: PlannerForm, payload: SitePayload) => void;
  onOpen3d: () => void;
  onOpenMap: () => void;
  autoRun?: boolean;
};

export function PlannerScreen({
  form,
  setForm,
  data,
  setData,
  onSaved,
  onOpen3d,
  onOpenMap,
  autoRun = false,
}: Props) {
  const [templates, setTemplates] = useState<MissionTemplate[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // Setup / Results split (D-20261117-pj-3b71); coming back with a result shows it.
  const [view, setView] = useState<"setup" | "results">(data ? "results" : "setup");
  const [tab, setTab] = useState<"overview" | "best">("overview");
  const [needsOpen, setNeedsOpen] = useState(false);

  useEffect(() => {
    fetchTemplates()
      .then(setTemplates)
      .catch((e: Error) => setError(`Templates: ${e.message}`));
  }, []);

  useEffect(() => {
    if (!autoRun || data) return;
    let cancelled = false;
    (async () => {
      setBusy(true);
      setStatus("Computing…");
      try {
        const payload = await fetchSite(form);
        if (cancelled) return;
        setData(payload);
        onSaved(form, payload);
        setStatus("");
        setTab("overview");
        setView("results");
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
        setStatus("");
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [autoRun]);

  function setField<K extends keyof PlannerForm>(key: K, value: PlannerForm[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function onTemplateChange(id: string) {
    setField("template_id", id);
    const tpl = templates.find((t) => t.id === id);
    if (!tpl) return;
    setForm((f) => ({
      ...f,
      template_id: id,
      max_night_h: String(tpl.max_night_h),
      max_no_earth_h: String(tpl.max_no_earth_h),
      min_continuous_lit_h: String(tpl.min_continuous_lit_h ?? 0),
      sun_lit_percent: String(tpl.sun_lit_percent),
      earth_lit_percent: String(tpl.earth_lit_percent),
      bridge_h: String(tpl.bridge_h),
      require_both: tpl.require_both,
      max_temperature_k: tpl.max_temperature_k == null ? "" : String(tpl.max_temperature_k),
      min_temperature_k: tpl.min_temperature_k == null ? "" : String(tpl.min_temperature_k),
      min_soil_resistance: tpl.min_soil_resistance == null ? "" : String(tpl.min_soil_resistance),
    }));
  }

  async function runPlanner(ev?: FormEvent) {
    ev?.preventDefault();
    setBusy(true);
    setError(null);
    setStatus("Computing…");
    try {
      const payload = await fetchSite(form);
      setData(payload);
      onSaved(form, payload);
      setStatus("");
      setTab("overview");
      setView("results");
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : String(e));
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  const sc = data?.score;
  const mock = data?.data_source !== "real";
  const hasBoard = Boolean(data?.local_search?.leaderboard?.length);
  const needsSummary = `${form.template_id ? templates.find((t) => t.id === form.template_id)?.label ?? form.template_id : "Custom"} · night ≤ ${form.max_night_h} h · no-Earth ≤ ${form.max_no_earth_h} h${form.min_continuous_lit_h !== "0" ? ` · lit ≥ ${form.min_continuous_lit_h} h` : ""}${form.require_both ? " · Sun+Earth together" : ""}${form.hazards_enabled && form.max_temperature_k ? ` · T ≤ ${form.max_temperature_k} K` : ""}${form.hazards_enabled && form.min_temperature_k ? ` · T ≥ ${form.min_temperature_k} K` : ""}`;

  /** Move the window to a leaderboard start, keeping its length; the user then re-runs. */
  function useStart(windowStartIso: string) {
    const span = Date.parse(`${form.end}:00Z`) - Date.parse(`${form.start}:00Z`);
    const t0 = Date.parse(windowStartIso);
    if (!Number.isFinite(span) || !Number.isFinite(t0)) return;
    const local = (ms: number) => new Date(ms).toISOString().slice(0, 16);
    setForm((f) => ({ ...f, start: local(t0), end: local(t0 + span) }));
    setStatus("Window moved to the selected start — press Run planner to evaluate it.");
    setView("setup");
  }

  const demoCallout = STATIC_DEMO && (
    <Callout intent="warning" title="Browser demo: mocked data" style={{ marginBottom: 8 }}>
      There is no server behind this page. Every run returns the same sample result, so changing the inputs
      does not change it. For computed results, run lunar-eval locally with the data —{" "}
      <a href="https://github.com/Pedrojonfg/clps#try-it" target="_blank" rel="noreferrer">
        see the README
      </a>
      .
    </Callout>
  );

  const messages = (
    <>
      {status && (
        <Callout style={{ marginBottom: 8 }}>
          {busy && <Spinner size={16} />} {status}
        </Callout>
      )}
      {error && (
        <Callout intent="danger" title="Planner error" style={{ marginBottom: 8 }}>
          {error}
          <div className={Classes.TEXT_MUTED} style={{ marginTop: 8 }}>
            Start the API:{" "}
            <code>cd ~/clps && PYTHONPATH=. python3 -m uvicorn api.app:app --port 8000</code>
          </div>
        </Callout>
      )}
    </>
  );

  if (view === "results" && data) {
    return (
      <div>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <Button icon="arrow-left" onClick={() => setView("setup")}>
            Edit inputs
          </Button>
          <Button icon="globe" onClick={onOpen3d}>
            Open in 3D
          </Button>
          <Button icon="map" onClick={onOpenMap}>
            Region map
          </Button>
          <span className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
            {form.lat}°, {form.lon}° · {form.start.replace("T", " ")} → {form.end.replace("T", " ")} UTC
          </span>
          <span style={{ flex: 1 }} />
          {mock && (
            <Tag minimal intent="warning">
              mock data — not a result
            </Tag>
          )}
        </div>
        {messages}
        <Tabs id="planner-results" selectedTabId={tab} onChange={(id) => setTab(id as "overview" | "best")} renderActiveTabPanelOnly>
          <Tab id="overview" title="Overview" />
          <Tab
            id="best"
            title={hasBoard ? `Best starts (${data.local_search!.leaderboard.length})` : "Best starts"}
          />
        </Tabs>
        <div style={{ opacity: busy ? 0.5 : 1, marginTop: 10 }}>
          {tab === "overview" && (
            <>
              <SiteResult data={data} />
              <p className={Classes.TEXT_MUTED} style={{ margin: "8px 0 0", fontSize: 11 }}>
                Provenance:{" "}
                {data.data_source === "real"
                  ? "horizon mask computed from LOLA DEMs, Sun and Earth from SPICE kernels"
                  : "mocked horizon and sky — not a result"}{" "}
                · score formula {sc?.provenance?.score_formula ?? "—"}
              </p>
            </>
          )}
          {tab === "best" &&
            (hasBoard ? (
              <div style={{ maxHeight: "calc(100vh - 170px)", overflowY: "auto" }}>
                <LocalSearchBoard data={data} onUseStart={useStart} />
              </div>
            ) : (
              <Callout icon="info-sign" title="This analysis ran without “Best nearby start”">
                Switch the mode in Setup to “Best nearby start” and run again to rank shifted window starts.
                <div style={{ marginTop: 8 }}>
                  <Button
                    intent="primary"
                    onClick={() => {
                      setField("local_search", true);
                      setView("setup");
                    }}
                  >
                    Enable it in Setup
                  </Button>
                </div>
              </Callout>
            ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className={Classes.HEADING} style={{ marginTop: 0, marginBottom: 2 }}>
        New analysis
      </h2>
      <p className={Classes.TEXT_MUTED} style={{ marginTop: 0, fontSize: 12 }}>
        Scores one landing site over one time window: when the Sun and the Earth clear the local horizon, and
        whether that meets the mission's needs. Evaluated on this machine.
      </p>
      {demoCallout}

      <form onSubmit={runPlanner}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(11rem, 1fr))",
            gap: "0 12px",
          }}
        >
          <FormGroup label="Latitude °" labelFor="lat">
            <InputGroup id="lat" value={form.lat} onChange={(e) => setField("lat", e.target.value)} />
          </FormGroup>
          <FormGroup label="Longitude °" labelFor="lon">
            <InputGroup id="lon" value={form.lon} onChange={(e) => setField("lon", e.target.value)} />
          </FormGroup>
          <FormGroup label="Start (UTC)" labelFor="start">
            <InputGroup id="start" type="datetime-local" value={form.start} onChange={(e) => setField("start", e.target.value)} />
          </FormGroup>
          <FormGroup label="End (UTC)" labelFor="end">
            <InputGroup id="end" type="datetime-local" value={form.end} onChange={(e) => setField("end", e.target.value)} />
          </FormGroup>
          <FormGroup label="Mission template" labelFor="template">
            <HTMLSelect id="template" fill value={form.template_id} onChange={(e) => onTemplateChange(e.target.value)}>
              <option value="">Custom</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </HTMLSelect>
          </FormGroup>
        </div>

        <div style={{ marginBottom: 8 }}>
          <Button minimal small icon={needsOpen ? "chevron-down" : "chevron-right"} onClick={() => setNeedsOpen((o) => !o)}>
            Mission needs
          </Button>
          <span className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
            {needsSummary}
          </span>
          <Collapse isOpen={needsOpen}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(11rem, 1fr))",
                gap: "8px 12px",
                padding: "8px 0 0 8px",
              }}
            >
              <FormGroup label="Max night (h)" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.max_night_h} onChange={(e) => setField("max_night_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Max no-Earth (h)" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.max_no_earth_h} onChange={(e) => setField("max_no_earth_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Min continuous lit (h)" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.min_continuous_lit_h} onChange={(e) => setField("min_continuous_lit_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Sun lit %" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.sun_lit_percent} onChange={(e) => setField("sun_lit_percent", e.target.value)} />
              </FormGroup>
              <FormGroup label="Earth lit %" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.earth_lit_percent} onChange={(e) => setField("earth_lit_percent", e.target.value)} />
              </FormGroup>
              <FormGroup label="Shadow bridge (h)" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.bridge_h} onChange={(e) => setField("bridge_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Step (h)" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.step_h} onChange={(e) => setField("step_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Max temperature (K)" helperText="empty = no limit" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.max_temperature_k ?? ""} onChange={(e) => setField("max_temperature_k", e.target.value)} />
              </FormGroup>
              <FormGroup label="Min temperature (K)" helperText="empty = no limit" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.min_temperature_k ?? ""} onChange={(e) => setField("min_temperature_k", e.target.value)} />
              </FormGroup>
              <FormGroup label="Min soil resistance" helperText="empty = no limit" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.min_soil_resistance ?? ""} onChange={(e) => setField("min_soil_resistance", e.target.value)} />
              </FormGroup>
              <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
                <Checkbox
                  style={{ margin: 0 }}
                  checked={form.require_both}
                  label="Require Sun and Earth together"
                  onChange={(e) => setField("require_both", e.currentTarget.checked)}
                />
                <Checkbox
                  style={{ margin: 0 }}
                  checked={form.hazards_enabled}
                  label="Layer-B hazards in score"
                  onChange={(e) => setField("hazards_enabled", e.currentTarget.checked)}
                />
              </div>
            </div>
          </Collapse>
        </div>

        <div
          role="radiogroup"
          aria-label="Analysis mode"
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 8 }}
        >
          <div className={Classes.CARD} style={{ padding: 10 }}>
            <Radio
              name="mode"
              checked={!form.local_search}
              onChange={() => setField("local_search", false)}
              label="Single window"
              style={{ marginBottom: 2, fontWeight: 600 }}
            />
            <div className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
              Score exactly this window at this site. Fast.
            </div>
          </div>
          <div className={Classes.CARD} style={{ padding: 10 }}>
            <Radio
              name="mode"
              checked={form.local_search}
              onChange={() => setField("local_search", true)}
              label="Best nearby start"
              style={{ marginBottom: 2, fontWeight: 600 }}
            />
            <div className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
              Same site, same window length, slid hour by hour around your start; ranks every start in
              “Best starts”. Slower.
            </div>
          </div>
        </div>
        <p className={Classes.TEXT_MUTED} style={{ fontSize: 12, margin: "0 0 8px" }}>
          Looking across a whole region instead of one site? Use the{" "}
          <a onClick={onOpenMap}>Region map</a> (deep search over a rectangle or the whole Moon).
        </p>

        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <Button type="submit" intent="primary" icon="play" disabled={busy} loading={busy}>
            Run planner
          </Button>
          <Button type="button" disabled={busy} onClick={() => setForm((f) => ({ ...f, ...DEMO_SITE }))}>
            Demo site (PGDA Site01)
          </Button>
          {data && (
            <Button type="button" icon="timeline-bar-chart" onClick={() => setView("results")}>
              View last result
            </Button>
          )}
          <span style={{ flex: 1 }} />
          <Checkbox
            style={{ margin: 0 }}
            checked={form.mock || STATIC_DEMO}
            disabled={STATIC_DEMO}
            label="Mock data (demo)"
            onChange={(e) => setField("mock", e.currentTarget.checked)}
          />
        </div>
      </form>

      {messages}
    </div>
  );
}
