import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(() => ({
  plugins: [react()],

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
      "/site": "http://127.0.0.1:8000",
      "/mission-templates": "http://127.0.0.1:8000",
      "/deep-search": "http://127.0.0.1:8000",
      "/region-map": "http://127.0.0.1:8000",
      "/map.html": "http://127.0.0.1:8000",
      "/map.js": "http://127.0.0.1:8000",
      "/firstperson.html": "http://127.0.0.1:8000",
      "/firstperson.js": "http://127.0.0.1:8000",
      "/assets": "http://127.0.0.1:8000",
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
