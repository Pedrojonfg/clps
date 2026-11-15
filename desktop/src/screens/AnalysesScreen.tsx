import {
  Button,
  Callout,
  Classes,
  HTMLTable,
  NonIdealState,
  Tag,
} from "@blueprintjs/core";
import type { SavedAnalysis } from "../types";

type Props = {
  analyses: SavedAnalysis[];
  onOpen: (a: SavedAnalysis) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onClear: () => void;
  onOpen3d: (a: SavedAnalysis) => void;
};

export function AnalysesScreen({
  analyses,
  onOpen,
  onNew,
  onDelete,
  onClear,
  onOpen3d,
}: Props) {
  if (analyses.length === 0) {
    return (
      <NonIdealState
        icon="timeline-events"
        title="No saved analyses yet"
        description="Run the site×time planner; each successful run is kept here on this machine."
        action={
          <Button intent="primary" icon="plus" onClick={onNew}>
            New analysis
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        <p className={Classes.TEXT_MUTED} style={{ margin: 0 }}>
          Stored in this browser / desktop webview (localStorage). Re-opens recompute from
          saved parameters.
        </p>
        <div style={{ display: "flex", gap: 8 }}>
          <Button icon="plus" intent="primary" onClick={onNew}>
            New analysis
          </Button>
          <Button icon="trash" minimal onClick={onClear}>
            Clear all
          </Button>
        </div>
      </div>

      <Callout style={{ marginBottom: 12 }} intent="none">
        Tip: open an analysis, then use <strong>3D first-person</strong> or{" "}
        <strong>Region map</strong> in the nav with the same site/window.
      </Callout>

      <HTMLTable compact striped interactive style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>When</th>
            <th>Label</th>
            <th>Window</th>
            <th>Score</th>
            <th>Source</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {analyses.map((a) => (
            <tr key={a.id}>
              <td style={{ whiteSpace: "nowrap" }}>
                {new Date(a.createdAt).toLocaleString()}
              </td>
              <td>{a.label}</td>
              <td className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
                {a.form.start} → {a.form.end}
              </td>
              <td>
                <Tag
                  minimal
                  intent={a.summary.feasible ? "success" : "danger"}
                >
                  {a.summary.feasible
                    ? a.summary.score.toFixed(3)
                    : "infeasible"}
                </Tag>
              </td>
              <td>
                <Tag minimal>
                  {a.summary.data_source === "real" ? "live" : "mock"}
                </Tag>
              </td>
              <td style={{ whiteSpace: "nowrap" }}>
                <Button small minimal icon="document-open" onClick={() => onOpen(a)}>
                  Open
                </Button>
                <Button small minimal icon="globe" onClick={() => onOpen3d(a)}>
                  3D
                </Button>
                <Button
                  small
                  minimal
                  icon="cross"
                  onClick={() => onDelete(a.id)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </HTMLTable>
    </div>
  );
}
