import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;
// Where the local API listens; override to run a second dev stack beside the default one.
const api = process.env.MOONPARK_API ?? "http://127.0.0.1:8000";

// https://vite.dev/config/
export default defineConfig(() => ({
  plugins: [react()],
  // Static Pages demo is served from a sub-path; relative asset URLs work anywhere.
  base: process.env.VITE_STATIC_DEMO === "1" ? "./" : "/",

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent Vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    host: host || "0.0.0.0",
    proxy: {
      "/site": api,
      "/progress": api,
      "/mission-templates": api,
      "/deep-search": api,
      "/region-map": api,
      "/map.html": api,
      "/map.js": api,
      "/firstperson.html": api,
      "/firstperson.js": api,
      "/assets": api,
    },
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      // 3. tell Vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
}));
