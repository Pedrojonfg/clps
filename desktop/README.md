# lunar-eval desktop

Tauri 2 + React + Blueprint shell for the product UI (`D-bdaf`, `D-50a5`, `D-b6fe`).
Static `web/` is not this product (`D-c973`).

## Prerequisites

- Node.js + npm
- Rust (`rustup`)
- Linux/WSL: Tauri system libs — see https://tauri.app/start/prerequisites/  
  (needs `sudo` for `libwebkit2gtk-4.1-dev`, `librsvg2-dev`, etc.)

## Commands

```bash
cd desktop
npm install
npm run build          # front only (tsc + vite)
npm run tauri dev      # native window (needs system libs)
npm run tauri build    # installable binary
```

Python evaluator bridge: not wired yet (deferred after shell).
