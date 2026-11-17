#!/usr/bin/env python3
"""Publish the static data store to the Cloudflare R2 bucket.

Two groups, each with its own checksummed manifest.json:

  cap_1km  data/masks/cap_1km/            index.parquet, summary.json, tiles/*   (~880 MB)
  data     data/                          kernels/*, hazards/pcp/{summer,winter}/*.npz,
                                          dem/LDSM_80S_80MPP_ADJ.TIF, dem/LPSR_80S_20MPP_ADJ.TIF (~2.5 GB)

Credentials come from the environment, never from git:

    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
    R2_BUCKET (default: lunar-masks)

Usage:
    python scripts/publish_masks.py --dry-run            # build manifests only, no network
    python scripts/publish_masks.py                      # upload both groups (pip install boto3)
    python scripts/publish_masks.py --only data          # or: --only cap_1km
# per D-20261115-pj-8c03
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
CAP = DATA / "masks" / "cap_1km"
KERNELS = (
    "naif0012.tls",
    "pck00011.tpc",
    "moon_pa_de440_200625.bpc",
    "moon_de440_250416.tf",
    "moon_assoc_me.tf",
    "de440s.bsp",
)
DEM_FILES = ("LDSM_80S_80MPP_ADJ.TIF", "LPSR_80S_20MPP_ADJ.TIF")
CONTENT_TYPES = {".npy": "application/octet-stream", ".parquet": "application/octet-stream"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cap_files() -> list[Path]:
    files = [CAP / n for n in ("index.parquet", "summary.json") if (CAP / n).is_file()]
    return files + sorted((CAP / "tiles").glob("t*_*.*"))


def data_files() -> list[Path]:
    files = [DATA / "kernels" / n for n in KERNELS]
    for season in ("summer", "winter"):
        files += sorted((DATA / "hazards" / "pcp" / season).glob("ltim*.npz"))
    files += [DATA / "dem" / n for n in DEM_FILES]
    missing = [p for p in files if not p.is_file()]
    if missing:
        raise SystemExit("missing data files: " + ", ".join(str(p.relative_to(DATA)) for p in missing[:5]))
    return files


GROUPS = {
    # name: (root the manifest keys are relative to, file lister, extra manifest fields)
    "cap_1km": (CAP, cap_files),
    "data": (DATA, data_files),
}


def build_manifest(name: str) -> dict:
    root, lister = GROUPS[name]
    files = {}
    for p in lister():
        rel = p.relative_to(root).as_posix()
        files[rel] = {"size": p.stat().st_size, "sha256": sha256(p)}
        print(f"  hashed {name}/{rel}", file=sys.stderr)
    extra: dict = {}
    if name == "cap_1km":
        s = json.loads((CAP / "summary.json").read_text(encoding="utf-8"))
        extra = {k: s.get(k) for k in ("schedule_version", "spacing_m", "observer_height_m", "n_masks")}
    return {"schema": 1, **extra, "files": files}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="write manifests locally, upload nothing")
    ap.add_argument("--only", choices=sorted(GROUPS), help="publish one group only")
    args = ap.parse_args()
    names = [args.only] if args.only else sorted(GROUPS)

    if "cap_1km" in names and not (CAP / "index.parquet").is_file():
        print(f"no cap at {CAP}", file=sys.stderr)
        return 1

    manifests = {}
    for name in names:
        m = build_manifest(name)
        out = GROUPS[name][0] / ("manifest.json" if name == "cap_1km" else "store-manifest.json")
        out.write_text(json.dumps(m, indent=1), encoding="utf-8")
        total = sum(f["size"] for f in m["files"].values())
        print(f"{name}: {len(m['files'])} files, {total / 1e6:.0f} MB -> {out}")
        manifests[name] = (m, out)
    if args.dry_run:
        return 0

    try:
        import boto3
    except ImportError:
        print("pip install boto3", file=sys.stderr)
        return 1
    missing = [k for k in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY") if not os.environ.get(k)]
    if missing:
        print(f"missing env: {', '.join(missing)}", file=sys.stderr)
        return 1
    bucket = os.environ.get("R2_BUCKET", "lunar-masks")
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )

    def remote_sha(key: str) -> str | None:
        try:
            return s3.head_object(Bucket=bucket, Key=key)["Metadata"].get("sha256")
        except s3.exceptions.ClientError:
            return None

    for name, (manifest, manifest_path) in manifests.items():
        root = GROUPS[name][0]
        # Files first, manifest last: clients never see a manifest naming missing files.
        for rel, meta in manifest["files"].items():
            key = f"{name}/{rel}"
            if remote_sha(key) == meta["sha256"]:
                print(f"  skip   {key}")
                continue
            ctype = CONTENT_TYPES.get(Path(rel).suffix) or mimetypes.guess_type(rel)[0] or "application/octet-stream"
            s3.upload_file(
                str(root / rel), bucket, key,
                ExtraArgs={
                    "ContentType": ctype,
                    "Metadata": {"sha256": meta["sha256"]},
                    "CacheControl": "public, max-age=31536000, immutable",
                },
            )
            print(f"  upload {key}")
        s3.upload_file(
            str(manifest_path), bucket, f"{name}/manifest.json",
            ExtraArgs={"ContentType": "application/json", "CacheControl": "public, max-age=300"},
        )
        print(f"published {name}/ to bucket {bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
