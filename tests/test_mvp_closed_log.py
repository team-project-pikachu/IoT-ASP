"""Offline tests for MVP closed-log helper (#65 / #68)."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mvp_closed_log_append.sh"
LOG = ROOT / "docs" / "mvp-closed-log.md"
ROADMAP = ROOT / "docs" / "mvp-roadmap.md"
WORKFLOW = ROOT / ".github" / "workflows" / "mvp-closed-log.yml"


def test_mvp_artifacts_present():
    assert SCRIPT.is_file()
    assert LOG.is_file()
    assert ROADMAP.is_file()
    assert WORKFLOW.is_file()
    text = LOG.read_text(encoding="utf-8")
    assert "YYYY-MM-DD | #N |" in text or "| #9 |" in text
    assert "mvp-roadmap.md" in ROADMAP.read_text(encoding="utf-8") or "Milestone" in ROADMAP.read_text(
        encoding="utf-8"
    )


def test_mvp_closed_log_append_idempotent(tmp_path, monkeypatch):
    log = tmp_path / "mvp-closed-log.md"
    log.write_text(
        "# MVP closed-issue log\n\n## Log\n\n2026-01-01 | #999 | fixture | closed\n",
        encoding="utf-8",
    )
    # Point script at temp log by copying script with LOG override via env is not supported;
    # instead run against a temp copy of the repo layout.
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "docs" / "mvp-closed-log.md").write_text(log.read_text(encoding="utf-8"), encoding="utf-8")
    script = root / "scripts" / "mvp_closed_log_append.sh"
    script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    script.chmod(0o755)

    env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), "PATH": __import__("os").environ.get("PATH", "")}
    # Disable gh title lookup noise by putting a fake gh that fails
    fake_bin = root / "bin"
    fake_bin.mkdir()
    (fake_bin / "gh").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (fake_bin / "gh").chmod(0o755)
    env["PATH"] = str(fake_bin) + ":" + env["PATH"]

    proc1 = subprocess.run(
        ["bash", str(script), "123", "unit test outcome"],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc1.returncode == 0, proc1.stdout + proc1.stderr
    body = (root / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8")
    assert "| #123 |" in body
    assert "unit test outcome" in body

    proc2 = subprocess.run(
        ["bash", str(script), "123", "should skip"],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc2.returncode == 0
    assert "already logged" in proc2.stdout
    body2 = (root / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8")
    assert body2.count("| #123 |") == 1
    assert "should skip" not in body2


def test_workflow_avoids_interpolating_issue_body():
    yml = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event.issue.body" not in yml
    assert "contents: write" in yml
    assert "mvp-closed-log.md" in yml
