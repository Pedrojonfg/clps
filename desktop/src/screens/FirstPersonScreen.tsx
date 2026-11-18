import { useMemo, useState } from "react";
import { Button, Classes, Collapse, ControlGroup, InputGroup, Tag } from "@blueprintjs/core";
import { firstPersonUrl } from "../api";
import { loadIonToken, saveIonToken } from "../lib/ionToken";
import type { PlannerForm } from "../types";

type Props = {
  form: PlannerForm;
};

export function FirstPersonScreen({ form }: Props) {
  const [tokenDraft, setTokenDraft] = useState(() => loadIonToken());
  const [savedToken, setSavedToken] = useState(() => loadIonToken());
  const [tokenOpen, setTokenOpen] = useState(false); // the token is optional now: our own relief needs none
  const [iframeKey, setIframeKey] = useState(0);

  // Light 2D panorama on request (slow GPU / no token). Remembered per machine.
  const [mode2d, setMode2d] = useState(() => {
    try {
      return localStorage.getItem("moonpark:firstPerson2d") === "1";
    } catch {
      return false;
    }
  });
  // Cesium ion Moon instead of our own LOLA relief; needs a token. Remembered per machine.
  const [preferIon, setPreferIon] = useState(() => {
    try {
      return localStorage.getItem("moonpark:firstPersonIon") === "1";
    } catch {
      return false;
    }
  });
  const src = useMemo(() => firstPersonUrl(form, mode2d, preferIon && !!savedToken), [form, iframeKey, mode2d, preferIon, savedToken]);

  function toggleIon() {
    const next = !preferIon;
    setPreferIon(next);
    try {
      localStorage.setItem("moonpark:firstPersonIon", next ? "1" : "0");
    } catch {
      /* not remembered */
    }
  }

  function toggleMode() {
    const next = !mode2d;
    setMode2d(next);
    try {
      localStorage.setItem("moonpark:firstPerson2d", next ? "1" : "0");
    } catch {
      /* private mode: the choice just isn't remembered */
    }
  }

  function persistToken() {
    saveIonToken(tokenDraft);
    setSavedToken(tokenDraft.trim());
    setTokenOpen(!tokenDraft.trim());
    setIframeKey((k) => k + 1);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, height: "calc(100vh - 82px)" }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", minHeight: 24 }}>
        <span className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
          Site {Number(form.lat).toFixed(4)}°, {Number(form.lon).toFixed(4)}° · {form.start.replace("T", " ")} →{" "}
          {form.end.replace("T", " ")} UTC · same site and window as the planner
        </span>
        <span style={{ flex: 1 }} />
        <Tag minimal intent={savedToken ? "success" : "warning"}>
          {savedToken ? "Cesium ion token saved (optional)" : "No Cesium ion token (optional)"}
        </Tag>
        {savedToken && (
          <Button
            small
            minimal
            icon="globe"
            intent={preferIon ? "primary" : "none"}
            onClick={toggleIon}
            title={preferIon ? "Back to our own LOLA relief" : "Use the Cesium ion Moon terrain (textured, higher resolution) instead of our own relief"}
          >
            {preferIon ? "Use our relief" : "Use Cesium ion"}
          </Button>
        )}
        <Button
          small
          minimal
          icon="key"
          active={tokenOpen}
          aria-expanded={tokenOpen}
          onClick={() => setTokenOpen((o) => !o)}
        >
          {savedToken ? "Change ion token" : "Add ion token"}
        </Button>
        <Button
          small
          minimal
          icon={mode2d ? "cube" : "heat-grid"}
          intent={mode2d ? "primary" : "none"}
          onClick={toggleMode}
           title={mode2d ? "Load the 3D view (needs a GPU)" : "Use the light 2D horizon panorama instead of the 3D view"}
        >
          {mode2d ? "Switch to 3D" : "Use 2D view"}
        </Button>
        <Button small minimal icon="refresh" onClick={() => setIframeKey((k) => k + 1)}>
          Reload view
        </Button>
      </div>

      <Collapse isOpen={tokenOpen}>
        <div className={Classes.TEXT_MUTED} style={{ fontSize: 12, display: "grid", gap: 6, paddingBottom: 4 }}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              persistToken();
            }}
          >
            <ControlGroup fill>
              <InputGroup
                aria-label="Cesium ion access token"
                type="password"
                value={tokenDraft}
                placeholder="Cesium ion access token (eyJhbGciOi…)"
                onChange={(e) => setTokenDraft(e.target.value)}
              />
              <Button type="submit" intent="primary" icon="floppy-disk" style={{ flex: "none" }}>
                Save and reload
              </Button>
            </ControlGroup>
          </form>
          <span>
            Optional. The 3D view uses our own LOLA relief and needs no token. For the textured, higher-resolution
            Cesium Moon instead, or as a stand-in while the API has no DEM for a site, use a free Cesium ion account: 1) create a token at{" "}
            <a href="https://ion.cesium.com/tokens" target="_blank" rel="noreferrer">
              ion.cesium.com/tokens
            </a>
            ; 2) add{" "}
            <a href="https://ion.cesium.com/assetdepot/2684829" target="_blank" rel="noreferrer">
              Cesium Moon Terrain (asset 2684829)
            </a>{" "}
            to “My Assets” — a token alone cannot load it; 3) paste the token here. It is kept only in
            this machine's localStorage, then choose “Use Cesium ion”.
          </span>
        </div>
      </Collapse>

      <iframe
        key={iframeKey}
        title="First-person site view"
        src={src}
        style={{ flex: 1, minHeight: 320, width: "100%", border: "1px solid #404854", borderRadius: 4, background: "#111418" }}
      />
    </div>
  );
}
