import { FormEvent, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import {
  Button,
  Callout,
  Checkbox,
  Classes,
  FormGroup,
  HTMLSelect,
  HTMLTable,
  InputGroup,
  Spinner,
} from "@blueprintjs/core";
import { STATIC_DEMO, fetchSite, fetchTemplates } from "../api";
import { PolarChart } from "../PolarChart";
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
  const [hideGapStars, setHideGapStars] = useState(false);

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
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : String(e));
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  const sc = data?.score;
  const board = data?.local_search?.leaderboard?.filter(
    (r) => !hideGapStars || !r.hazard_gap_star,
  );

  return (
    <div>
      <h2 className={Classes.HEADING} style={{ marginTop: 0 }}>
        New analysis — site×time planner
      </h2>
      <p className={Classes.TEXT_MUTED} style={{ marginTop: 0 }}>
        Polar sky chart: azimuth from north at top. Evaluator on this machine; remote role is
        horizon masks only.
      </p>
      {STATIC_DEMO && (
        <Callout intent="warning" title="Browser demo: mocked data" style={{ marginBottom: 12 }}>
          There is no server behind this page. Every run returns the same sample result: a
          mocked horizon and sample Sun/Earth tracks over 24 h, scored with fixed demo needs, so
          changing the inputs does not change the result. For computed results, run lunar-eval
          locally with the data —{" "}
          <a href="https://github.com/Pedrojonfg/clps#try-it" target="_blank" rel="noreferrer">
            see the README
          </a>
          .
        </Callout>
      )}

      <form onSubmit={runPlanner}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(11rem, 1fr))",
            gap: 12,
            marginBottom: 12,
          }}
        >
          <FormGroup label="Latitude °" labelFor="lat">
            <InputGroup
              id="lat"
              value={form.lat}
              onChange={(e) => setField("lat", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Longitude °" labelFor="lon">
            <InputGroup
              id="lon"
              value={form.lon}
              onChange={(e) => setField("lon", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Start (UTC)" labelFor="start">
            <InputGroup
              id="start"
              type="datetime-local"
              value={form.start}
              onChange={(e) => setField("start", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="End (UTC)" labelFor="end">
            <InputGroup
              id="end"
              type="datetime-local"
              value={form.end}
              onChange={(e) => setField("end", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Step (h)" labelFor="step_h">
            <InputGroup
              id="step_h"
              type="number"
              value={form.step_h}
              onChange={(e) => setField("step_h", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Mission template" labelFor="template">
            <HTMLSelect
              id="template"
              fill
              value={form.template_id}
              onChange={(e) => onTemplateChange(e.target.value)}
            >
              <option value="">Custom</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </HTMLSelect>
          </FormGroup>
          <FormGroup label="Max night (h)">
            <InputGroup
              type="number"
              value={form.max_night_h}
              onChange={(e) => setField("max_night_h", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Max no-Earth (h)">
            <InputGroup
              type="number"
              value={form.max_no_earth_h}
              onChange={(e) => setField("max_no_earth_h", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Min continuous lit (h)">
            <InputGroup
              type="number"
              value={form.min_continuous_lit_h}
              onChange={(e) => setField("min_continuous_lit_h", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Sun lit %">
            <InputGroup
              type="number"
              value={form.sun_lit_percent}
              onChange={(e) => setField("sun_lit_percent", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Earth lit %">
            <InputGroup
              type="number"
              value={form.earth_lit_percent}
              onChange={(e) => setField("earth_lit_percent", e.target.value)}
            />
          </FormGroup>
          <FormGroup label="Shadow bridge (h)">
            <InputGroup
              type="number"
              value={form.bridge_h}
              onChange={(e) => setField("bridge_h", e.target.value)}
            />
          </FormGroup>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 12 }}>
          <Checkbox
            checked={form.require_both}
            label="Require Sun and Earth together"
            onChange={(e) => setField("require_both", e.currentTarget.checked)}
          />
          <Checkbox
            checked={form.hazards_enabled}
            label="Layer-B hazards in score"
            onChange={(e) => setField("hazards_enabled", e.currentTarget.checked)}
          />
          <Checkbox
            checked={form.local_search}
            label="Local search (time slide)"
            onChange={(e) => setField("local_search", e.currentTarget.checked)}
          />
          <Checkbox
            checked={form.mock || STATIC_DEMO}
            disabled={STATIC_DEMO}
            label="Mock data (demo)"
            onChange={(e) => setField("mock", e.currentTarget.checked)}
          />
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
          <Button type="submit" intent="primary" disabled={busy} loading={busy}>
            Run planner
          </Button>
          <Button
            type="button"
            disabled={busy}
            onClick={() => {
              setForm((f) => ({ ...f, ...DEMO_SITE }));
            }}
          >
            Demo site (PGDA Site01)
          </Button>
          <Button type="button" icon="globe" disabled={!data} onClick={onOpen3d}>
            Open in 3D
          </Button>
          <Button type="button" icon="map" disabled={!data} onClick={onOpenMap}>
            Region map
          </Button>
        </div>
      </form>

      {status && (
        <Callout>
          <Spinner size={16} /> {status}
        </Callout>
      )}
      {error && (
        <Callout intent="danger" title="Planner error">
          {error}
          <div className={Classes.TEXT_MUTED} style={{ marginTop: 8 }}>
            Start the API:{" "}
            <code>cd ~/clps && PYTHONPATH=. python3 -m uvicorn api.app:app --port 8000</code>
          </div>
        </Callout>
      )}

      {data && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <section>
            <PolarChart data={data} />
          </section>
          <section>
            <h3 className={Classes.HEADING}>Score</h3>
            <p style={{ fontSize: 28, margin: "0 0 8px", color: "#c9a227" }}>
              {sc?.feasible ? sc.score.toFixed(3) : "0.000 (infeasible)"}
            </p>
            <HTMLTable compact striped style={{ width: "100%" }}>
              <tbody>
                <tr>
                  <td>Longest night</td>
                  <td>{data.series.longest_night_h} h</td>
                </tr>
                <tr>
                  <td>Longest no-Earth</td>
                  <td>{data.series.longest_no_earth_h} h</td>
                </tr>
                <tr>
                  <td>Longest continuous lit</td>
                  <td>{data.series.longest_lit_h ?? "—"} h</td>
                </tr>
                <tr>
                  <td>Any sun ∧ Earth</td>
                  <td>{data.series.any_both ? "yes" : "no"}</td>
                </tr>
                <tr>
                  <td>Hazards</td>
                  <td>{data.hazards_enabled ? "on" : "off"}</td>
                </tr>
              </tbody>
            </HTMLTable>
            <Callout style={{ marginTop: 12 }} title="Provenance">
              {data.data_source === "real" ? "mask: computed/cached" : "mask: mocked"} ·{" "}
              {sc?.provenance?.score_formula ?? "—"}
            </Callout>
          </section>
        </div>
      )}

      {board && board.length > 0 && (
        <section style={{ marginTop: 24 }}>
          <h3 className={Classes.HEADING}>Local search</h3>
          <Checkbox
            checked={hideGapStars}
            label="Hide hazard-gap rows (*)"
            onChange={(e) => setHideGapStars(e.currentTarget.checked)}
          />
          <HTMLTable compact striped style={{ width: "100%" }}>
            <thead>
              <tr>
                <th>Pick</th>
                <th>Start</th>
                <th>Feasible</th>
                <th>Score</th>
                <th>Companion</th>
                <th>Δ h</th>
                <th>km</th>
              </tr>
            </thead>
            <tbody>
              {board.map((r) => {
                const pick =
                  data?.local_search?.pick &&
                  r.window_start === data.local_search.pick.window_start;
                return (
                  <tr key={`${r.window_start}-${r.distance_km}`}>
                    <td>{pick ? "★" : r.hazard_gap_star ? "*" : ""}</td>
                    <td>{r.window_start ?? "—"}</td>
                    <td>{r.feasible ? "yes" : "no"}</td>
                    <td>{Number(r.score).toFixed(3)}</td>
                    <td>{Number(r.companion_score).toFixed(3)}</td>
                    <td>{Number(r.distance_hours).toFixed(1)}</td>
                    <td>{Number(r.distance_km).toFixed(3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </HTMLTable>
        </section>
      )}
    </div>
  );
}
