"""Offline tests for MVP closed-log helper (#65 / #68)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mvp_closed_log_append.sh"
LOG = ROOT / "docs" / "mvp-closed-log.md"
ROADMAP = ROOT / "docs" / "mvp-roadmap.md"
WORKFLOW = ROOT / ".github" / "workflows" / "mvp-closed-log.yml"
EVIDENCE = ROOT / ".vv" / "mvp-closed-log" / "EVIDENCE.md"
SPEC = ROOT / "docs" / "specs" / "65-68-mvp-closed-log.md"


def test_mvp_artifacts_present():
    assert SCRIPT.is_file()
    assert LOG.is_file()
    assert ROADMAP.is_file()
    assert WORKFLOW.is_file()
    assert EVIDENCE.is_file()
    assert SPEC.is_file()
    text = LOG.read_text(encoding="utf-8")
    assert "YYYY-MM-DD | #N |" in text or "| #9 |" in text
    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert "Milestone" in roadmap
    assert "--backfill" in roadmap


def _prep_repo(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "docs" / "mvp-closed-log.md").write_text(
        "# MVP closed-issue log\n\n## Log\n\n2026-01-01 | #999 | fixture | closed\n",
        encoding="utf-8",
    )
    script = root / "scripts" / "mvp_closed_log_append.sh"
    script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    script.chmod(0o755)

    fake_bin = root / "bin"
    fake_bin.mkdir()
    # Fake gh: issue view fails; api --jq path returns plain issue numbers for backfill.
    (fake_bin / "gh").write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        'if [[ "${1:-}" == "issue" && "${2:-}" == "view" ]]; then exit 1; fi\n'
        'if [[ "${1:-}" == "api" ]]; then printf "%s\\n" 123 124; exit 0; fi\n'
        'if [[ "${1:-}" == "auth" ]]; then exit 0; fi\n'
        "exit 1\n",
        encoding="utf-8",
    )
    (fake_bin / "gh").chmod(0o755)

    env = {**os.environ, "PATH": str(fake_bin) + ":" + os.environ.get("PATH", "")}
    return root, env


def test_mvp_closed_log_append_idempotent(tmp_path):
    root, env = _prep_repo(tmp_path)
    script = root / "scripts" / "mvp_closed_log_append.sh"

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


def test_mvp_closed_log_backfill_idempotent(tmp_path):
    root, env = _prep_repo(tmp_path)
    script = root / "scripts" / "mvp_closed_log_append.sh"

    proc = subprocess.run(
        ["bash", str(script), "--backfill"],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK backfill" in proc.stdout
    body = (root / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8")
    assert "| #123 |" in body
    assert "| #124 |" in body

    proc2 = subprocess.run(
        ["bash", str(script), "--backfill"],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc2.returncode == 0
    body2 = (root / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8")
    assert body2.count("| #123 |") == 1
    assert body2.count("| #124 |") == 1


def test_workflow_avoids_interpolating_issue_body():
    yml = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event.issue.body" not in yml
    assert "contents: write" in yml
    assert "mvp-closed-log.md" in yml
    assert "vars.MVP_CLOSED_LOG_PUSH_MAIN" in yml
    assert "timelineItems" in yml
    assert "ls-remote --exit-code --heads origin" in yml
    # Recreate-from-main force push removed; merge + regular push only.
    assert "git push -u origin \"$BRANCH\" --force" not in yml
    assert "git push -u origin \"$BRANCH\" --force-with-lease" not in yml
