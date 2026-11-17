// Copy the embedded pages (first-person view, region map) next to the built UI so the desktop app
// serves them from its own origin (shared localStorage with the shell, no server needed for them).
import { cpSync } from "node:fs";

const web = new URL("../../web/", import.meta.url);
const dist = new URL("../dist/", import.meta.url);
for (const f of ["map.html", "map.js", "firstperson.html", "firstperson.js"]) {
  cpSync(new URL(f, web), new URL(f, dist));
}
cpSync(new URL("assets/", web), new URL("assets/", dist), { recursive: true });
