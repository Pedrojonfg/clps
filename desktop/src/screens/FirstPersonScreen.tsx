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
  const [tokenOpen, setTokenOpen] = useState(() => !loadIonToken());
  const [iframeKey, setIframeKey] = useState(0);

  const src = useMemo(() => firstPersonUrl(form), [form, iframeKey]);

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
          {savedToken ? "Cesium ion token saved" : "No Cesium ion token"}
        </Tag>
        <Button
          small
          minimal
          icon="key"
          active={tokenOpen}
          aria-expanded={tokenOpen}
          onClick={() => setTokenOpen((o) => !o)}
        >
          {savedToken ? "Change token" : "Add token"}
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
            The 3D backdrop needs a free Cesium ion account: 1) create a token at{" "}
            <a href="https://ion.cesium.com/tokens" target="_blank" rel="noreferrer">
              ion.cesium.com/tokens
            </a>
            ; 2) add{" "}
            <a href="https://ion.cesium.com/assetdepot/2684829" target="_blank" rel="noreferrer">
              Cesium Moon Terrain (asset 2684829)
            </a>{" "}
            to “My Assets” — a token alone cannot load it; 3) paste the token here. It is kept only in
            this machine's localStorage. Without it the view falls back to the 2D mask panorama.
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
