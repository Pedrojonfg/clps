import { useMemo, useState } from "react";
import { Button, Callout, Classes, Checkbox } from "@blueprintjs/core";
import { STATIC_DEMO, regionMapUrl } from "../api";
import type { PlannerForm } from "../types";

type Props = {
  form: PlannerForm;
};

export function RegionMapScreen({ form }: Props) {
  const [demo, setDemo] = useState(true);
  const [iframeKey, setIframeKey] = useState(0);
  const src = useMemo(() => regionMapUrl(form, demo), [form, demo, iframeKey]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "calc(100vh - 7rem)" }}>
      <div>
        <h2 className={Classes.HEADING} style={{ margin: "0 0 4px" }}>
          Region map (3D Moon)
        </h2>
        <p className={Classes.TEXT_MUTED} style={{ margin: 0 }}>
          Three.js globe with south-pole score cells. Demo mode posts sample rows; turn it off
          after a deep-search / region pipeline has data on the API.
        </p>
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <Checkbox
          checked={demo || STATIC_DEMO}
          disabled={STATIC_DEMO}
          label="Demo region rows (?demo=1)"
          onChange={(e) => {
            setDemo(e.currentTarget.checked);
            setIframeKey((k) => k + 1);
          }}
        />
        <Button
          icon="refresh"
          onClick={() => setIframeKey((k) => k + 1)}
        >
          Reload map
        </Button>
      </div>

      <Callout>
        No Cesium ion token required for this view — it uses the vendored Moon texture under{" "}
        <code>/assets</code>.
      </Callout>

      <iframe
        key={iframeKey}
        title="Region score map"
        src={src}
        style={{
          flex: 1,
          minHeight: 420,
          width: "100%",
          border: "1px solid #3f4556",
          background: "#0a0b0f",
        }}
      />
    </div>
  );
}
