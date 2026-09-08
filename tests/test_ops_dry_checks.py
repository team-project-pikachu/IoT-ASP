"""Ops dry-check scripts for Balanced PR8 (#27 #60 #63) — offline shape + dry-run."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_adk_deploy_dry_check_runs() -> None:
    r = subprocess.run(
        ["bash", str(ROOT / "scripts" / "adk_deploy_dry_check.sh")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK adk_deploy_dry_check" in r.stdout
    assert "adk deploy" in r.stdout  # recipe text only


def test_scripts_bash_syntax() -> None:
    for rel in ("scripts/adk_deploy_dry_check.sh", "scripts/gh_protect_main_status.sh"):
        r = subprocess.run(["bash", "-n", str(ROOT / rel)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


def test_issue27_inventory_doc_has_names_only() -> None:
    text = (ROOT / "docs" / "issues" / "ISSUE-27-vercel-actions-secrets.md").read_text(encoding="utf-8")
    assert "VERCEL_TOKEN" in text
    assert "vercel - hop-ultrasonic" in text
    assert "names only" in text.lower()
    assert "MISSING" in text  # TOKEN still missing honesty
    assert "eyJ" not in text
