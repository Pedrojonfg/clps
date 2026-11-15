"""S12 harness smoke (D-1a9e): scripts exist and dry-run without inventing pass numbers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validation_md_exists() -> None:
    text = (ROOT / "docs" / "validation.md").read_text(encoding="utf-8")
    assert "D-39f3" in text
    assert "D-9ab3" in text
    assert "planned" in text.lower()


def test_short_night_script_dry_run(tmp_path: Path) -> None:
    out = tmp_path / "short.json"
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "s12_short_night_recheck.py"), "--json-out", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["decision"] == "D-20261115-pj-39f3"
    assert data["tolerance_h"] == 5
    assert data["status"] in {"SKIP_NO_DEM", "HARNESS_READY_AWAITING_OVERNIGHT"}


def test_pgda69_script_dry_run(tmp_path: Path) -> None:
    out = tmp_path / "pgda.json"
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "s12_pgda69_compare.py"), "--json-out", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["decision"] == "D-20261115-pj-9ab3"
    assert data["deltas"] == []
    assert data["pass_fail"] == "none_v1_report_only"
