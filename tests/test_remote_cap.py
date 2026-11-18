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
