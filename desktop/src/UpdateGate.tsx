import { useEffect, useState, type ReactNode } from "react";
import { Button, NonIdealState } from "@blueprintjs/core";
import { apiUrl, STATIC_DEMO } from "./api";
import { isOlder } from "./lib/version";

const RELEASES_URL = "https://github.com/Pedrojonfg/moonpark/releases/latest";
const inTauri = () => "__TAURI_INTERNALS__" in window;

async function openReleases() {
  try {
    const { openUrl } = await import("@tauri-apps/plugin-opener");
    await openUrl(RELEASES_URL);
  } catch {
    window.open(RELEASES_URL, "_blank", "noopener");
  }
}

/** D-20261118-pj-62d3: blocks the app when the data store needs a newer app. Any failure lets the app through. */
export function UpdateGate({ children }: { children: ReactNode }) {
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    if (STATIC_DEMO || !inTauri()) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(apiUrl("/store-status"));
        if (!res.ok) return;
        const body = (await res.json()) as { min_app_version?: string | null };
        const min = body.min_app_version ?? "";
        if (!min) return;
        const { getVersion } = await import("@tauri-apps/api/app");
        if (!cancelled && isOlder(await getVersion(), min)) setBlocked(true);
      } catch {
        /* unreachable store or failed call never blocks */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!blocked) return <>{children}</>;
  return (
    <div className="bp6-dark" style={{ position: "fixed", inset: 0, display: "grid", placeItems: "center", background: "#1c2127" }}>
      <NonIdealState
        icon="updated"
        title="A newer version is required"
        description="Please download the latest version; your saved analyses stay in your Documents folder."
        action={
          <Button intent="primary" icon="download" onClick={() => void openReleases()}>
            Open download page
          </Button>
        }
      />
    </div>
  );
}
