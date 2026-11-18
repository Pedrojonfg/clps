import React from "react";
import ReactDOM from "react-dom/client";
import { FocusStyleManager } from "@blueprintjs/core";
import App from "./App";
import { EngineGate } from "./EngineGate";

FocusStyleManager.onlyShowFocusOnTabs();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <EngineGate>
      <App />
    </EngineGate>
  </React.StrictMode>,
);
