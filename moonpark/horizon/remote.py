"""Static data store (Cloudflare R2 behind a CDN): masks, kernels and hazard rasters.

The remote is only files per group (``cap_1km/``, ``data/``). Each published version lives
under its own path ``<group>/<version>/`` with its own ``manifest.json``; the mutable pointer
``<group>/latest.json`` = ``{"version", "min_app_version"}`` names the live one. Nothing is
computed server side. Files are downloaded on demand into ``<cache>/<group>/<version>/``,
verified against the manifest sha256, and reused afterwards (offline OK: newest cached version).
A store without ``latest.json`` (404) is read with the legacy flat layout.
# per D-20261115-pj-8c03 (remote serves data only; the evaluator runs on the client)
# per D-20261118-pj-62d3 (version in the path, one live version, client checks the version id)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import threading
import urllib.error
import time
import urllib.request
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

DEFAULT_ORIGIN = "https://masks.pedrojon.com"
USER_AGENT = "moonpark-client"
TIMEOUT_S = 60  # per tile download
MANIFEST_TIMEOUT_S = 8  # a missing remote must not stall the API
RETRY_AFTER_S = 30  # after a failed probe, do not hit the network again for this long
STATUS_TIMEOUT_S = 2  # /store-status probe (pointer + manifest): the first app screen must not wait ~16 s
KEEP_VERSIONS = 2  # cached version dirs kept: current + previous (offline right after an update still works)
VERSION_RE = re.compile(r"[0-9a-f]{12}")  # the publisher's content digest (scripts/publish_masks.py)


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
    return Path(base) / "moonpark"


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


def _fetch_json(url: str, timeout: float = MANIFEST_TIMEOUT_S) -> dict:
    with _get(url, timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_manifest(base: str, timeout: float = MANIFEST_TIMEOUT_S) -> dict:
    return _fetch_json(f"{base}/manifest.json", timeout)


def store_status(timeout: float = STATUS_TIMEOUT_S) -> dict:
    """Live data version and the minimum app version it needs, for the force-update check.

    The pointer + manifest probe uses a short ``timeout``; a failed short probe reports the cached version as
    unreachable without pinning the group offline (the data paths retry with their own timeout)."""
    g = group("data")
    if g is None:  # remote off
        return {"version": None, "min_app_version": None, "reachable": False}
    try:
        g.load(timeout=timeout)
    except OSError:  # unreachable with nothing cached
        return {"version": None, "min_app_version": None, "reachable": False}
    return {"version": g.version, "min_app_version": g.min_app_version, "reachable": g.reachable}


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
    # A unique temp per call: concurrent downloads of the same rel never share (or delete)
    # each other's in-flight file; whichever finishes last atomically replaces identical bytes.
    # uuid + "xb" (not mkstemp) so the published file keeps umask permissions instead of 0600.
    part = dest.with_name(f"{dest.name}.{uuid.uuid4().hex}.part")
    _progress_start(rel, entry["size"])
    try:
        with part.open("xb") as out, _get(f"{base}/{rel}") as r:
            while chunk := r.read(1 << 16):  # 64 KiB: a 1 MiB read stalls progress for seconds on a slow link
                out.write(chunk)
                _progress_add(len(chunk))
        if _sha256(part) != entry["sha256"]:
            raise OSError(f"checksum mismatch for {rel}")
        os.replace(part, dest)
        _progress_finish()
    finally:
        part.unlink(missing_ok=True)
    return dest


class RemoteCap:
    """Lazy, cached view of one remote group. Falls back to the cache if offline.

    ``root`` is the group's cache dir; versioned files go to ``root/<version>/<rel>``.
    """

    def __init__(self, base: str, root: Path | None = None) -> None:
        self.base = base
        self.root = root or cache_root()
        self._manifest: dict | None = None
        self._failed_at: float | None = None
        self.version: str | None = None  # None: legacy flat layout
        self.min_app_version: str | None = None
        self.reachable = False

    @property
    def _dir(self) -> Path:
        return self.root / self.version if self.version else self.root

    @property
    def _base(self) -> str:
        return f"{self.base}/{self.version}" if self.version else self.base

    def _cached_versions(self) -> list[Path]:
        """Version dirs in the cache: ``root/<v>/manifest.json`` whose ``version`` is ``<v>``."""
        out = []
        for m in self.root.glob("*/manifest.json"):
            if not VERSION_RE.fullmatch(m.parent.name):
                continue
            try:
                if json.loads(m.read_text(encoding="utf-8")).get("version") == m.parent.name:
                    out.append(m)
            except (OSError, ValueError):
                continue
        return sorted(out, key=lambda m: m.stat().st_mtime)

    def _load_offline(self) -> dict:
        versions = self._cached_versions()
        if versions:  # newest cached version
            self.version = versions[-1].parent.name
            try:
                ptr = json.loads((self.root / "latest.json").read_text(encoding="utf-8"))
                if ptr.get("version") == self.version:
                    self.min_app_version = ptr.get("min_app_version") or None
            except (OSError, ValueError):
                pass
            return json.loads(versions[-1].read_text(encoding="utf-8"))
        return json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))  # legacy

    def _load_online(self, timeout: float = MANIFEST_TIMEOUT_S) -> dict:
        try:
            ptr = _fetch_json(f"{self.base}/latest.json", timeout)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            m = fetch_manifest(self.base, timeout)  # legacy flat layout
            self.root.mkdir(parents=True, exist_ok=True)
            (self.root / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
            return m
        version = ptr["version"]
        # Only the publisher's 12-hex digest: anything else (path separators, drive letters, UNC, ..) is an
        # invalid pointer, handled like an unreachable store (newest cached version, else legacy cache).
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            raise OSError(f"bad store version {version!r}")
        m = fetch_manifest(f"{self.base}/{version}", timeout)
        if m.get("version", version) != version:
            raise OSError(f"manifest version {m.get('version')!r} != latest.json {version!r}")
        m["version"] = version
        vdir = self.root / version
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
        (self.root / "latest.json").write_text(json.dumps(ptr), encoding="utf-8")
        # One live version, but keep the previous one too (KEEP_VERSIONS): a user who goes offline right
        # after an update still has a complete cache. Older version dirs are dropped; legacy flat files stay.
        older = [m for m in self._cached_versions() if m.parent.name != version]  # oldest first
        for old in older[: max(len(older) - (KEEP_VERSIONS - 1), 0)]:
            shutil.rmtree(old.parent, ignore_errors=True)
        self.version, self.min_app_version = version, ptr.get("min_app_version") or None
        return m

    @property
    def manifest(self) -> dict:
        return self.load()

    def load(self, timeout: float | None = None) -> dict:
        """The manifest (memoized). ``timeout`` None = the normal MANIFEST_TIMEOUT_S path. A custom (short)
        timeout is a probe: on failure it reports the cached version but memoizes nothing and sets no backoff,
        so the next normal access retries the network."""
        if self._manifest is None:
            if self._failed_at is not None and time.monotonic() - self._failed_at < RETRY_AFTER_S:
                raise OSError("mask store unreachable (retrying shortly)")
            probe = timeout is not None
            try:
                self._manifest = self._load_online(MANIFEST_TIMEOUT_S if timeout is None else timeout)
                self.reachable = True
            except (urllib.error.URLError, OSError, ValueError, KeyError):
                self.version = self.min_app_version = None
                self.reachable = False
                try:
                    offline = self._load_offline()
                except (OSError, ValueError):
                    if not probe:
                        self._failed_at = time.monotonic()
                    raise OSError("data store unreachable and nothing cached") from None
                if probe:
                    return offline
                self._manifest = offline
        return self._manifest

    def get(self, rel: str) -> Path:
        m = self.manifest
        return ensure_file(rel, self._dir, self._base, m)

    def available(self) -> bool:
        try:
            self.get("index.parquet")
            return True
        except (urllib.error.URLError, OSError, KeyError, FileNotFoundError):
            return False
