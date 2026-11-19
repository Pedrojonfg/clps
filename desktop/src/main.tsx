import React from "react";
import ReactDOM from "react-dom/client";
import { FocusStyleManager } from "@blueprintjs/core";
import App from "./App";
import { EngineGate } from "./EngineGate";
import { UpdateGate } from "./UpdateGate";
import { FirstRun } from "./FirstRun";

FocusStyleManager.onlyShowFocusOnTabs();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <EngineGate>
      <UpdateGate>
        <FirstRun>
          <App />
        </FirstRun>
      </UpdateGate>
    </EngineGate>
  </React.StrictMode>,
);
