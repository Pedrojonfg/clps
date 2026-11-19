import { FormEvent, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import {
  Button,
  Callout,
  Checkbox,
  Classes,
  Collapse,
  FormGroup,
  HTMLSelect,
  InputGroup,
  ProgressBar,
  Radio,
  Spinner,
  Tab,
  Tabs,
  Tag,
} from "@blueprintjs/core";
import {
  STATIC_DEMO,
  buildSiteQuery,
  fetchProgress,
  latitudeProblem,
  fetchSite,
  fetchTemplates,
  requirementProblems,
  type DownloadProgress,
  type RequirementKey,
} from "../api";

const mb = (bytes: number) => (bytes / 1e6).toFixed(bytes >= 1e8 ? 0 : 1);
import { LocalSearchBoard } from "../LocalSearchBoard";
import { SiteResult } from "../SiteCharts";
import { DEMO_SITE, MissionTemplate, PlannerForm, SitePayload, energyOn, matchingTemplateId } from "../types";

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
  const [dl, setDl] = useState<DownloadProgress | null>(null);
  // Whether the engine has answered a /progress poll yet for this request (stage labels, D-20261118-pj-23ab).
  const [polled, setPolled] = useState(false);
  const stageLabel = dl ? "Downloading" : polled ? "Processing" : "Waiting for the engine";
  // The inputs the displayed result was computed with; a result is only ever shown against these.
  const [ranWith, setRanWith] = useState<PlannerForm | null>(data ? form : null);
  const stale = Boolean(data && ranWith && buildSiteQuery(ranWith) !== buildSiteQuery(form));
  // Latest request wins: older responses (aborted or late) are ignored.
  const reqId = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => () => abortRef.current?.abort(), []);

  // While an analysis runs, ask the engine whether it is downloading data (first use, D-8c03).
  useEffect(() => {
    if (!busy) {
      setDl(null);
      setPolled(false);
      return;
    }
    let live = true;
    const id = window.setInterval(async () => {
      const p = await fetchProgress();
      if (!live) return;
      setDl(p?.active ? p : null);
      if (p) setPolled(true);
    }, 1000);
    return () => {
      live = false;
      window.clearInterval(id);
    };
  }, [busy]);
  // Setup / Results split (D-20261117-pj-3b71); coming back with a result shows it.
  const [view, setView] = useState<"setup" | "results">(data ? "results" : "setup");
  const [tab, setTab] = useState<"overview" | "best">("overview");
  const [provOpen, setProvOpen] = useState(false);
  const [needsOpen, setNeedsOpen] = useState(false);
  const [batteryOpen, setBatteryOpen] = useState(false);

  useEffect(() => {
    fetchTemplates()
      .then(setTemplates)
      .catch((e: Error) => setError(`Templates: ${e.message}`));
  }, []);

  useEffect(() => {
    if (!autoRun || data) return;
    void compute(form);
  }, [autoRun]);

  // The template select shows a template only while every value still equals it; any edit -> Custom ("").
  useEffect(() => {
    if (!templates.length) return;
    const id = matchingTemplateId(form, templates);
    if (id !== form.template_id) setForm((f) => ({ ...f, template_id: id }));
  }, [templates, form, setForm]);

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
      min_total_lit_h: String(tpl.min_total_lit_h ?? 0),
      sun_lit_percent: String(tpl.sun_lit_percent),
      earth_lit_percent: String(tpl.earth_lit_percent),
      bridge_h: String(tpl.bridge_h),
      require_both: tpl.require_both,
      max_temperature_k: tpl.max_temperature_k == null ? "" : String(tpl.max_temperature_k),
      min_temperature_k: tpl.min_temperature_k == null ? "" : String(tpl.min_temperature_k),
      min_soil_resistance: tpl.min_soil_resistance == null ? "" : String(tpl.min_soil_resistance),
    }));
  }

  async function compute(f: PlannerForm) {
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    const id = ++reqId.current;
    setBusy(true);
    setError(null);
    setStatus("Computing…");
    try {
      const payload = await fetchSite(f, ctl.signal);
      if (id !== reqId.current) return;
      setData(payload);
      setRanWith(f);
      onSaved(f, payload);
      setStatus("");
      setTab("overview");
      setView("results");
    } catch (e) {
      if (id !== reqId.current || ctl.signal.aborted) return;
      setData(null);
      setRanWith(null);
      setError(e instanceof Error ? e.message : String(e));
      setStatus("");
    } finally {
      if (id === reqId.current) setBusy(false);
    }
  }

  const latMsg = latitudeProblem(form.lat);
  // Schedule fields: same rules fetchSite and the region search enforce; Run stays off until fixed.
  const needProblems = requirementProblems(form);
  const needsInvalid = Object.keys(needProblems).length > 0;
  const fieldProps = (key: RequirementKey, helper?: string) => ({
    intent: needProblems[key] ? ("danger" as const) : ("none" as const),
    helperText: needProblems[key] ?? helper,
  });

  function runPlanner(ev?: FormEvent) {
    ev?.preventDefault();
    if (latMsg) {
      setError(latMsg);
      return;
    }
    if (needsInvalid) {
      setNeedsOpen(true);
      setView("setup");
      return;
    }
    void compute(form);
  }

  const sc = data?.score;
  const mock = data?.data_source !== "real";
  const hasBoard = Boolean(data?.local_search?.leaderboard?.length);
  const needsSummary = `${form.template_id ? templates.find((t) => t.id === form.template_id)?.label ?? form.template_id : "Custom"} · ${energyOn(form) ? `battery ${form.battery_wh} Wh` : `night < ${form.max_night_h} h`} · no-Earth < ${form.max_no_earth_h} h${form.min_continuous_lit_h !== "0" ? ` · light ≥ ${form.min_continuous_lit_h} h in a row` : ""}${Number(form.min_total_lit_h) > 0 ? ` · light ≥ ${form.min_total_lit_h} h total` : ""}${form.require_both ? " · Sun+Earth together" : ""}${form.hazards_enabled && form.max_temperature_k ? ` · T < ${form.max_temperature_k} K` : ""}${form.hazards_enabled && form.min_temperature_k ? ` · T ≥ ${form.min_temperature_k} K` : ""}`;

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
      does not change it. For computed results, run moonpark locally with the data —{" "}
      <a href="https://github.com/Pedrojonfg/moonpark#try-it" target="_blank" rel="noreferrer">
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
          {busy && (
            <span className={Classes.TEXT_MUTED} style={{ marginLeft: 6 }}>
              · {stageLabel}
            </span>
          )}
          {dl && (
            <div style={{ marginTop: 8 }} role="status" aria-live="polite">
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 12 }}>
                <span>First use: downloading data (cannot be cancelled)</span>
                <span className={Classes.MONOSPACE_TEXT} style={{ fontVariantNumeric: "tabular-nums" }}>
                  {dl.total > 0 ? Math.min(100, Math.round((100 * dl.done) / dl.total)) : 0} %
                </span>
              </div>
              <ProgressBar
                value={dl.total > 0 ? Math.min(1, dl.done / dl.total) : undefined}
                animate={false}
                stripes={false}
                style={{ margin: "4px 0" }}
              />
              <div
                className={`${Classes.TEXT_MUTED} ${Classes.MONOSPACE_TEXT}`}
                style={{ fontSize: 11, fontVariantNumeric: "tabular-nums" }}
              >
                {dl.file} · {mb(dl.done)} / {mb(dl.total)} MB · {dl.files_done} files, {mb(dl.bytes_done)} MB in total
              </div>
              <div className={Classes.TEXT_MUTED} style={{ fontSize: 11, marginTop: 2 }}>
                Stored in the app cache folder on this machine and not downloaded again; analyses of data you already
                downloaded keep working offline.
              </div>
            </div>
          )}
        </Callout>
      )}
      {error && (
        <Callout intent="danger" title="Planner error" style={{ marginBottom: 8 }}>
          {error}
          {import.meta.env.DEV && !STATIC_DEMO && (
            <div className={Classes.TEXT_MUTED} style={{ marginTop: 8 }}>
              Development: start the API with{" "}
              <code>PYTHONPATH=. python3 -m uvicorn moonpark.api.app:app --port 8000</code>
            </div>
          )}
        </Callout>
      )}
    </>
  );

  if (view === "results" && data) {
    const used = ranWith ?? form;
    const usedSummary = `${used.template_id || "custom"} · step ${used.step_min || "10"} min${energyOn(used) ? ` · battery ${used.battery_wh} Wh` : ` · night < ${used.max_night_h} h`} · no-Earth < ${used.max_no_earth_h} h${used.local_search ? " · best nearby start" : ""}${used.mock ? " · mock" : ""}`;
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
            {used.lat}°, {used.lon}° · {used.start.replace("T", " ")} → {used.end.replace("T", " ")} UTC · {usedSummary}
          </span>
          <span style={{ flex: 1 }} />
          {mock && (
            <Tag minimal intent="warning">
              mock data — not a result
            </Tag>
          )}
        </div>
        {stale && (
          <Callout intent="warning" icon="warning-sign" title="Inputs changed — recalculate" style={{ marginBottom: 8 }}>
            This result was computed with the parameters shown above, not the ones now in the form.
            <div style={{ marginTop: 8 }}>
              <Button intent="primary" icon="play" loading={busy} disabled={needsInvalid} onClick={() => runPlanner()}>
                Recalculate
              </Button>
              {needsInvalid && (
                <span style={{ marginLeft: 8, fontSize: 12, color: "#fa999c" }}>
                  Some mission needs are invalid: use Edit inputs to fix them.
                </span>
              )}
            </div>
          </Callout>
        )}
        {messages}
        <Tabs id="planner-results" selectedTabId={tab} onChange={(id) => setTab(id as "overview" | "best")} renderActiveTabPanelOnly>
          <Tab id="overview" title="Overview" />
          <Tab
            id="best"
            title={hasBoard ? `Best starts (${data.local_search!.leaderboard.length})` : "Best starts"}
          />
        </Tabs>
        <div style={{ opacity: busy || stale ? 0.5 : 1, marginTop: 10 }}>
          {tab === "overview" && (
            <>
              <SiteResult data={data} />
              <p className={Classes.TEXT_MUTED} style={{ margin: "8px 0 0", fontSize: 11 }}>
                Provenance:{" "}
                {data.data_source === "real"
                  ? "horizon mask computed from LOLA DEMs, Sun and Earth from SPICE kernels"
                  : "mocked horizon and sky — not a result"}{" "}
                · score formula {sc?.provenance?.score_formula ?? "—"}
                {data.provenance && (
                  <Button minimal small onClick={() => setProvOpen((o) => !o)} style={{ marginLeft: 6 }}>
                    {provOpen ? "Hide details" : "Details"}
                  </Button>
                )}
              </p>
              {data.provenance && (
                <Collapse isOpen={provOpen}>
                  <ProvenanceDetails p={data.provenance} />
                </Collapse>
              )}
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
          <FormGroup label="Latitude °" labelFor="lat" helperText={latMsg ?? "South polar cap: -90 to -60"} intent={latMsg ? "danger" : "none"}>
            <InputGroup id="lat" value={form.lat} intent={latMsg ? "danger" : "none"} onChange={(e) => setField("lat", e.target.value)} />
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
              {/* Disabled in energy mode, but left editable while invalid so it can be fixed. */}
              <FormGroup label="Night: less than (h)" {...fieldProps("max_night_h", energyOn(form) ? "not used: battery model is on" : "whole hours")} style={{ margin: 0 }}>
                <InputGroup type="number" step={1} min={0} intent={fieldProps("max_night_h").intent} disabled={energyOn(form) && !needProblems.max_night_h} value={form.max_night_h} onChange={(e) => setField("max_night_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="No-Earth gap: less than (h)" {...fieldProps("max_no_earth_h", "whole hours")} style={{ margin: 0 }}>
                <InputGroup type="number" step={1} min={0} intent={fieldProps("max_no_earth_h").intent} value={form.max_no_earth_h} onChange={(e) => setField("max_no_earth_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Min light in a row (h)" {...fieldProps("min_continuous_lit_h", "visibility; whole hours; 0 = no requirement")} style={{ margin: 0 }}>
                <InputGroup type="number" step={1} min={0} intent={fieldProps("min_continuous_lit_h").intent} value={form.min_continuous_lit_h} onChange={(e) => setField("min_continuous_lit_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Min total light (h)" helperText="visibility; 0 = no requirement" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.min_total_lit_h} onChange={(e) => setField("min_total_lit_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Sun lit %" {...fieldProps("sun_lit_percent", "0 to 100")} style={{ margin: 0 }}>
                <InputGroup type="number" min={0} max={100} intent={fieldProps("sun_lit_percent").intent} value={form.sun_lit_percent} onChange={(e) => setField("sun_lit_percent", e.target.value)} />
              </FormGroup>
              <FormGroup label="Earth lit %" {...fieldProps("earth_lit_percent", "0 to 100")} style={{ margin: 0 }}>
                <InputGroup type="number" min={0} max={100} intent={fieldProps("earth_lit_percent").intent} value={form.earth_lit_percent} onChange={(e) => setField("earth_lit_percent", e.target.value)} />
              </FormGroup>
              <FormGroup label="Shadow bridge (h)" {...fieldProps("bridge_h", energyOn(form) ? "not used: battery model is on" : "only without battery data; whole hours, 0 to 48")} style={{ margin: 0 }}>
                <InputGroup type="number" step={1} min={0} max={48} intent={fieldProps("bridge_h").intent} disabled={energyOn(form) && !needProblems.bridge_h} value={form.bridge_h} onChange={(e) => setField("bridge_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Time resolution" helperText="fine sees short light intervals; coarse is faster" style={{ margin: 0 }}>
                <HTMLSelect fill value={form.step_min || "10"} onChange={(e) => setField("step_min", e.target.value)}>
                  <option value="10">Fine · 10 min</option>
                  <option value="60">Coarse · 1 h</option>
                </HTMLSelect>
              </FormGroup>
              <FormGroup label="Temperature: less than (K)" helperText="empty = no limit" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.max_temperature_k ?? ""} onChange={(e) => setField("max_temperature_k", e.target.value)} />
              </FormGroup>
              <FormGroup label="Temperature: at least (K)" helperText="empty = no limit" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.min_temperature_k ?? ""} onChange={(e) => setField("min_temperature_k", e.target.value)} />
              </FormGroup>
              <FormGroup label="Soil resistance: at least (J/m³)" helperText="empty = no limit" style={{ margin: 0 }}>
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

        <div style={{ marginBottom: 8 }}>
          <Button minimal small icon={batteryOpen ? "chevron-down" : "chevron-right"} onClick={() => setBatteryOpen((o) => !o)}>
            Battery (optional)
          </Button>
          <span className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
            {energyOn(form)
              ? "Energy balance on: the score uses the battery instead of “Night: less than”."
              : "Fill capacity, array power and a darkness load to score with a battery balance."}
          </span>
          <Collapse isOpen={batteryOpen}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(11rem, 1fr))",
                gap: "8px 12px",
                padding: "8px 0 0 8px",
              }}
            >
              <FormGroup label="Battery capacity (Wh)" helperText="usable" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.battery_wh} onChange={(e) => setField("battery_wh", e.target.value)} />
              </FormGroup>
              <FormGroup label="Array power (W)" helperText="Sun at normal incidence" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.array_w} onChange={(e) => setField("array_w", e.target.value)} />
              </FormGroup>
              <FormGroup label="Darkness endurance (h)" helperText="or give the load in W" style={{ margin: 0 }}>
                <InputGroup type="number" disabled={Number(form.dark_w) > 0} value={form.endurance_h} onChange={(e) => setField("endurance_h", e.target.value)} />
              </FormGroup>
              <FormGroup label="Darkness load (W)" helperText="survival, incl. heaters" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.dark_w} onChange={(e) => setField("dark_w", e.target.value)} />
              </FormGroup>
              <FormGroup label="Panels" style={{ margin: 0 }}>
                <HTMLSelect fill value={form.panel || "tracking_vertical"} onChange={(e) => setField("panel", e.target.value)}>
                  <option value="tracking_vertical">Vertical, tracking the Sun</option>
                  <option value="fixed_vertical">Vertical, fixed</option>
                  <option value="horizontal">Horizontal</option>
                </HTMLSelect>
              </FormGroup>
              {form.panel === "fixed_vertical" && (
                <FormGroup label="Panel azimuth (°)" helperText="from north, clockwise" style={{ margin: 0 }}>
                  <InputGroup type="number" value={form.panel_az_deg} onChange={(e) => setField("panel_az_deg", e.target.value)} />
                </FormGroup>
              )}
              <FormGroup label="Load when lit (W)" helperText="empty = same as darkness" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.lit_w} onChange={(e) => setField("lit_w", e.target.value)} />
              </FormGroup>
              <FormGroup label="Reserve (%)" helperText="never go below" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.reserve_pct} onChange={(e) => setField("reserve_pct", e.target.value)} />
              </FormGroup>
              <FormGroup label="Charge efficiency (0–1)" helperText="empty = 1" style={{ margin: 0 }}>
                <InputGroup type="number" value={form.charge_eff} onChange={(e) => setField("charge_eff", e.target.value)} />
              </FormGroup>
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
          <Button type="submit" intent="primary" icon="play" disabled={busy || Boolean(latMsg) || needsInvalid} loading={busy}>
            Run planner
          </Button>
          {needsInvalid && (
            <a style={{ fontSize: 12, color: "#fa999c" }} onClick={() => setNeedsOpen(true)}>
              Some mission needs are invalid; fix the fields marked in red under Mission needs.
            </a>
          )}
          <Button type="button" disabled={busy} onClick={() => setForm((f) => ({ ...f, ...DEMO_SITE }))}>
            Demo site (PGDA Site01)
          </Button>
          {data && (
            <Button type="button" icon="timeline-bar-chart" onClick={() => setView("results")}>
              {stale ? "View last result (inputs changed)" : "View last result"}
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

const APPROX_LABEL: Record<string, string> = {
  mask_interval_bounds_pessimistic: "mask intervals taken on the pessimistic side",
  score_sigmas_provisional: "score widths are provisional",
  climatology_not_forecast: "temperatures are climatology, not a forecast",
  mask_from_nearest_1km_cap_cell: "horizon from the nearest 1 km cap cell",
  terrain_gaps_filled_unfavorable: "terrain gaps filled with the unfavourable value",
};

/** Expandable provenance (D-20261118-pj-1bc9; fill notice D-20261118-pj-d90c). */
function ProvenanceDetails({ p }: { p: NonNullable<SitePayload["provenance"]> }) {
  const m = p.mask;
  const fill = p.fill && (p.fill.filled_pixels > 0 || p.fill.out_of_coverage_samples > 0) ? p.fill : null;
  const needs = Object.entries(p.effective_needs ?? {})
    .filter(([, v]) => v != null && !Array.isArray(v) && typeof v !== "object")
    .map(([k, v]) => `${k} ${String(v)}`)
    .join(", ");
  const row = (k: string, v: string | undefined) =>
    v ? (
      <div key={k}>
        <span style={{ display: "inline-block", minWidth: 130 }}>{k}</span>
        <span className={Classes.MONOSPACE_TEXT}>{v}</span>
      </div>
    ) : null;
  return (
    <div className={Classes.TEXT_MUTED} style={{ fontSize: 11, padding: "2px 0 0 8px" }}>
      {row("Engine", p.engine_version)}
      {row("Formula", p.formula_version)}
      {row("Data version", p.data_version ?? undefined)}
      {row("Time step", p.step_min != null ? `${p.step_min} min` : undefined)}
      {row("Observer height", p.observer_height_m != null ? `${p.observer_height_m} m` : undefined)}
      {row("Needs used", needs)}
      {m &&
        row(
          "Horizon mask",
          `requested ${m.requested_lat.toFixed(5)}°, ${m.requested_lon.toFixed(5)}° · used ${m.lat.toFixed(5)}°, ${m.lon.toFixed(5)}° · ${m.distance_m} m apart · ${m.source}`,
        )}
      {fill &&
        row("Terrain gaps", `${fill.filled_pixels} pixels filled, ${fill.out_of_coverage_samples} samples outside coverage (unfavourable values used)`)}
      {p.approximations && p.approximations.length > 0 && row("Approximations", p.approximations.map((a) => APPROX_LABEL[a] ?? a).join("; "))}
    </div>
  );
}
