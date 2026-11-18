#!/usr/bin/env python3
"""Download Diviner PCP diurnal tabs and convert to compact npz (D-41a2).

Each season×lst_bin becomes data/hazards/pcp/{summer|winter}/ltimXX.npz with
float32 arrays x,y,tbol (x,y = pole distances / 1737.4 km). Source tabs are
deleted after a successful convert to keep disk under control.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

SEASONS = ("summer", "winter")
SEASON_TOKEN = {"summer": "sum", "winter": "win"}
N_BINS = 96
R_KM = 1737.4


def _tab_name(season: str, bin_1based: int) -> str:
    tok = SEASON_TOKEN[season]
    return f"pcp_avg_tbol_pols_{tok}_ltim{bin_1based:02d}_240.tab"


def _npz_path(dest: Path, season: str, bin_1based: int) -> Path:
    return dest / season / f"ltim{bin_1based:02d}.npz"


def _curl(url: str, path: Path, ua: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "curl",
        "-L",
        "--fail",
        "--retry",
        "5",
        "--retry-all-errors",
        "-A",
        ua,
        "-C",
        "-",
        "-o",
        str(path),
        url,
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def convert_tab(tab_path: Path, npz_path: Path) -> None:
    data = np.loadtxt(tab_path, delimiter=",", skiprows=1, dtype=np.float64)
    if data.ndim != 2 or data.shape[1] < 5:
        raise ValueError(f"unexpected PCP shape {data.shape} in {tab_path}")
    x = data[:, 0].astype(np.float32)
    y = data[:, 1].astype(np.float32)
    tbol = data[:, 4].astype(np.float32)
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = npz_path.with_name(npz_path.stem + ".tmp.npz")
    np.savez_compressed(tmp, x=x, y=y, tbol=tbol, r_km=np.float32(R_KM))
    tmp.replace(npz_path)


def ensure_bin(dest: Path, base: str, ua: str, season: str, bin_1based: int) -> Path:
    out = _npz_path(dest, season, bin_1based)
    if out.is_file():
        return out
    name = _tab_name(season, bin_1based)
    tab = dest / "_tabs" / name
    url = f"{base.rstrip('/')}/{name}"
    print(f"==> {season} ltim{bin_1based:02d}", flush=True)
    _curl(url, tab, ua)
    convert_tab(tab, out)
    tab.unlink(missing_ok=True)
    print(f"    ok {out.name} ({out.stat().st_size // 10**6} MB)", flush=True)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--base", type=str, required=True)
    parser.add_argument("--ua", type=str, default="moonpark/0.1")
    parser.add_argument("--season", choices=["summer", "winter", "both"], default="both")
    parser.add_argument("--bins", type=str, default="", help="Comma 1-based bins; empty=all 1..96")
    parser.add_argument("--jobs", type=int, default=4, help="Parallel downloads")
    args = parser.parse_args()

    seasons = SEASONS if args.season == "both" else (args.season,)
    if args.bins.strip():
        bins = [int(x) for x in args.bins.split(",") if x.strip()]
    else:
        bins = list(range(1, N_BINS + 1))

    work = [(season, b) for season in seasons for b in bins]
    jobs = max(1, int(args.jobs))
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futs = {
            pool.submit(ensure_bin, args.dest, args.base, args.ua, season, b): (season, b)
            for season, b in work
        }
        for fut in as_completed(futs):
            season, b = futs[fut]
            try:
                fut.result()
            except Exception as exc:  # noqa: BLE001 — report and continue siblings
                msg = f"{season} ltim{b:02d}: {exc}"
                errors.append(msg)
                print(f"FAIL {msg}", flush=True)

    print(f"pcp bins ready under {args.dest}", flush=True)
    if errors:
        print(f"{len(errors)} failures", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
