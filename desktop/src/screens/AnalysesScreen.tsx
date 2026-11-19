import {
  Alert,
  Button,
  Callout,
  Classes,
  HTMLTable,
  NonIdealState,
  Tag,
} from "@blueprintjs/core";
import { useState } from "react";
import type { SavedAnalysis } from "../types";
import type { AnalysisFileError } from "../lib/analysesStore";

type Props = {
  analyses: SavedAnalysis[];
  fileErrors?: AnalysisFileError[];
  storeError?: string | null;
  folder?: string | null;
  /** Data version the engine has now, when known; compared with the one stored in each analysis. */
  currentDataVersion?: string | null;
  onOpen: (a: SavedAnalysis) => void;
  onRecalculate: (a: SavedAnalysis) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  /** Browser fallback only. */
  onClear?: () => void;
  onOpen3d: (a: SavedAnalysis) => void;
  /** Continue a stopped region search (kind "search") on the region map (D-20261118-pj-1454). */
  onContinueSearch?: (a: SavedAnalysis) => void;
};

export function AnalysesScreen({
  analyses,
  fileErrors = [],
  storeError = null,
  folder = null,
  currentDataVersion = null,
  onOpen,
  onRecalculate,
  onNew,
  onDelete,
  onClear,
  onOpen3d,
  onContinueSearch,
}: Props) {
  const [pendingRecalc, setPendingRecalc] = useState<SavedAnalysis | null>(null);
  const [pendingDelete, setPendingDelete] = useState<SavedAnalysis | null>(null);
  // List rows carry only start/end from the form (see SavedAnalysis); any of them may be missing.
  const windowText = (a: SavedAnalysis) =>
    a.start || a.end ? `${a.start ?? "?"} → ${a.end ?? "?"}` : "—";

  const recalcWarning = (a: SavedAnalysis): string => {
    if (currentDataVersion && a.dataVersion && currentDataVersion !== a.dataVersion) {
      return `This analysis used data version ${a.dataVersion}; the current data is ${currentDataVersion}. The recalculated result can differ.`;
    }
    return "Data or the app may have changed since this analysis; the recalculated result can differ.";
  };

  const problems = (
    <>
      {storeError && (
        <Callout intent="danger" style={{ marginBottom: 12 }}>
          {storeError}
        </Callout>
      )}
      {fileErrors.map((e) => (
        <Callout key={e.file} intent="warning" icon="warning-sign" style={{ marginBottom: 8 }}>
          <strong>{e.file}</strong> could not be read: {e.error}. Other analyses are not affected; you
          can delete or fix the file by hand.
        </Callout>
      ))}
    </>
  );

  if (analyses.length === 0) {
    return (
      <div>
        {problems}
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
        {folder && (
          <p className={Classes.TEXT_MUTED} style={{ fontSize: 11, textAlign: "center" }}>
            Saved in {folder}
          </p>
        )}
      </div>
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
          Each analysis is saved as a file{folder ? <> in <code style={{ fontSize: 11 }}>{folder}</code></> : " (browser storage in this mode)"}.
          Open shows the stored result.
        </p>
        <div style={{ display: "flex", gap: 8 }}>
          <Button icon="plus" intent="primary" onClick={onNew}>
            New analysis
          </Button>
          {onClear && (
            <Button icon="trash" minimal onClick={onClear}>
              Clear all
            </Button>
          )}
        </div>
      </div>

      {problems}

      {pendingRecalc && (
        <Callout intent="warning" title="Recalculate this analysis?" style={{ marginBottom: 12 }}>
          <p>{recalcWarning(pendingRecalc)}</p>
          <Button
            intent="warning"
            icon="refresh"
            onClick={() => {
              const a = pendingRecalc;
              setPendingRecalc(null);
              onRecalculate(a);
            }}
          >
            Recalculate
          </Button>{" "}
          <Button minimal onClick={() => setPendingRecalc(null)}>
            Cancel
          </Button>
        </Callout>
      )}

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
          {analyses.map((a) =>
            a.kind === "search" ? (
              <tr key={a.id}>
                <td style={{ whiteSpace: "nowrap" }}>{whenText(a.createdAt)}</td>
                <td>{a.label}</td>
                <td className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
                  {windowText(a)}
                </td>
                <td>
                  <Tag minimal intent="primary">Search (stopped)</Tag>
                </td>
                <td>
                  <Tag minimal>{a.summary?.data_source === "mock" ? "mock" : "live"}</Tag>
                </td>
                <td style={{ whiteSpace: "nowrap" }}>
                  <Button
                    small
                    minimal
                    icon="play"
                    disabled={!onContinueSearch}
                    title="Continue this search on the region map from where it stopped"
                    onClick={() => onContinueSearch?.(a)}
                  >
                    Continue
                  </Button>
                  <Button
                    small
                    minimal
                    icon="cross"
                    title="Delete this stopped search"
                    onClick={() => setPendingDelete(a)}
                  />
                </td>
              </tr>
            ) : (
            <tr key={a.id}>
              <td style={{ whiteSpace: "nowrap" }}>
                {whenText(a.createdAt)}
              </td>
              <td>{a.label}</td>
              <td className={Classes.TEXT_MUTED} style={{ fontSize: 12 }}>
                {windowText(a)}
              </td>
              <td>
                <Tag
                  minimal
                  intent={a.summary?.feasible ? "success" : "danger"}
                >
                  {a.summary?.feasible
                    ? Number(a.summary.score ?? 0).toFixed(3)
                    : "infeasible"}
                </Tag>
              </td>
              <td>
                <Tag minimal>
                  {a.summary?.data_source === "real" ? "live" : "mock"}
                </Tag>
              </td>
              <td style={{ whiteSpace: "nowrap" }}>
                <Button small minimal icon="document-open" onClick={() => onOpen(a)}>
                  Open
                </Button>
                <Button small minimal icon="refresh" title="Recalculate (result may differ)" onClick={() => setPendingRecalc(a)}>
                  Recalculate
                </Button>
                <Button small minimal icon="globe" onClick={() => onOpen3d(a)}>
                  3D
                </Button>
                <Button
                  small
                  minimal
                  icon="cross"
                  title="Delete this saved analysis"
                  onClick={() => setPendingDelete(a)}
                />
              </td>
            </tr>
            ),
          )}
        </tbody>
      </HTMLTable>
      {folder && (
        <p className={Classes.TEXT_MUTED} style={{ fontSize: 11, marginTop: 8 }}>
          Folder: {folder}
        </p>
      )}
      <Alert
        className={Classes.DARK}
        isOpen={pendingDelete !== null}
        intent="danger"
        icon="trash"
        confirmButtonText="Delete"
        cancelButtonText="Cancel"
        canEscapeKeyCancel
        canOutsideClickCancel
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          const a = pendingDelete;
          setPendingDelete(null);
          if (a) onDelete(a.id);
        }}
      >
        {pendingDelete?.kind === "search" ? (
          <p>
            Delete the stopped search <strong>{pendingDelete.label}</strong>? It can no longer be continued.
          </p>
        ) : (
          <p>
            Delete the saved analysis <strong>{pendingDelete?.label}</strong>? This removes its file.
          </p>
        )}
      </Alert>
    </div>
  );
}

/** Creation time for the list; the raw text when the stored value is not a date. */
function whenText(createdAt: string): string {
  const d = new Date(createdAt);
  return Number.isNaN(d.getTime()) ? String(createdAt ?? "") : d.toLocaleString();
}
