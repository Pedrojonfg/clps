#!/usr/bin/env python3
"""Publish the static data store to the Cloudflare R2 bucket.

Two groups, each with its own checksummed manifest.json. Each publish goes under a
content-derived version path, and the mutable pointer ``<group>/latest.json`` is written last:

  <group>/<version>/<rel>            immutable files
  <group>/<version>/manifest.json    {"schema", "version", "files": {rel: {size, sha256}}}
  <group>/latest.json                {"version", "min_app_version"}  (short cache, revalidated)

  cap_1km  data/masks/cap_1km/            index.parquet, summary.json, tiles/*   (~880 MB)
  data     data/                          kernels/*, hazards/pcp/{summer,winter}/*.npz,
                                          dem/LDSM_80S_80MPP_ADJ.TIF, dem/LPSR_80S_20MPP_ADJ.TIF (~2.5 GB),
                                          relief/<stem>/{manifest.json,<ty>_<tx>.npz} when cut locally
                                          (source data/relief_tiles/<stem>/, scripts/cut_dems.py)

Credentials come from the environment, never from git:

    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
    R2_BUCKET (default: lunar-masks)

Usage:
    python scripts/publish_masks.py --dry-run            # build manifests only, no network
    python scripts/publish_masks.py                      # upload both groups (pip install boto3)
    python scripts/publish_masks.py --only data          # or: --only cap_1km
Old version paths are not deleted here (do it by hand after clients migrate).
# per D-20261115-pj-8c03
# per D-20261118-pj-62d3 (version in the path, one live version)
# per D-20261118-pj-6fea (relief tiles published in the data group)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
import tempfile
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
RELIEF_SRC = "relief_tiles"  # local cutter output under DATA ...
RELIEF_KEY = "relief"  # ... published (and asked for by terrain.py) under this key prefix
IMMUTABLE = "public, max-age=31536000, immutable"
POINTER_CACHE = "public, max-age=60, must-revalidate"
MIN_APP_VERSION = os.environ.get("MIN_APP_VERSION", "")  # "" = any app version may use this data
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
    files += relief_files()
    missing = [p for p in files if not p.is_file()]
    if missing:
        raise SystemExit("missing data files: " + ", ".join(str(p.relative_to(DATA)) for p in missing[:5]))
    return files


def relief_files() -> list[Path]:
    """Every locally cut model: its manifest.json plus the tiles it lists (stray files are not published).

    A model folder without manifest.json is a cut that did not finish: skipped, with a warning.
    """
    files: list[Path] = []
    src = DATA / RELIEF_SRC
    for d in sorted(p for p in src.iterdir() if p.is_dir()) if src.is_dir() else ():
        mpath = d / "manifest.json"
        if not mpath.is_file():
            print(f"  skip {d.relative_to(DATA)}: no manifest.json (unfinished cut?)", file=sys.stderr)
            continue
        listed = json.loads(mpath.read_text(encoding="utf-8"))["files"]
        files += [mpath] + [d / rel for rel in sorted(listed)]
    return files


def _key(name: str, root: Path, p: Path) -> str:
    """Manifest key of a local file: its path under ``root``, with relief_tiles/ published as relief/."""
    rel = p.relative_to(root).as_posix()
    if name == "data" and rel.startswith(RELIEF_SRC + "/"):
        rel = RELIEF_KEY + rel[len(RELIEF_SRC):]
    return rel


def _source(name: str, rel: str) -> Path:
    """Local file behind a manifest key (inverse of ``_key``)."""
    root = GROUPS[name][0]
    if name == "data" and rel.startswith(RELIEF_KEY + "/"):
        return root / RELIEF_SRC / rel[len(RELIEF_KEY) + 1:]
    return root / rel


def _check_relief(name: str, files: dict) -> None:
    """Each published tile must match the size and sha256 its model manifest recorded when it was cut."""
    for key in files:
        parts = key.split("/")
        if name != "data" or parts[0] != RELIEF_KEY or parts[-1] != "manifest.json":
            continue
        model = json.loads(_source(name, key).read_text(encoding="utf-8"))
        prefix = key.removesuffix("manifest.json")
        bad = [r for r, meta in model["files"].items()
               if {k: files.get(prefix + r, {}).get(k) for k in ("size", "sha256")} != {k: meta[k] for k in ("size", "sha256")}]
        if bad:
            raise SystemExit(f"{prefix}: {len(bad)} tile(s) differ from their manifest (re-cut?): {', '.join(sorted(bad)[:5])}")


GROUPS = {
    # name: (root the manifest keys are relative to, file lister, extra manifest fields)
    "cap_1km": (CAP, cap_files),
    "data": (DATA, data_files),
}


def build_manifest(name: str) -> dict:
    root, lister = GROUPS[name]
    files = {}
    for p in lister():
        rel = _key(name, root, p)
        files[rel] = {"size": p.stat().st_size, "sha256": sha256(p)}
        print(f"  hashed {name}/{rel}", file=sys.stderr)
    _check_relief(name, files)
    extra: dict = {}
    if name == "cap_1km":
        s = json.loads((CAP / "summary.json").read_text(encoding="utf-8"))
        extra = {k: s.get(k) for k in ("schedule_version", "spacing_m", "observer_height_m", "n_masks")}
    digest = hashlib.sha256("".join(f"{r}\0{files[r]['sha256']}\n" for r in sorted(files)).encode())
    return {"schema": 1, "version": digest.hexdigest()[:12], **extra, "files": files}


def plan_uploads(name: str, manifest: dict, version: str) -> list[tuple[Path, str, str]]:
    """(local path, bucket key, Cache-Control) in upload order: files, version manifest, pointer.

    The version manifest and ``latest.json`` are written to a temp dir by ``write_publish_files``.
    """
    plan = [(_source(name, rel), f"{name}/{version}/{rel}", IMMUTABLE) for rel in manifest["files"]]
    plan.append((_version_manifest_path(name, version), f"{name}/{version}/manifest.json", IMMUTABLE))
    plan.append((_pointer_path(name), f"{name}/latest.json", POINTER_CACHE))
    return plan


def _local_manifest_path(name: str) -> Path:
    return GROUPS[name][0] / ("manifest.json" if name == "cap_1km" else "store-manifest.json")


PUBLISH_TMP = Path(tempfile.gettempdir()) / "moonpark-publish"


def _version_manifest_path(name: str, version: str) -> Path:
    return PUBLISH_TMP / name / version / "manifest.json"


def _pointer_path(name: str) -> Path:
    return PUBLISH_TMP / name / "latest.json"


def write_publish_files(name: str, manifest: dict, version: str) -> None:
    """Local copies of the version manifest and the pointer, for upload."""
    _version_manifest_path(name, version).parent.mkdir(parents=True, exist_ok=True)
    _version_manifest_path(name, version).write_text(json.dumps({**manifest, "version": version}, indent=1), encoding="utf-8")
    _pointer_path(name).write_text(json.dumps({"version": version, "min_app_version": MIN_APP_VERSION}), encoding="utf-8")


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
        out = _local_manifest_path(name)
        out.write_text(json.dumps(m, indent=1), encoding="utf-8")
        total = sum(f["size"] for f in m["files"].values())
        print(f"{name}: version {m['version']}, {len(m['files'])} files, {total / 1e6:.0f} MB -> {out}")
        manifests[name] = m
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

    for name, manifest in manifests.items():
        version = manifest["version"]
        write_publish_files(name, manifest, version)
        # Files first, version manifest next, latest.json last: clients never see a pointer
        # naming a version whose manifest or files are missing.
        for local, key, cache in plan_uploads(name, manifest, version):
            meta = manifest["files"].get(key.removeprefix(f"{name}/{version}/"))
            if meta and remote_sha(key) == meta["sha256"]:
                print(f"  skip   {key}")
                continue
            ctype = "application/json" if meta is None else (
                CONTENT_TYPES.get(local.suffix) or mimetypes.guess_type(local.name)[0] or "application/octet-stream")
            extra = {"ContentType": ctype, "CacheControl": cache}
            if meta:
                extra["Metadata"] = {"sha256": meta["sha256"]}
            s3.upload_file(str(local), bucket, key, ExtraArgs=extra)
            print(f"  upload {key}")
        print(f"published {name}/{version}/ to bucket {bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
