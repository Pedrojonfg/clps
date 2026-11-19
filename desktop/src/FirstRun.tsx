import { useState, type ReactNode } from "react";
import { Button, Callout, Card, Dialog, DialogBody, DialogFooter, Icon, ProgressBar, Tag } from "@blueprintjs/core";
import { STATIC_DEMO } from "./api";

const KEY = "moonpark_first_run_done";
const inTauri = () => "__TAURI_INTERNALS__" in window;

function alreadyDone(): boolean {
  try {
    return localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
}
function markDone() {
  try {
    localStorage.setItem(KEY, "1");
  } catch {
    /* works without storage; the notice will just show again next launch */
  }
}

const MOCK = <Tag minimal>Sample data - not a real analysis</Tag>;

const STEPS: { text: string; art: ReactNode }[] = [
  {
    text: "Pick a landing site on the map, or type its coordinates.",
    art: (
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Icon icon="map-marker" intent="primary" /> <code>-89.50, 0.00</code> {MOCK}
      </div>
    ),
  },
  {
    text: "Choose a mission and a date range, then run the analysis.",
    art: (
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Button small icon="calendar" text="14 days" disabled /> <Button small intent="primary" icon="play" text="Analyse" disabled /> {MOCK}
      </div>
    ),
  },
  {
    text: "Read the sunlight, Earth visibility and hazard results for the site.",
    art: (
      <div>
        <div style={{ fontSize: 12 }}>Sunlight 72%</div>
        <ProgressBar value={0.72} stripes={false} animate={false} intent="warning" />
        <div style={{ fontSize: 12, marginTop: 6 }}>Earth visibility 41%</div>
        <ProgressBar value={0.41} stripes={false} animate={false} intent="primary" />
        <div style={{ marginTop: 6 }}>{MOCK}</div>
      </div>
    ),
  },
  {
    text: "Your analyses are saved in the Documents/Moonpark folder on this computer, so you can reopen and compare them later.",
    art: (
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Icon icon="floppy-disk" /> Site A, 14 days <Icon icon="swap-horizontal" /> Site B {MOCK}
      </div>
    ),
  },
];

/** D-20261118-pj-23ab: one-time, non-dismissable notice about the data download plus a skippable walkthrough. */
export function FirstRun({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(() => !STATIC_DEMO && inTauri() && !alreadyDone());
  const [step, setStep] = useState(-1); // -1 = download notice

  const finish = () => {
    markDone();
    setOpen(false);
  };

  const last = step === STEPS.length - 1;
  return (
    <>
      {/* Children mount only after the notice: nothing may start a download behind the dialog. */}
      {open ? null : children}
      <Dialog
        isOpen={open}
        title={step < 0 ? "Welcome to moonpark" : `Quick tour (${step + 1} of ${STEPS.length})`}
        isCloseButtonShown={false}
        canEscapeKeyClose={false}
        canOutsideClickClose={false}
        style={{ width: 520, maxWidth: "92vw" }}
      >
        <DialogBody>
          {step < 0 ? (
            <>
              <p>
                moonpark computes on this computer. The first time you analyse a site it downloads the data it needs; you will see
                the progress (downloading, processing, waiting) while it runs.
              </p>
              <ul style={{ paddingLeft: 18 }}>
                <li>Horizon masks: about 880 MB in total, but only the parts a site needs are downloaded.</li>
                <li>SPICE kernels (Sun, Earth and Moon positions): about 46 MB.</li>
                <li>Hazard data: up to about 2 GB.</li>
                <li>3D relief: roughly 65 MB for each site you view (estimate).</li>
              </ul>
              <Callout icon="info-sign" compact>
                The downloaded data is stored in the app cache folder on this computer; your saved analyses go to the
                Documents/Moonpark folder. Analyses of data you already downloaded keep working offline; the 3D textured
                Moon needs a connection. The download cannot be cancelled or postponed.
              </Callout>
            </>
          ) : (
            <>
              <p>{STEPS[step].text}</p>
              <Card compact>{STEPS[step].art}</Card>
            </>
          )}
        </DialogBody>
        <DialogFooter
          actions={
            step < 0 ? (
              <Button intent="primary" text="Continue" onClick={() => setStep(0)} />
            ) : last ? (
              <Button intent="primary" text="Start" onClick={finish} />
            ) : (
              <Button intent="primary" text="Next" onClick={() => setStep(step + 1)} />
            )
          }
        >
          {!last && <Button minimal small text="Skip tour" onClick={finish} />}
        </DialogFooter>
      </Dialog>
    </>
  );
}
