"""Entry point of the bundled engine the desktop app starts as a Tauri sidecar.

Serves the same FastAPI app on 127.0.0.1 only; the app picks the port. # per D-8c03
"""

from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--cache", help="directory for downloaded masks/kernels/hazards")
    args = ap.parse_args()

    if args.cache:
        import os

        os.environ["LUNAR_CACHE"] = args.cache

    import uvicorn

    from api.app import app

    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
