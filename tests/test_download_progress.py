"""Download progress reported while the data store streams a file. # per D-20261115-pj-8c03"""

from __future__ import annotations

import hashlib
import http.server
import threading
from pathlib import Path

from fastapi.testclient import TestClient

from moonpark.api.app import app
from moonpark.horizon import remote


def _serve(tmp: Path, payload: bytes):
    (tmp / "f.bin").write_bytes(payload)

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(tmp), **k)

        def log_message(self, *a):  # quiet
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_ensure_file_reports_progress(tmp_path: Path) -> None:
    payload = b"x" * (3 << 20)
    srv = _serve(tmp_path, payload)
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        manifest = {"files": {"f.bin": {"size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}}}
        remote._progress.update(file=None, done=0, total=0, files_done=0, bytes_done=0, updated=0.0)
        assert remote.download_progress()["active"] is False
        dest = remote.ensure_file("f.bin", tmp_path / "cache", base, manifest)
        p = remote.download_progress()
        assert dest.read_bytes() == payload
        assert p["active"] is True and p["file"] == "f.bin"
        assert p["done"] == p["total"] == len(payload)
        assert p["files_done"] == 1 and p["bytes_done"] == len(payload)
    finally:
        srv.shutdown()


def test_progress_endpoint_shape() -> None:
    r = TestClient(app).get("/progress")
    assert r.status_code == 200
    assert {"active", "file", "done", "total", "files_done", "bytes_done"} <= set(r.json())
