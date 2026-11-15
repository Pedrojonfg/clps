import { useMemo, useState } from "react";
import {
  Button,
  Callout,
  Classes,
  FormGroup,
  InputGroup,
  Tag,
} from "@blueprintjs/core";
import { firstPersonUrl } from "../api";
import { loadIonToken, saveIonToken } from "../lib/ionToken";
import type { PlannerForm } from "../types";

type Props = {
  form: PlannerForm;
  hasResult: boolean;
};

export function FirstPersonScreen({ form, hasResult }: Props) {
  const [tokenDraft, setTokenDraft] = useState(() => loadIonToken());
  const [savedToken, setSavedToken] = useState(() => loadIonToken());
  const [iframeKey, setIframeKey] = useState(0);

  const src = useMemo(() => firstPersonUrl(form), [form, iframeKey]);

  function persistToken() {
    saveIonToken(tokenDraft);
    setSavedToken(tokenDraft.trim());
    setIframeKey((k) => k + 1);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "calc(100vh - 7rem)" }}>
      <div>
        <h2 className={Classes.HEADING} style={{ margin: "0 0 4px" }}>
          3D first-person
        </h2>
        <p className={Classes.TEXT_MUTED} style={{ margin: 0 }}>
          Cesium Moon terrain + your horizon mask, Sun, and Earth markers for the active
          site/window. Needs a free Cesium ion token for the 3D Moon asset.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr auto",
          gap: 12,
          alignItems: "end",
        }}
      >
        <FormGroup
          label="Cesium ion access token"
          labelFor="ion"
          helperText="Create a free token at https://ion.cesium.com/tokens — Asset ID 2684829 (Moon). Stored only in localStorage on this machine."
        >
          <InputGroup
            id="ion"
            type="password"
            value={tokenDraft}
            placeholder="eyJhbGciOi…"
            onChange={(e) => setTokenDraft(e.target.value)}
            rightElement={
              <Tag minimal intent={savedToken ? "success" : "warning"}>
                {savedToken ? "saved" : "missing"}
              </Tag>
            }
          />
        </FormGroup>
        <Button intent="primary" icon="floppy-disk" onClick={persistToken}>
          Save & reload 3D
        </Button>
      </div>

      {!hasResult && (
        <Callout intent="warning">
          No planner result in memory yet — the view will use the form site and may fall back to
          mock sky. Run an analysis first for a consistent overlay.
        </Callout>
      )}

      {!savedToken && (
        <Callout intent="primary" title="What you need to do (Ion)">
          <ol style={{ margin: "8px 0 0", paddingLeft: 20 }}>
            <li>
              Sign up / log in at{" "}
              <a href="https://ion.cesium.com/" target="_blank" rel="noreferrer">
                ion.cesium.com
              </a>
            </li>
            <li>
              Open{" "}
              <a href="https://ion.cesium.com/tokens" target="_blank" rel="noreferrer">
                Access Tokens
              </a>{" "}
              → create a token (default scopes are fine for the Moon asset).
            </li>
            <li>Paste it above and click Save & reload 3D.</li>
          </ol>
          Without a token you still get a 2D canvas fallback inside the frame.
        </Callout>
      )}

      <iframe
        key={iframeKey}
        title="First-person Cesium"
        src={src}
        style={{
          flex: 1,
          minHeight: 420,
          width: "100%",
          border: "1px solid #3f4556",
          background: "#1a1c22",
        }}
      />
    </div>
  );
}
