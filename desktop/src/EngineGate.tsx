import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button, Callout, Spinner } from "@blueprintjs/core";
import { setApiBase } from "./api";

const inTauri = () => "__TAURI_INTERNALS__" in window;

async function call<T>(cmd: string): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>(cmd);
}

/** Wait until the engine at `base` answers /health, or say why it did not. Returns "" when ready. */
async function waitHealthy(base: string): Promise<string> {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    const why = await call<string>("engine_status");
    if (why) return why;
    try {
      if ((await fetch(`${base}/health`)).ok) return "";
    } catch {
      /* engine still starting */
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  return "the engine did not answer within 60 s (/health)";
}

/** Desktop shell only: starts/health-checks the bundled engine, shows a Retry state when it fails or dies. */
export function EngineGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<"starting" | "ready" | "failed">(inTauri() ? "starting" : "ready");
  const [why, setWhy] = useState("");

  const boot = useCallback(async (restart: boolean) => {
    setState("starting");
    const base = await call<string>(restart ? "restart_engine" : "api_base");
    if (!base) {
      // empty base is "no bundled engine" (tauri dev) unless the shell reports a start failure
      const err = await call<string>("engine_status");
      if (err) {
        setWhy(err);
        setState("failed");
        return;
      }
      setState("ready");
      return;
    }
    setApiBase(base);
    const err = await waitHealthy(base);
    setWhy(err);
    setState(err ? "failed" : "ready");
  }, []);

  useEffect(() => {
    if (inTauri()) void boot(false);
  }, [boot]);

  // Engine dying after startup would otherwise surface as a generic fetch error.
  useEffect(() => {
    if (state !== "ready" || !inTauri()) return;
    const id = window.setInterval(async () => {
      const err = await call<string>("engine_status").catch(() => "");
      if (err) {
        setWhy(err);
        setState("failed");
      }
    }, 3000);
    return () => window.clearInterval(id);
  }, [state]);

  if (state === "ready") return <>{children}</>;
  return (
    <div style={{ padding: 24, maxWidth: 560, margin: "0 auto", color: "#abb3bf", fontFamily: "sans-serif" }}>
      {state === "starting" ? (
        <div>
          <Spinner size={16} /> Starting the engine…
        </div>
      ) : (
        <Callout intent="danger" title="The analysis engine is not running">
          moonpark computes on this machine with a bundled engine, and it is not available: {why}.
          <div style={{ marginTop: 12 }}>
            <Button intent="primary" icon="refresh" onClick={() => void boot(true)}>
              Retry
            </Button>
          </div>
          <div style={{ marginTop: 8, fontSize: 12 }}>
            If it keeps failing, close and reopen moonpark, or reinstall it.
          </div>
        </Callout>
      )}
    </div>
  );
}
