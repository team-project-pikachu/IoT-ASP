"""Tests for .github/rulesets/main-protection.json (issue #27, branch protection).

Offline, deterministic: parses the ruleset JSON and .github/workflows/ci.yml (PyYAML) and asserts
the ruleset's required status-check contexts are exactly the CI job ``name:`` values.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RULESET = ROOT / ".github" / "rulesets" / "main-protection.json"
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"
SCRIPT = ROOT / "scripts" / "gh_protect_main.sh"
DOC = ROOT / "docs" / "branch-protection.md"


@pytest.fixture(scope="module")
def ruleset() -> dict:
    return json.loads(RULESET.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ci_job_names() -> set[str]:
    wf = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    jobs = wf["jobs"]
    names = {job["name"] for job in jobs.values()}
    assert len(names) == len(jobs), "every ci.yml job must have a unique name:"
    return names


def _rules_by_type(ruleset: dict) -> dict[str, dict]:
    out = {r["type"]: r for r in ruleset["rules"]}
    assert len(out) == len(ruleset["rules"]), "duplicate rule types"
    return out


# ── RS-01 shape ───────────────────────────────────────────────────────────────


def test_json_loads_and_required_keys(ruleset):
    for key in ("name", "target", "enforcement", "bypass_actors", "conditions", "rules"):
        assert key in ruleset, key
    assert ruleset["name"] == "main-protection"
    assert ruleset["target"] == "branch"
    assert isinstance(ruleset["rules"], list) and ruleset["rules"]
    # Importable JSON must not carry server-assigned fields.
    for forbidden in ("id", "source", "source_type", "_links", "node_id", "created_at", "updated_at"):
        assert forbidden not in ruleset, forbidden


def test_enforcement_active(ruleset):
    assert ruleset["enforcement"] == "active"


def test_targets_default_branch_only(ruleset):
    ref = ruleset["conditions"]["ref_name"]
    assert ref["include"] == ["~DEFAULT_BRANCH"]
    assert ref["exclude"] == []


def test_no_bypass_actors_by_default(ruleset):
    assert ruleset["bypass_actors"] == []


# ── RS-02 rules ───────────────────────────────────────────────────────────────


def test_rule_types(ruleset):
    assert set(_rules_by_type(ruleset)) == {
        "deletion",
        "non_fast_forward",
        "pull_request",
        "required_status_checks",
    }


def test_pull_request_parameters(ruleset):
    p = _rules_by_type(ruleset)["pull_request"]["parameters"]
    assert p["required_approving_review_count"] == 0
    assert p["dismiss_stale_reviews_on_push"] is True
    assert p["require_code_owner_review"] is False
    assert p["require_last_push_approval"] is False
    assert p["required_review_thread_resolution"] is True
    assert set(p["allowed_merge_methods"]) == {"squash", "merge"}
    assert "rebase" not in p["allowed_merge_methods"]


def test_required_status_checks_parameters(ruleset):
    p = _rules_by_type(ruleset)["required_status_checks"]["parameters"]
    assert p["strict_required_status_checks_policy"] is True
    assert p["do_not_enforce_on_create"] is False
    checks = p["required_status_checks"]
    assert checks, "at least one required check"
    for c in checks:
        assert set(c) <= {"context", "integration_id"}, c
        assert isinstance(c["context"], str) and c["context"].strip()


def test_contexts_match_ci_job_names_exactly(ruleset, ci_job_names):
    checks = _rules_by_type(ruleset)["required_status_checks"]["parameters"]["required_status_checks"]
    contexts = [c["context"] for c in checks]
    assert len(contexts) == len(set(contexts)), "duplicate contexts"
    assert set(contexts) == ci_job_names, (
        f"ruleset contexts {sorted(contexts)} must equal ci.yml job names {sorted(ci_job_names)}"
    )


def test_pr_issue_ref_job_is_pr_only(ruleset):
    # `PR must reference an issue` only runs on pull_request events; that is fine for a required
    # check because merges to main always go through a PR under this ruleset.
    wf = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    job = wf["jobs"]["pr_issue_ref"]
    assert job["name"] == "PR must reference an issue"
    assert "pull_request" in job["if"]


# ── RS-03 script + docs ───────────────────────────────────────────────────────


def test_script_syntax_and_conventions():
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text
    assert 'REPO="${REPO:-team-project-pikachu/IoT-ASP}"' in text
    assert "gh auth status" in text
    assert "--input" in text and "main-protection.json" in text
    assert "-X PUT" in text and "-X POST" in text
    assert "allow_auto_merge=true" in text and "delete_branch_on_merge=true" in text
    assert 'echo "OK gh_protect_main"' in text
    res = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr


def test_script_dry_run_offline(tmp_path):
    env = {"DRY_RUN": "1", "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    res = subprocess.run(
        ["bash", str(SCRIPT)], capture_output=True, text=True, env=env, cwd=str(tmp_path)
    )
    assert res.returncode == 0, res.stderr
    assert "team-project-pikachu/IoT-ASP" in res.stdout
    assert "OK gh_protect_main (dry-run)" in res.stdout


def test_script_no_secret_values():
    text = SCRIPT.read_text(encoding="utf-8") + DOC.read_text(encoding="utf-8")
    import re

    assert not re.search(r"gh[pousr]_[A-Za-z0-9]{20,}", text)
    assert not re.search(r"github_pat_[A-Za-z0-9_]{20,}", text)


def test_docs_sections():
    text = DOC.read_text(encoding="utf-8")
    for needle in (
        "## Why",
        "## What each rule does",
        "## How to apply",
        "## How to verify",
        "## Auto-merge and the Cursor flow",
        "## Plan availability",
        "## Acceptance",
        "## Sources",
        "settings/rules/new?target=branch&enforcement=disabled",
        "gh ruleset check main",
        "RepositoryRole",
        "bypass_mode",
        "required_approving_review_count",
        "~DEFAULT_BRANCH",
        "/websites/github_en_rest",
    ):
        assert needle in text, needle


def test_docs_emergency_path_uses_disabled_not_evaluate():
    # Regression (adversarial review, issue #27): the "Evaluate" enforcement status is GitHub
    # Enterprise-only; on this repo's plan the picker offers only Active / Disabled. The emergency
    # path must say "Disabled", and any mention of `evaluate` must carry the Enterprise caveat so the
    # doc never again sends an admin looking for an option that is not there.
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## Auto-merge and the Cursor flow", 1)[1].split("## Plan availability", 1)[0]
    assert "Emergency" in section
    assert "Disabled" in section, "emergency path must use the Disabled enforcement status"
    assert "set the ruleset to `evaluate`" not in text
    for line in text.splitlines():
        if "evaluate" in line.lower():
            assert "enterprise" in line.lower(), f"mention of evaluate without Enterprise caveat: {line!r}"
