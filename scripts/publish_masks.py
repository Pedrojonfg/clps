#!/usr/bin/env python3
"""Publish data/masks/cap_1km to the Cloudflare R2 bucket as static files.

Builds manifest.json (size + sha256 per file) and uploads only what changed.
Credentials come from the environment, never from git:

    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
    R2_BUCKET (default: lunar-masks)

Usage:
    python scripts/publish_masks.py --dry-run     # build manifest only, no network
    python scripts/publish_masks.py               # upload (needs: pip install boto3)
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
CAP = REPO / "data" / "masks" / "cap_1km"
PREFIX = "cap_1km"
PUBLISH = ("index.parquet", "summary.json")  # plus everything under tiles/
CONTENT_TYPES = {".npy": "application/octet-stream", ".parquet": "application/octet-stream"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect() -> list[Path]:
    files = [CAP / n for n in PUBLISH if (CAP / n).is_file()]
    files += sorted((CAP / "tiles").glob("t*_*.*"))
    return files


def build_manifest() -> dict:
    summary = json.loads((CAP / "summary.json").read_text(encoding="utf-8"))
    files = {}
    for p in collect():
        rel = p.relative_to(CAP).as_posix()
        files[rel] = {"size": p.stat().st_size, "sha256": sha256(p)}
        print(f"  hashed {rel}", file=sys.stderr)
    return {
        "schema": 1,
        "schedule_version": summary.get("schedule_version"),
        "spacing_m": summary.get("spacing_m"),
        "observer_height_m": summary.get("observer_height_m"),
        "n_masks": summary.get("n_masks"),
        "files": files,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="write manifest locally, upload nothing")
    args = ap.parse_args()

    if not (CAP / "index.parquet").is_file():
        print(f"no cap at {CAP}", file=sys.stderr)
        return 1

    manifest = build_manifest()
    out = CAP / "manifest.json"
    out.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    total = sum(f["size"] for f in manifest["files"].values())
    print(f"manifest: {len(manifest['files'])} files, {total / 1e6:.0f} MB -> {out}")
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

    # Tiles and index first, manifest last: clients never see a manifest naming missing files.
    for rel, meta in manifest["files"].items():
        key = f"{PREFIX}/{rel}"
        if remote_sha(key) == meta["sha256"]:
            print(f"  skip   {key}")
            continue
        ctype = CONTENT_TYPES.get(Path(rel).suffix) or mimetypes.guess_type(rel)[0] or "application/octet-stream"
        s3.upload_file(
            str(CAP / rel), bucket, key,
            ExtraArgs={"ContentType": ctype, "Metadata": {"sha256": meta["sha256"]}, "CacheControl": "public, max-age=31536000, immutable"},
        )
        print(f"  upload {key}")
    s3.upload_file(
        str(out), bucket, f"{PREFIX}/manifest.json",
        ExtraArgs={"ContentType": "application/json", "CacheControl": "public, max-age=300"},
    )
    print(f"published to bucket {bucket}/{PREFIX}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
