"""Static data store (Cloudflare R2 behind a CDN): masks, kernels and hazard rasters.

The remote is only files plus a ``manifest.json`` per group (``cap_1km/``, ``data/``).
Nothing is computed server side. Files are downloaded on demand into a local
cache, verified against the manifest sha256, and reused afterwards (offline OK).
# per D-20261115-pj-8c03 (remote serves data only; the evaluator runs on the client)
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import urllib.error
import time
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

DEFAULT_ORIGIN = "https://masks.pedrojon.com"
USER_AGENT = "lunar-eval-client"
TIMEOUT_S = 60  # per tile download
MANIFEST_TIMEOUT_S = 8  # a missing remote must not stall the API
RETRY_AFTER_S = 30  # after a failed probe, do not hit the network again for this long


def store_origin() -> str | None:
    """Origin of the data store; ``LUNAR_STORE_URL=off`` disables remote fetch."""
    url = os.environ.get("LUNAR_STORE_URL", DEFAULT_ORIGIN).strip()
    if not url or url.lower() == "off":
        return None
    return url.rstrip("/")


def cache_root() -> Path:
    env = os.environ.get("LUNAR_CACHE")
    if env:
        return Path(env)
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "lunar-eval"


_GROUPS: dict[tuple[str, str], "RemoteCap"] = {}


def group(name: str) -> "RemoteCap | None":
    """Remote group (``cap_1km`` or ``data``), or None when remote fetch is off."""
    origin = store_origin()
    if origin is None:
        return None
    key = (origin, name)
    if key not in _GROUPS:
        _GROUPS[key] = RemoteCap(f"{origin}/{name}", cache_root() / name)
    return _GROUPS[key]


def locate(rel: str) -> Path | None:
    """Path of ``data/<rel>``: the local file if present, else fetched from the store.

    ``rel`` is relative to ``data/`` (``kernels/de440s.bsp``, ``hazards/pcp/summer/ltim03.npz``,
    ``dem/LDSM_80S_80MPP_ADJ.TIF``). Returns None when neither local nor remote has it.
    """
    local = DATA_DIR / rel
    if local.is_file():
        return local
    g = group("data")
    if g is None:
        return None
    try:
        return g.get(rel)
    except (OSError, KeyError, FileNotFoundError):
        return None


def remote_has_prefix(prefix: str) -> bool:
    """True if the remote ``data`` group lists any file under ``prefix`` (cheap: manifest only)."""
    g = group("data")
    if g is None:
        return False
    try:
        return any(k.startswith(prefix) for k in g.manifest["files"])
    except OSError:
        return False


def _get(url: str, timeout: float = TIMEOUT_S) -> urllib.request.addinfourl:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 (https store)


def fetch_manifest(base: str) -> dict:
    with _get(f"{base}/manifest.json", MANIFEST_TIMEOUT_S) as r:
        return json.loads(r.read().decode("utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_progress_lock = threading.Lock()
_IDLE_AFTER_S = 3.0  # no download activity for this long => idle (files arrive one after another)
_progress: dict = {"file": None, "done": 0, "total": 0, "files_done": 0, "bytes_done": 0, "updated": 0.0}


def download_progress() -> dict:
    """Snapshot of the download in flight, for the UI. ``active`` is False when idle."""
    with _progress_lock:
        p = dict(_progress)
    p["active"] = time.monotonic() - p.pop("updated") < _IDLE_AFTER_S
    return p


def _progress_start(rel: str, total: int) -> None:
    with _progress_lock:
        if time.monotonic() - _progress["updated"] >= _IDLE_AFTER_S:
            _progress.update(files_done=0, bytes_done=0)
        _progress.update(file=rel, done=0, total=int(total), updated=time.monotonic())


def _progress_add(n: int) -> None:
    with _progress_lock:
        _progress["done"] += n
        _progress["bytes_done"] += n
        _progress["updated"] = time.monotonic()


def _progress_finish() -> None:
    with _progress_lock:
        _progress["files_done"] += 1
        _progress["updated"] = time.monotonic()


def ensure_file(rel: str, dest_root: Path, base: str, manifest: dict) -> Path:
    """Return ``dest_root/rel``, downloading and verifying it if missing or stale."""
    entry = manifest["files"].get(rel)
    if entry is None:
        raise FileNotFoundError(f"{rel} is not in the remote manifest")
    dest = dest_root / rel
    if dest.is_file() and dest.stat().st_size == entry["size"]:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    _progress_start(rel, entry["size"])
    try:
        with _get(f"{base}/{rel}") as r, part.open("wb") as out:
            while chunk := r.read(1 << 20):
                out.write(chunk)
                _progress_add(len(chunk))
        if _sha256(part) != entry["sha256"]:
            raise OSError(f"checksum mismatch for {rel}")
        part.replace(dest)
        _progress_finish()
    finally:
        part.unlink(missing_ok=True)
    return dest


class RemoteCap:
    """Lazy, cached view of the remote cap. Falls back to the cache if offline."""

    def __init__(self, base: str, root: Path | None = None) -> None:
        self.base = base
        self.root = root or cache_root()
        self._manifest: dict | None = None
        self._failed_at: float | None = None

    @property
    def manifest(self) -> dict:
        if self._manifest is None:
            cached = self.root / "manifest.json"
            if self._failed_at is not None and time.monotonic() - self._failed_at < RETRY_AFTER_S:
                raise OSError("mask store unreachable (retrying shortly)")
            try:
                self._manifest = fetch_manifest(self.base)
                self.root.mkdir(parents=True, exist_ok=True)
                cached.write_text(json.dumps(self._manifest), encoding="utf-8")
            except (urllib.error.URLError, OSError):
                if not cached.is_file():
                    self._failed_at = time.monotonic()
                    raise
                self._manifest = json.loads(cached.read_text(encoding="utf-8"))
        return self._manifest

    def get(self, rel: str) -> Path:
        return ensure_file(rel, self.root, self.base, self.manifest)

    def available(self) -> bool:
        try:
            self.get("index.parquet")
            return True
        except (urllib.error.URLError, OSError, KeyError, FileNotFoundError):
            return False
