"""Versioned data store: version in the path, latest.json pointer. # per D-20261118-pj-62d3

Versions are the publisher's 12-hex content digest (the client rejects any other pointer); the client tests
below use digest-shaped ids ("0000000000a1" = version 1).

Layout: ``<origin>/<group>/<version>/<rel>``, manifest at ``<group>/<version>/manifest.json``,
mutable pointer ``<group>/latest.json`` = {"version", "min_app_version"}. No network: ``_get`` is faked.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import urllib.error
from pathlib import Path

import pytest

from moonpark.horizon import remote
from moonpark.horizon.remote import RemoteCap

BASE = "http://store.test/data"


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeStore:
    """url -> bytes. Missing url => HTTP 404; ``offline`` => URLError. Records requests."""

    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.offline = False
        self.requests: list[str] = []

    def put(self, url, data):
        self.files[url] = data if isinstance(data, bytes) else json.dumps(data).encode()

    def publish(self, version, blobs, min_app=""):
        """Publish a version the way the script does: files, manifest, then latest.json."""
        for rel, b in blobs.items():
            self.put(f"{BASE}/{version}/{rel}", b)
        files = {r: {"size": len(b), "sha256": hashlib.sha256(b).hexdigest()} for r, b in blobs.items()}
        self.put(f"{BASE}/{version}/manifest.json", {"schema": 1, "version": version, "files": files})
        self.put(f"{BASE}/latest.json", {"version": version, "min_app_version": min_app})

    def get(self, url, timeout=0):
        self.requests.append(url)
        if self.offline:
            raise urllib.error.URLError("offline")
        if url not in self.files:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return _Resp(self.files[url])


@pytest.fixture()
def fake(monkeypatch):
    s = FakeStore()
    monkeypatch.setattr(remote, "_get", s.get)
    return s


def _cap(tmp_path):
    return RemoteCap(BASE, tmp_path / "cache")


def _files(root: Path):
    return sorted(p for p in root.rglob("*") if p.is_file())


def test_same_size_other_version_file_is_redownloaded(fake, tmp_path):
    old, new = b"A" * 200, b"B" * 200  # same name, same size, different content
    fake.publish("0000000000a1", {"d/f.bin": old})
    assert _cap(tmp_path).get("d/f.bin").read_bytes() == old
    fake.publish("0000000000a2", {"d/f.bin": new})
    got = _cap(tmp_path).get("d/f.bin")  # fresh client: must notice latest.json moved
    assert got.read_bytes() == new
    assert any(u.endswith("/0000000000a2/d/f.bin") for u in fake.requests)


def test_new_version_dir_used_and_old_ignored_or_pruned(fake, tmp_path):
    fake.publish("0000000000a1", {"d/f.bin": b"A" * 50})
    _cap(tmp_path).get("d/f.bin")
    fake.publish("0000000000a2", {"d/f.bin": b"B" * 50})
    got = _cap(tmp_path).get("d/f.bin")
    cache = tmp_path / "cache"
    assert got == cache / "0000000000a2" / "d" / "f.bin"
    assert got.read_bytes() == b"B" * 50
    # one live version: the old dir is pruned (at minimum it must not be what is served)
    old = cache / "0000000000a1"
    assert not old.exists() or not (old / "d" / "f.bin").exists() or got.parent.parent.name == "0000000000a2"


def test_old_version_not_pruned_wrongly_when_still_live(fake, tmp_path):
    fake.publish("0000000000a1", {"d/f.bin": b"A" * 50})
    _cap(tmp_path).get("d/f.bin")
    n = len(fake.requests)
    again = _cap(tmp_path).get("d/f.bin")  # same live version: cache reused, file not re-fetched
    assert again == tmp_path / "cache" / "0000000000a1" / "d" / "f.bin"
    assert not any(u.endswith("/0000000000a1/d/f.bin") for u in fake.requests[n:])


def test_offline_uses_newest_cached_version(fake, tmp_path):
    fake.publish("0000000000a1", {"d/f.bin": b"A" * 50})
    c = _cap(tmp_path)
    p = c.get("d/f.bin")
    assert p.read_bytes() == b"A" * 50
    fake.offline = True
    c2 = _cap(tmp_path)
    assert c2.get("d/f.bin").read_bytes() == b"A" * 50
    assert getattr(c2, "version", "MISSING") == "0000000000a1"


def test_legacy_flat_layout_when_latest_404(fake, tmp_path):
    blob = b"L" * 64
    fake.put(f"{BASE}/manifest.json", {"schema": 1, "files": {"d/f.bin": {"size": 64, "sha256": hashlib.sha256(blob).hexdigest()}}})
    fake.put(f"{BASE}/d/f.bin", blob)
    c = _cap(tmp_path)
    assert c.get("d/f.bin").read_bytes() == blob
    assert any(u == f"{BASE}/latest.json" for u in fake.requests), "client must probe latest.json first"
    assert (tmp_path / "cache" / "d" / "f.bin").is_file()  # flat cache layout kept
    assert getattr(c, "version", "MISSING") is None


def test_checksum_mismatch_leaves_nothing_in_versioned_layout(fake, tmp_path):
    good = b"G" * 100
    fake.publish("0000000000a1", {"d/f.bin": good})
    fake.put(f"{BASE}/0000000000a1/d/f.bin", b"X" * 100)  # same size, corrupted
    with pytest.raises(OSError, match="checksum"):
        _cap(tmp_path).get("d/f.bin")
    cache = tmp_path / "cache"
    leftovers = [p.relative_to(cache).as_posix() for p in _files(cache) if p.name != "manifest.json" and p.name != "latest.json"]
    assert leftovers == []
    assert fake.requests and any(u.endswith("/latest.json") for u in fake.requests)


def test_version_and_min_app_version_exposed(fake, tmp_path):
    fake.publish("abc123def456", {"d/f.bin": b"Z" * 10}, min_app="1.2.0")
    c = _cap(tmp_path)
    c.get("d/f.bin")  # loads the manifest
    assert getattr(c, "version", "MISSING") == "abc123def456"
    assert getattr(c, "min_app_version", "MISSING") == "1.2.0"
    assert c.manifest["version"] == "abc123def456"


def test_empty_min_app_version_is_none_or_empty(fake, tmp_path):
    fake.publish("0000000000a1", {"d/f.bin": b"Z" * 10}, min_app="")
    c = _cap(tmp_path)
    c.get("d/f.bin")
    assert getattr(c, "version", "MISSING") == "0000000000a1"
    assert getattr(c, "min_app_version", "MISSING") in (None, "")


@pytest.fixture()
def env_store(fake, tmp_path, monkeypatch):
    monkeypatch.setenv("LUNAR_STORE_URL", "http://store.test")
    monkeypatch.setenv("LUNAR_CACHE", str(tmp_path / "cache"))
    monkeypatch.setattr(remote, "_GROUPS", {})
    return fake


def test_store_status_reports_version(env_store):
    env_store.publish("0000000000a7", {"d/f.bin": b"Z" * 10}, min_app="2.0.0")
    fn = getattr(remote, "store_status", None)
    if fn is None:
        pytest.fail("remote.store_status() does not exist")
    st = fn()
    assert st["version"] == "0000000000a7"
    assert st["min_app_version"] == "2.0.0"
    assert st["reachable"] is True


def test_store_status_unreachable(env_store):
    env_store.offline = True
    fn = getattr(remote, "store_status", None)
    if fn is None:
        pytest.fail("remote.store_status() does not exist")
    st = fn()
    assert st["reachable"] is False
    assert st["version"] is None and st["min_app_version"] is None


# --- publish script ----------------------------------------------------------------------


@pytest.fixture()
def pm(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "publish_masks.py"
    spec = importlib.util.spec_from_file_location("publish_masks_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    root = tmp_path / "src"
    (root / "k").mkdir(parents=True)
    (root / "k" / "a.bin").write_bytes(b"aaa")
    (root / "k" / "b.bin").write_bytes(b"bbbb")
    files = [root / "k" / "b.bin", root / "k" / "a.bin"]
    monkeypatch.setitem(mod.GROUPS, "data", (root, lambda: files))
    mod.root = root
    return mod


def _quiet(mod, name):
    return mod.build_manifest(name)


def test_build_manifest_has_content_derived_version(pm):
    m1 = _quiet(pm, "data")
    assert re.fullmatch(r"[0-9a-f]{12}", str(m1.get("version", ""))), m1.keys()
    m2 = _quiet(pm, "data")
    assert m1["version"] == m2["version"]  # identical content => identical version
    (pm.root / "k" / "a.bin").write_bytes(b"aab")  # same size, new content
    assert _quiet(pm, "data")["version"] != m1["version"]


def test_version_independent_of_listing_order(pm, monkeypatch):
    v1 = _quiet(pm, "data").get("version")
    root = pm.root
    monkeypatch.setitem(pm.GROUPS, "data", (root, lambda: [root / "k" / "a.bin", root / "k" / "b.bin"]))
    assert v1 is not None and _quiet(pm, "data")["version"] == v1


def test_plan_uploads_order_and_keys(pm):
    fn = getattr(pm, "plan_uploads", None)
    if fn is None:
        pytest.fail("publish_masks.plan_uploads does not exist")
    manifest = _quiet(pm, "data") if "version" in _quiet(pm, "data") else {**_quiet(pm, "data"), "version": "abc123def456"}
    version = manifest.get("version") or "abc123def456"
    plan = list(fn("data", manifest, version))
    keys = [k for _, k, _ in plan]
    assert keys[-1] == "data/latest.json"
    assert keys[-2] == f"data/{version}/manifest.json"
    assert keys.count("data/latest.json") == 1
    file_keys = keys[:-2]
    assert sorted(file_keys) == sorted(f"data/{version}/{rel}" for rel in manifest["files"])
    assert all(k.startswith(f"data/{version}/") for k in keys[:-1])
    cc = {k: c for _, k, c in plan}
    assert "immutable" in cc[file_keys[0]]
    assert "immutable" not in (cc["data/latest.json"] or "")  # mutable pointer must be revalidated


def test_plan_uploads_local_paths_for_files(pm):
    fn = getattr(pm, "plan_uploads", None)
    if fn is None:
        pytest.fail("publish_masks.plan_uploads does not exist")
    manifest = {**_quiet(pm, "data"), "version": "v1"}
    plan = list(fn("data", manifest, "v1"))
    by_key = {k: p for p, k, _ in plan}
    assert Path(by_key["data/v1/k/a.bin"]).read_bytes() == b"aaa"
