"""Offline tests for MVP closed-log append + workflow structure (#68)."""
"""Offline tests for MVP closed-log helper (#65 / #68)."""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml
ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "mvp-closed-log.yml"
APPEND = ROOT / "scripts" / "mvp_closed_log_append.sh"
LOG = ROOT / "docs" / "mvp-closed-log.md"
EVIDENCE = ROOT / ".vv" / "mvp" / "closed-log.md"
def _run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
def _jq_available(path: str) -> bool:
    return any(Path(p).joinpath("jq").exists() for p in path.split(":") if p)
def _install_fake_gh(fake_bin: Path, json_blob: str) -> None:
    fake_bin.mkdir(parents=True, exist_ok=True)
    gh = fake_bin / "gh"
    gh.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ "${{1:-}}" == "issue" && "${{2:-}}" == "view" ]]; then
              jqprog=""
              args=("$@")
              for i in "${{!args[@]}}"; do
                if [[ "${{args[$i]}}" == "--jq" ]]; then
                  jqprog="${{args[$((i+1))]}}"
                fi
              done
              json='{json_blob}'
              if [[ -n "$jqprog" ]]; then
                printf '%s' "$json" | jq -r "$jqprog"
              else
                printf '%s\\n' "$json"
              fi
              exit 0
            fi
            echo "unexpected: $*" >&2
            exit 99
            """
        ),
        encoding="utf-8",
    gh.chmod(0o755)
def _layout(tmp: Path) -> Path:
    (tmp / "scripts").mkdir()
    (tmp / "docs").mkdir()
    script = tmp / "scripts" / "mvp_closed_log_append.sh"
    script.write_text(APPEND.read_text(encoding="utf-8"), encoding="utf-8")
    script.chmod(0o755)
    log = tmp / "docs" / "mvp-closed-log.md"
    log.write_text(
            """\
            # MVP closed-issue log
            | Closed (UTC) | Issue | Title | Milestone | Labels | Reason |
            |--------------|------:|-------|-----------|--------|--------|
            | 2026-09-01 | #1 | First | M0 | `enhancement` | COMPLETED |
            ## Backfill / append
            ```bash
            bash scripts/mvp_closed_log_append.sh 37
            ```
    return script
def test_workflow_parses_and_uses_env_not_title_interpolation() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    assert data["name"]
    # PyYAML may parse bare `on:` as boolean True.
    on = data.get("on", data.get(True))
    assert on is not None and "issues" in on
    assert "${{ github.event.issue.title }}" not in raw
    assert "${{ github.event.issue.body }}" not in raw
    assert "ISSUE_FROM_EVENT: ${{ github.event.issue.number }}" in raw
    assert "refusing to commit conflict markers" in raw
    assert "append failed" in raw
    assert "git rebase origin/main" in raw
    assert "origin/$BRANCH" in raw
def test_evidence_package_present() -> None:
    text = EVIDENCE.read_text(encoding="utf-8")
    assert "PASS" in text
    assert "mvp_closed_log_append" in text or "mvp-closed-log" in text
    assert "closed-log" in text.lower()
def test_append_inserts_inside_table_escapes_pipes_and_dedupes(tmp_path: Path) -> None:
    script = _layout(tmp_path)
    fake_bin = tmp_path / "bin"
    _install_fake_gh(
        fake_bin,
        '{"state":"CLOSED","closedAt":"2026-09-08T12:00:00Z","number":42,'
        '"title":"Title with | pipe","milestone":{"title":"M0"},'
        '"labels":[{"name":"bug"},{"name":"enhancement"}],"stateReason":"COMPLETED"}',
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
    env["GITHUB_REPOSITORY"] = "team-project-pikachu/IoT-ASP"
    if not _jq_available(env["PATH"]):
        pytest.skip("jq not on PATH")
    proc = _run(["bash", str(script), "42"], env=env, cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = (tmp_path / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8")
    assert "| #42 |" in body
    assert "Title with / pipe" in body
    before, _after = body.split("## Backfill", 1)
    table_lines = [ln for ln in before.strip().splitlines() if ln.startswith("|")]
    assert table_lines[-1].startswith("| 2026-09-08 | #42 |")
    # Blank separator is after the new row, not between table rows.
    assert before.rstrip().endswith(table_lines[-1])
    proc2 = _run(["bash", str(script), "42"], env=env, cwd=tmp_path)
    assert proc2.returncode == 0
    assert "already logged" in proc2.stdout
    assert (tmp_path / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8").count("| #42 |") == 1
def test_append_fails_when_issue_not_closed(tmp_path: Path) -> None:
        '{"state":"OPEN","closedAt":null,"number":99,"title":"open",'
        '"milestone":null,"labels":[],"stateReason":null}',
    proc = _run(["bash", str(script), "99"], env=env, cwd=tmp_path)
    assert proc.returncode != 0
def test_repo_log_has_backfill_section() -> None:
    text = LOG.read_text(encoding="utf-8")
    assert "| Closed (UTC) |" in text
    assert "## Backfill" in text
SCRIPT = ROOT / "scripts" / "mvp_closed_log_append.sh"
ROADMAP = ROOT / "docs" / "mvp-roadmap.md"
EVIDENCE = ROOT / ".vv" / "mvp-closed-log" / "EVIDENCE.md"
SPEC = ROOT / "docs" / "specs" / "65-68-mvp-closed-log.md"
def test_mvp_artifacts_present():
    assert SCRIPT.is_file()
    assert LOG.is_file()
    assert ROADMAP.is_file()
    assert WORKFLOW.is_file()
    assert EVIDENCE.is_file()
    assert SPEC.is_file()
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
    script = root / "scripts" / "mvp_closed_log_append.sh"
    script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
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
    (fake_bin / "gh").chmod(0o755)
    env = {**os.environ, "PATH": str(fake_bin) + ":" + os.environ.get("PATH", "")}
    return root, env
def test_mvp_closed_log_append_idempotent(tmp_path):
    root, env = _prep_repo(tmp_path)
    proc1 = subprocess.run(
        ["bash", str(script), "123", "unit test outcome"],
        cwd=str(root),
    assert proc1.returncode == 0, proc1.stdout + proc1.stderr
    body = (root / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8")
    assert "| #123 |" in body
    assert "unit test outcome" in body
    proc2 = subprocess.run(
        ["bash", str(script), "123", "should skip"],
    body2 = (root / "docs" / "mvp-closed-log.md").read_text(encoding="utf-8")
    assert body2.count("| #123 |") == 1
    assert "should skip" not in body2
def test_mvp_closed_log_backfill_idempotent(tmp_path):
    proc = subprocess.run(
        ["bash", str(script), "--backfill"],
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK backfill" in proc.stdout
    assert "| #124 |" in body
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
