import { useCallback, useState } from "react";
import {
  Alignment,
  Button,
  Classes,
  Navbar,
  NavbarDivider,
  NavbarGroup,
  NavbarHeading,
  Tag,
} from "@blueprintjs/core";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import { STATIC_DEMO } from "./api";
import {
  clearAnalyses,
  deleteAnalysis,
  loadAnalyses,
  saveAnalysis,
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

function App() {
  const [screen, setScreen] = useState<AppScreen>("planner");
  const [form, setForm] = useState<PlannerForm>(initialForm);
  const [data, setData] = useState<SitePayload | null>(null);
  const [analyses, setAnalyses] = useState<SavedAnalysis[]>(() => loadAnalyses());
  const [plannerBoot, setPlannerBoot] = useState(true);

  const refreshAnalyses = useCallback(() => {
    setAnalyses(loadAnalyses());
  }, []);

  function onSaved(f: PlannerForm, payload: SitePayload) {
    saveAnalysis(f, payload);
    refreshAnalyses();
  }

  function openAnalysis(a: SavedAnalysis) {
    setForm({ ...HAZARD_LIMIT_DEFAULTS, ...a.form });
    setData(null);
    setPlannerBoot(true);
    setScreen("planner");
  }

  function open3dFromAnalysis(a: SavedAnalysis) {
    setForm({ ...HAZARD_LIMIT_DEFAULTS, ...a.form });
    setData(null);
    setScreen("firstperson");
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
        {screen === "analyses" && (
          <AnalysesScreen
            analyses={analyses}
            onOpen={openAnalysis}
            onNew={() => {
              setForm(initialForm);
              setData(null);
              setPlannerBoot(false);
              setScreen("planner");
            }}
            onDelete={(id) => {
              setAnalyses(deleteAnalysis(id));
            }}
            onClear={() => {
              clearAnalyses();
              setAnalyses([]);
            }}
            onOpen3d={open3dFromAnalysis}
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

        {screen === "map" && <RegionMapScreen form={form} onOpenSite={openSite} />}
      </main>
    </div>
  );
}

export default App;
