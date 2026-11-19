"""Remote mask store client: manifest, checksum, cache reuse. # per D-8c03"""

from __future__ import annotations

import hashlib
import json
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from moonpark.horizon.remote import RemoteCap


@pytest.fixture()
def store(tmp_path):
    root = tmp_path / "srv"
    root.mkdir()
    blob = b"abc" * 100
    (root / "index.parquet").write_bytes(blob)
    manifest = {"files": {"index.parquet": {"size": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}}}
    (root / "manifest.json").write_text(json.dumps(manifest))
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    handler.log_message = lambda *a, **k: None
    srv = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", root
    srv.shutdown()


def test_download_verify_and_reuse(store, tmp_path):
    base, root = store
    cap = RemoteCap(base, tmp_path / "cache")
    path = cap.get("index.parquet")
    assert path.read_bytes() == (root / "index.parquet").read_bytes()
    (root / "index.parquet").unlink()  # second read must come from cache
    assert RemoteCap(base, tmp_path / "cache").get("index.parquet") == path


def test_checksum_mismatch_rejected(store, tmp_path):
    base, root = store
    (root / "index.parquet").write_bytes(b"x" * 300)  # same size, wrong content
    with pytest.raises(OSError, match="checksum"):
        RemoteCap(base, tmp_path / "cache").get("index.parquet")
    assert not (tmp_path / "cache" / "index.parquet").exists()


def test_unknown_file(store, tmp_path):
    base, _ = store
    with pytest.raises(FileNotFoundError):
        RemoteCap(base, tmp_path / "cache").get("tiles/nope.npy")


def test_unreachable_store_fails_fast_and_is_not_retried_immediately(tmp_path, monkeypatch):
    import time

    from moonpark.horizon import remote

    calls = []

    def boom(url, timeout=0):
        calls.append(url)
        raise OSError("down")

    monkeypatch.setattr(remote, "_get", boom)
    cap = RemoteCap("http://127.0.0.1:1", tmp_path / "cache")
    assert cap.available() is False
    t = time.monotonic()
    assert cap.available() is False
    assert len(calls) == 1 and time.monotonic() - t < 0.5


# --- ensure_file: concurrency and failure hygiene -------------------------------------------

PAYLOAD = bytes(range(256)) * 64  # 16 KiB, non-repeating enough that interleaving shows up


class _FakeStream:
    """Context-manager response yielding PAYLOAD in two halves; ``on_mid`` runs between them."""

    def __init__(self, on_start=None, on_mid=None, fail_mid=False):
        self._parts = [PAYLOAD[: len(PAYLOAD) // 2], PAYLOAD[len(PAYLOAD) // 2 :]]
        self._on_start, self._on_mid, self._fail_mid = on_start, on_mid, fail_mid
        self._i = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, n=-1):
        if self._i == 1:
            if self._on_mid:
                self._on_mid()
            if self._fail_mid:
                raise OSError("connection reset")
        if self._i == 0 and self._on_start:
            self._on_start()
        if self._i >= len(self._parts):
            return b""
        chunk = self._parts[self._i]
        self._i += 1
        return chunk


def _manifest(payload=PAYLOAD):
    return {"files": {"d/f.bin": {"size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}}}


def _leftovers(root):
    return sorted(p.name for p in root.rglob("*") if p.is_file() and p.name != "f.bin")


def test_concurrent_ensure_file_same_rel_both_get_valid_file(tmp_path, monkeypatch):
    from moonpark.horizon import remote

    lock = threading.Lock()
    calls = []
    both_started = threading.Event()
    release = [threading.Event(), threading.Event()]

    def fake_get(url, timeout=0):
        with lock:
            idx = len(calls)
            calls.append(url)
            if len(calls) == 2:
                both_started.set()
        # Pause mid-stream so the two downloads overlap (if the implementation allows overlap).
        return _FakeStream(on_mid=lambda: release[idx].wait(5))

    monkeypatch.setattr(remote, "_get", fake_get)
    root = tmp_path / "cache"
    results, errors = [], []

    def worker():
        try:
            results.append(remote.ensure_file("d/f.bin", root, "http://x", _manifest()))
        except BaseException as e:  # noqa: BLE001 - surfaced by the assertion below
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    both_started.wait(1.0)  # overlap if allowed; a serializing lock simply never sets this
    release[0].set()  # first download finishes (and publishes dest) while the second is mid-stream
    dest = root / "d" / "f.bin"
    for _ in range(200):
        if dest.exists():
            break
        threading.Event().wait(0.01)
    release[1].set()
    for t in threads:
        t.join(10)
    assert not any(t.is_alive() for t in threads)

    assert errors == []
    assert len(results) == 2 and results[0] == results[1] == dest
    assert dest.read_bytes() == PAYLOAD
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == _manifest()["files"]["d/f.bin"]["sha256"]
    assert _leftovers(root) == []


def test_failed_checksum_leaves_nothing_and_retry_succeeds(tmp_path, monkeypatch):
    from moonpark.horizon import remote

    bad = bytes(len(PAYLOAD))  # right size, wrong content
    streams = [_FakeStream(), _FakeStream()]
    streams[0]._parts = [bad[: len(bad) // 2], bad[len(bad) // 2 :]]
    it = iter(streams)
    monkeypatch.setattr(remote, "_get", lambda url, timeout=0: next(it))
    root = tmp_path / "cache"

    with pytest.raises(OSError, match="checksum"):
        remote.ensure_file("d/f.bin", root, "http://x", _manifest())
    assert not (root / "d" / "f.bin").exists()
    assert _leftovers(root) == []

    dest = remote.ensure_file("d/f.bin", root, "http://x", _manifest())  # retry gets good bytes
    assert dest.read_bytes() == PAYLOAD
    assert _leftovers(root) == []


def test_stream_error_midway_leaves_nothing_and_retry_succeeds(tmp_path, monkeypatch):
    from moonpark.horizon import remote

    streams = iter([_FakeStream(fail_mid=True), _FakeStream()])
    monkeypatch.setattr(remote, "_get", lambda url, timeout=0: next(streams))
    root = tmp_path / "cache"

    with pytest.raises(OSError, match="connection reset"):
        remote.ensure_file("d/f.bin", root, "http://x", _manifest())
    assert not (root / "d" / "f.bin").exists()
    assert _leftovers(root) == []

    dest = remote.ensure_file("d/f.bin", root, "http://x", _manifest())
    assert dest.read_bytes() == PAYLOAD
    assert _leftovers(root) == []


def test_successful_download_is_complete_with_no_part_files(tmp_path, monkeypatch):
    from moonpark.horizon import remote

    monkeypatch.setattr(remote, "_get", lambda url, timeout=0: _FakeStream())
    root = tmp_path / "cache"
    dest = remote.ensure_file("d/f.bin", root, "http://x", _manifest())
    assert dest == root / "d" / "f.bin"
    assert dest.read_bytes() == PAYLOAD
    assert [p.name for p in dest.parent.iterdir()] == ["f.bin"]
