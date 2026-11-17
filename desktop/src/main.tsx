import React from "react";
import ReactDOM from "react-dom/client";
import { FocusStyleManager } from "@blueprintjs/core";
import App from "./App";
import { setApiBase } from "./api";

FocusStyleManager.onlyShowFocusOnTabs();

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);

/** In the desktop app, ask the shell where the bundled engine listens and wait until it answers. */
async function startEngine(): Promise<void> {
  if (!("__TAURI_INTERNALS__" in window)) return;
  const { invoke } = await import("@tauri-apps/api/core");
  const base = await invoke<string>("api_base");
  if (!base) return; // no bundled engine (tauri dev): the Vite proxy serves the API
  setApiBase(base);
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(`${base}/health`)).ok) return;
    } catch {
      /* engine still starting */
    }
    await new Promise((r) => setTimeout(r, 300));
  }
}

root.render(<div style={{ padding: 24, color: "#abb3bf", fontFamily: "sans-serif" }}>Starting the engine…</div>);
startEngine().finally(() =>
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  ),
);
