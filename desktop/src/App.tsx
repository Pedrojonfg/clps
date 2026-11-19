import { Component, useCallback, useEffect, useState, type ErrorInfo, type ReactNode } from "react";
import {
  Alignment,
  Button,
  Callout,
  Classes,
  Navbar,
  NavbarDivider,
  NavbarGroup,
  NavbarHeading,
  Tag,
} from "@blueprintjs/core";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import { STATIC_DEMO, fetchStoreVersion } from "./api";
import {
  analysesDir,
  clearBrowserAnalyses,
  deleteAnalysis,
  inTauri,
  loadAnalyses,
  openAnalysis as openStoredAnalysis,
  openStoppedSearch,
  saveAnalysis,
  type AnalysisFileError,
} from "./lib/analysesStore";
import { AnalysesScreen } from "./screens/AnalysesScreen";
import { FirstPersonScreen } from "./screens/FirstPersonScreen";
import { PlannerScreen } from "./screens/PlannerScreen";
import { RegionMapScreen } from "./screens/RegionMapScreen";
import {
  AppScreen,
  DEMO_SITE,
  ENERGY_DEFAULTS,
  HAZARD_LIMIT_DEFAULTS,
  PlannerForm,
  SavedAnalysis,
  SearchResume,
  SitePayload,
} from "./types";

const initialForm: PlannerForm = {
  ...DEMO_SITE,
  step_min: "10",
  template_id: "",
  max_night_h: "72",
  max_no_earth_h: "48",
  min_continuous_lit_h: "0",
  min_total_lit_h: "0",
  sun_lit_percent: "0",
  earth_lit_percent: "0",
  bridge_h: "5",
  ...ENERGY_DEFAULTS,
  ...HAZARD_LIMIT_DEFAULTS,
  require_both: false,
  hazards_enabled: true,
  local_search: false,
  mock: false, // real data by default; the browser demo forces mock via STATIC_DEMO
};

const NAV: { id: AppScreen; label: string; icon: "timeline-events" | "plus" | "globe" | "map" }[] =
  [
    { id: "analyses", label: "Past analyses", icon: "timeline-events" },
    { id: "planner", label: "New analysis", icon: "plus" },
    { id: "firstperson", label: "3D first-person", icon: "globe" },
    { id: "map", label: "Region map", icon: "map" },
  ];

/**
 * Keeps a render error in one screen from blanking the whole window: shows the message instead,
 * with a way back. Reset by changing `resetKey` (the screen id), so switching screens retries.
 */
class ScreenErrorBoundary extends Component<
  { resetKey: string; onBack: () => void; children: ReactNode },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Screen render error", error, info.componentStack);
  }

  componentDidUpdate(prev: { resetKey: string }) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null });
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <Callout intent="danger" title="This screen could not be shown" style={{ margin: 16 }}>
        <p>Something went wrong while showing this screen: {this.state.error.message || String(this.state.error)}</p>
        <p className={Classes.TEXT_MUTED}>Your saved analyses are not affected.</p>
        <Button icon="arrow-left" onClick={this.props.onBack}>
          Go to New analysis
        </Button>{" "}
        <Button minimal icon="refresh" onClick={() => this.setState({ error: null })}>
          Try again
        </Button>
      </Callout>
    );
  }
}

function App() {
  const [screen, setScreen] = useState<AppScreen>("planner");
  const [form, setForm] = useState<PlannerForm>(initialForm);
  const [data, setData] = useState<SitePayload | null>(null);
  const [analyses, setAnalyses] = useState<SavedAnalysis[]>([]);
  const [fileErrors, setFileErrors] = useState<AnalysisFileError[]>([]);
  const [storeError, setStoreError] = useState<string | null>(null);
  const [folder, setFolder] = useState<string | null>(null);
  // Data version the engine serves now (GET /store-status), for the recalculation warning; null if unknown.
  const [storeVersion, setStoreVersion] = useState<string | null>(null);
  const [plannerBoot, setPlannerBoot] = useState(true);
  // A stopped region search to continue on the map (D-20261118-pj-1454); consumed once by RegionMapScreen.
  const [searchResume, setSearchResume] = useState<(SearchResume & { form: PlannerForm }) | null>(null);
  const onResumeHandled = useCallback(() => setSearchResume(null), []);

  const refreshAnalyses = useCallback(async () => {
    try {
      const l = await loadAnalyses();
      setAnalyses(l.items);
      setFileErrors(l.errors);
      setStoreError(null);
    } catch (e) {
      setStoreError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refreshAnalyses();
    analysesDir().then(setFolder).catch(() => setFolder(null));
  }, [refreshAnalyses]);

  // Best effort and never blocking: the list works without it (generic warning instead).
  useEffect(() => {
    let live = true;
    void fetchStoreVersion().then((v) => {
      if (live) setStoreVersion(v);
    });
    return () => {
      live = false;
    };
  }, []);

  // MARKED (analyses agent): save is async now; PlannerScreen keeps its sync onSaved callback.
  function onSaved(f: PlannerForm, payload: SitePayload) {
    saveAnalysis(f, payload)
      .then(() => refreshAnalyses())
      .catch((e) => setStoreError(`Could not save this analysis: ${e instanceof Error ? e.message : e}`));
  }

  /** Show the STORED result (no recompute). */
  async function openAnalysis(a: SavedAnalysis) {
    try {
      const rec = await openStoredAnalysis(a.id);
      setForm({ ...HAZARD_LIMIT_DEFAULTS, ...rec.form });
      setData(rec.payload);
      setPlannerBoot(false);
      setScreen("planner");
    } catch (e) {
      setStoreError(`Could not open "${a.label}": ${e instanceof Error ? e.message : e}`);
    }
  }

  /** Recompute from the stored inputs (the result may differ). */
  async function recalculateAnalysis(a: SavedAnalysis) {
    try {
      const rec = await openStoredAnalysis(a.id);
      setForm({ ...HAZARD_LIMIT_DEFAULTS, ...rec.form });
      setData(null);
      setPlannerBoot(true);
      setScreen("planner");
    } catch (e) {
      setStoreError(`Could not open "${a.label}": ${e instanceof Error ? e.message : e}`);
    }
  }

  async function open3dFromAnalysis(a: SavedAnalysis) {
    try {
      const rec = await openStoredAnalysis(a.id);
      setForm({ ...HAZARD_LIMIT_DEFAULTS, ...rec.form });
      setData(null);
      setScreen("firstperson");
    } catch (e) {
      setStoreError(`Could not open "${a.label}": ${e instanceof Error ? e.message : e}`);
    }
  }

  /** Continue a stopped search: same form, rectangle, mode, step and requirements, plus its checkpoint. */
  async function continueSearch(a: SavedAnalysis) {
    try {
      const rec = await openStoppedSearch(a.id);
      setForm({ ...HAZARD_LIMIT_DEFAULTS, ...rec.form });
      setSearchResume(rec);
      setScreen("map");
    } catch (e) {
      setStoreError(`Could not continue "${a.label}": ${e instanceof Error ? e.message : e}`);
    }
  }

  const openSite = useCallback(
    (lat: number, lon: number, target: "planner" | "firstperson") => {
      setForm((f) => ({ ...f, lat: lat.toFixed(5), lon: lon.toFixed(5) }));
      setData(null);
      setPlannerBoot(true);
      setScreen(target);
    },
    [],
  );

  return (
    <div className={Classes.DARK} style={{ minHeight: "100vh" }}>
      <Navbar>
        <NavbarGroup align={Alignment.LEFT}>
          <NavbarHeading>moonpark</NavbarHeading>
          {STATIC_DEMO && (
            <Tag intent="warning" style={{ marginRight: 8 }}>
              Browser demo · mocked data
            </Tag>
          )}
          <Tag minimal intent={data?.data_source === "real" ? "success" : "warning"}>
            {data
              ? data.data_source === "real"
                ? "Live · kernels + cached mask"
                : "Mock data"
              : "Ready"}
          </Tag>
          <NavbarDivider />
          {NAV.map((item) => (
            <Button
              key={item.id}
              minimal
              active={screen === item.id}
              icon={item.icon}
              text={item.label}
              onClick={() => setScreen(item.id)}
            />
          ))}
        </NavbarGroup>
      </Navbar>

      <main
        style={{
          padding: screen === "firstperson" || screen === "map" ? "8px 12px" : 16,
          maxWidth: screen === "firstperson" || screen === "map" ? "100%" : 960,
          margin: "0 auto",
        }}
      >
        <ScreenErrorBoundary resetKey={screen} onBack={() => setScreen("planner")}>
        {screen === "analyses" && (
          <AnalysesScreen
            analyses={analyses}
            fileErrors={fileErrors}
            storeError={storeError}
            folder={folder}
            currentDataVersion={storeVersion}
            onOpen={openAnalysis}
            onRecalculate={recalculateAnalysis}
            onNew={() => {
              setForm(initialForm);
              setData(null);
              setPlannerBoot(false);
              setScreen("planner");
            }}
            onDelete={async (id) => {
              try {
                await deleteAnalysis(id);
              } catch (e) {
                setStoreError(`Could not delete: ${e instanceof Error ? e.message : e}`);
              }
              await refreshAnalyses();
            }}
            onClear={
              inTauri()
                ? undefined
                : () => {
                    clearBrowserAnalyses();
                    setAnalyses([]);
                  }
            }
            onOpen3d={open3dFromAnalysis}
            onContinueSearch={continueSearch}
          />
        )}

        {screen === "planner" && (
          <PlannerScreen
            form={form}
            setForm={setForm}
            data={data}
            setData={setData}
            onSaved={onSaved}
            onOpen3d={() => setScreen("firstperson")}
            onOpenMap={() => setScreen("map")}
            autoRun={plannerBoot}
          />
        )}

        {screen === "firstperson" && (
          <FirstPersonScreen form={form} />
        )}

        {screen === "map" && (
          <RegionMapScreen
            form={form}
            onOpenSite={openSite}
            resume={searchResume}
            onResumeHandled={onResumeHandled}
            onSearchStoreChanged={refreshAnalyses}
          />
        )}
        </ScreenErrorBoundary>
      </main>
    </div>
  );
}

export default App;
