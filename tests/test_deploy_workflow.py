"""Structure tests for the continuous-ship pipeline (issue #27) — offline, deterministic.

Covers DP-01 … DP-13 from docs/specs/27-continuous-ship-dev-test-prod.md: parses
.github/workflows/deploy.yml with PyYAML, vercel.json with json, and exercises the two bash
scripts without network (usage error + a closed local port only).
"""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "deploy.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
VERCEL_JSON = ROOT / "vercel.json"
SMOKE = ROOT / "scripts" / "deploy_smoke.sh"
SECRETS_CHECK = ROOT / "scripts" / "vercel_secrets_check.sh"
DEPLOY_DOC = ROOT / "docs" / "deploy.md"
EVIDENCE_CI = ROOT / ".vv" / "ci" / "continuous-ship.md"
EVIDENCE_VERCEL = ROOT / ".vv" / "deploy" / "VERCEL.md"

EXPECTED_SECRETS = {
    "VERCEL_TOKEN",
    "VERCEL_ORG_ID",
    "VERCEL_PROJECT_ID",
    "VERCEL_DEPLOY_HOOK_PROD",
    "VERCEL_AUTOMATION_BYPASS_SECRET",
}
TOKEN_LIKE = re.compile(r"AIza[0-9A-Za-z_-]{20,}|vercel_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}")
RUN_GUARD_SUCCESS = "workflow_run.conclusion == 'success'"
RUN_GUARD_BRANCH = "head_branch == 'main'"


@pytest.fixture(scope="module")
def raw() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def wf(raw: str) -> dict:
    return yaml.safe_load(raw)


@pytest.fixture(scope="module")
def on(wf: dict) -> dict:
    # PyYAML (YAML 1.1) parses the bare `on` key as boolean True.
    return wf.get("on", wf.get(True))


@pytest.fixture(scope="module")
def jobs(wf: dict) -> dict:
    return wf["jobs"]


@pytest.fixture(scope="module")
def cfg() -> dict:
    return json.loads(VERCEL_JSON.read_text(encoding="utf-8"))


def _run_text(job: dict) -> str:
    return "\n".join(str(s.get("run", "")) for s in job.get("steps", []))


def _needs(job: dict) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


# ── DP-01 ────────────────────────────────────────────────────────────────────
def test_dp01_workflow_parses_and_name(wf: dict):
    assert wf["name"] == "Deploy — dev → test → prod"


# ── DP-02 ────────────────────────────────────────────────────────────────────
def test_dp02_triggers(on: dict):
    ci_name_line = CI_WORKFLOW.read_text(encoding="utf-8").splitlines()[0]
    assert ci_name_line.startswith("name: ")
    ci_name = ci_name_line[len("name: ") :].strip()
    wr = on["workflow_run"]
    assert wr["workflows"] == [ci_name] == ["CI — no breaking changes"]
    assert wr["types"] == ["completed"]
    assert wr["branches"] == ["main"]
    inputs = on["workflow_dispatch"]["inputs"]
    assert inputs["target"]["type"] == "choice"
    assert inputs["target"]["options"] == ["dev", "test", "prod"]
    assert inputs["target"]["default"] == "prod"
    assert "ref" in inputs
    assert not inputs["ref"].get("required", False)


# ── DP-03 ────────────────────────────────────────────────────────────────────
def test_dp03_permissions_and_concurrency(wf: dict):
    assert wf["permissions"] == {"contents": "read", "deployments": "write"}
    assert wf["concurrency"]["group"] == "deploy-main"
    assert wf["concurrency"]["cancel-in-progress"] is False


# ── DP-04 ────────────────────────────────────────────────────────────────────
def test_dp04_job_graph(jobs: dict):
    assert {"secrets_check", "gates", "deploy_dev", "test", "deploy_prod"} <= set(jobs)
    assert "needs" not in jobs["secrets_check"]
    assert "needs" not in jobs["gates"]
    assert set(_needs(jobs["deploy_dev"])) == {"secrets_check", "gates"}
    assert _needs(jobs["test"]) == ["deploy_dev"]
    prod_needs = set(_needs(jobs["deploy_prod"]))
    assert {"test", "secrets_check", "gates"} <= prod_needs


# ── DP-05 ────────────────────────────────────────────────────────────────────
def test_dp05_environments(jobs: dict):
    assert jobs["deploy_dev"]["environment"]["name"] == "dev"
    assert jobs["test"]["environment"]["name"] == "test"
    prod_env = jobs["deploy_prod"]["environment"]
    assert prod_env["name"] == "production"
    assert "PROD_URL" in prod_env["url"]
    # exact hostname match on extracted URLs (CodeQL py/incomplete-url-substring-sanitization)
    hosts = [urlparse(u).hostname for u in re.findall(r"https?://[^\s<>\"'}]+", str(prod_env["url"]))]
    prod_host = "hop-ultrasonic-1digital-design.vercel.app"
    assert any(h == prod_host for h in hosts), prod_env["url"]


# ── DP-06 ────────────────────────────────────────────────────────────────────
def test_dp06_success_guard(jobs: dict):
    for name, job in jobs.items():
        cond = str(job.get("if", ""))
        assert RUN_GUARD_SUCCESS in cond, name
        assert RUN_GUARD_BRANCH in cond, name
        assert "workflow_dispatch" in cond, name
    assert "has_cli == 'true'" in jobs["deploy_dev"]["if"]
    prod_if = jobs["deploy_prod"]["if"]
    assert "has_hook" in prod_if
    assert "!cancelled()" in prod_if
    assert "needs.gates.result == 'success'" in prod_if
    assert "needs.test.result == 'success'" in prod_if


# ── DP-07 ────────────────────────────────────────────────────────────────────
def test_dp07_cli_flags(jobs: dict):
    dev = _run_text(jobs["deploy_dev"])
    assert "vercel pull --yes --environment=preview" in dev
    assert "vercel build" in dev
    assert "vercel deploy --prebuilt" in dev
    assert "--prod" not in dev
    prod = _run_text(jobs["deploy_prod"])
    assert "vercel pull --yes --environment=production" in prod
    assert "vercel build --prod" in prod
    assert "vercel deploy --prebuilt --prod" in prod
    assert "curl -fsS -X POST" in prod
    assert "scripts/deploy_smoke.sh" in prod
    for name, job in jobs.items():
        if name != "deploy_prod":
            assert "--prod" not in _run_text(job), name
    for name in ("deploy_dev", "deploy_prod"):
        m = re.search(r"npm i -g vercel@(\d+)\b", _run_text(jobs[name]))
        assert m, name
        assert m.group(1) == "59", name  # pinned major; bump deliberately with docs/deploy.md
    # Preview job must not touch prod; smoke test wired into test job
    assert "scripts/deploy_smoke.sh" in _run_text(jobs["test"])


# ── DP-08 ────────────────────────────────────────────────────────────────────
def test_dp08_secrets_hygiene(raw: str):
    refs = re.findall(r"secrets\.[A-Za-z0-9_]+", raw)
    assert refs, "workflow must reference secrets"
    well_formed = re.findall(r"\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}", raw)
    assert len(refs) == len(well_formed), "every secrets.* must be a ${{ secrets.NAME }} expression"
    assert set(well_formed) == EXPECTED_SECRETS
    for path in (WORKFLOW, VERCEL_JSON, DEPLOY_DOC, SMOKE, SECRETS_CHECK, EVIDENCE_CI, EVIDENCE_VERCEL):
        assert not TOKEN_LIKE.search(path.read_text(encoding="utf-8")), path
    for line in raw.splitlines():
        if "echo" in line:
            for var in ("$VT", "$VO", "$VP", "$HP", "$VERCEL_TOKEN", "$VERCEL_DEPLOY_HOOK_PROD"):
                assert var not in line, line
    # tokens only ever travel on --token= (run:) or env:, never as literal values
    assert "--token=${{ secrets.VERCEL_TOKEN }}" in raw


# ── DP-09 ────────────────────────────────────────────────────────────────────
def test_dp09_secrets_check_contract(jobs: dict):
    job = jobs["secrets_check"]
    steps = job["steps"]
    assert len(steps) == 1
    step = steps[0]
    assert step["id"] == "probe"
    env = step["env"]
    assert set(env) == {"VT", "VO", "VP", "HP"}
    assert env["VT"] == "${{ secrets.VERCEL_TOKEN }}"
    assert env["VO"] == "${{ secrets.VERCEL_ORG_ID }}"
    assert env["VP"] == "${{ secrets.VERCEL_PROJECT_ID }}"
    assert env["HP"] == "${{ secrets.VERCEL_DEPLOY_HOOK_PROD }}"
    run = step["run"]
    assert 'echo "has_cli=$has_cli" >> "$GITHUB_OUTPUT"' in run
    assert 'echo "has_hook=$has_hook" >> "$GITHUB_OUTPUT"' in run
    assert "::notice" in run
    assert "docs/deploy.md" in run
    assert "issue #27" in run
    assert "exit 1" not in run
    assert {"has_cli", "has_hook"} <= set(job["outputs"])
    assert job["outputs"]["target"] == "${{ github.event.inputs.target || 'prod' }}"


# ── DP-10 ────────────────────────────────────────────────────────────────────
def test_dp10_smoke_script_offline():
    for script in (SMOKE, SECRETS_CHECK):
        assert subprocess.run(["bash", "-n", str(script)], cwd=ROOT).returncode == 0
    usage = subprocess.run(["bash", str(SMOKE)], cwd=ROOT, capture_output=True, text=True)
    assert usage.returncode == 2
    assert "usage:" in usage.stderr
    closed = subprocess.run(
        ["bash", str(SMOKE), "http://127.0.0.1:9"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "SMOKE_RETRIES": "1", "SMOKE_SLEEP_S": "0"},
    )
    assert closed.returncode != 0
    assert "FAIL:" in closed.stderr + closed.stdout
    text = SMOKE.read_text(encoding="utf-8")
    for marker in (
        "Hold / Manual",
        "holdManual",
        "schemaVersion",
        "Permissions-Policy",
        "microphone",
        "application/manifest+json",
        "x-vercel-protection-bypass",
        "OK deploy_smoke",
        "set -euo pipefail",
    ):
        assert marker in text, marker


def test_dp10b_secrets_check_script_offline():
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
    missing = subprocess.run(["bash", str(SECRETS_CHECK)], cwd=ROOT, capture_output=True, text=True, env=env)
    assert missing.returncode == 1
    assert "VERCEL_TOKEN: MISSING" in missing.stdout
    present = subprocess.run(
        ["bash", str(SECRETS_CHECK)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            **env,
            "VERCEL_TOKEN": "fake-token-value-1",
            "VERCEL_ORG_ID": "fake-org-value-2",
            "VERCEL_PROJECT_ID": "fake-project-value-3",
        },
    )
    assert present.returncode == 0
    assert "OK vercel_secrets_check" in present.stdout
    assert "VERCEL_TOKEN: set" in present.stdout
    # values must never be echoed — only names
    for fake in ("fake-token-value-1", "fake-org-value-2", "fake-project-value-3"):
        assert fake not in present.stdout + present.stderr


# ── DP-11 ────────────────────────────────────────────────────────────────────
def test_dp11_vercel_json(cfg: dict):
    assert cfg["git"]["deploymentEnabled"]["main"] is False
    assert "github" not in cfg
    assert cfg["cleanUrls"] is True
    assert cfg["trailingSlash"] is False
    rules = {r["source"]: {h["key"]: h["value"] for h in r["headers"]} for r in cfg["headers"]}
    assert rules["/(.*)"] == {
        "Permissions-Policy": "microphone=(self), autoplay=(self), accelerometer=(self), gyroscope=(self)",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "public, max-age=0, must-revalidate",
    }
    assert rules["/manifest.webmanifest"] == {"Content-Type": "application/manifest+json"}


# ── DP-12 ────────────────────────────────────────────────────────────────────
def test_dp12_docs_and_evidence():
    doc = DEPLOY_DOC.read_text(encoding="utf-8")
    for marker in (
        "vercel.com/1digital-design/hop-ultrasonic/settings/git",
        "gh-actions-prod",
        "VERCEL_DEPLOY_HOOK_PROD",
        "gh secret set",
        "vercel rollback",
        "vercel promote",
        "## Sources",
        "git.deploymentEnabled",
        "workflow_dispatch",
    ):
        assert marker in doc, marker
    status = "secrets not set as of 2026-09-08 (issue #27)"
    assert status in EVIDENCE_CI.read_text(encoding="utf-8")
    assert status in EVIDENCE_VERCEL.read_text(encoding="utf-8")
    script = SECRETS_CHECK.read_text(encoding="utf-8")
    assert "op://dev/" in script
    assert "gh secret set VERCEL_TOKEN --repo team-project-pikachu/IoT-ASP" in script
    assert "scripts/op_secrets_to_gh.sh" in script


# ── DP-13 ────────────────────────────────────────────────────────────────────
def test_dp13_dispatch_semantics(wf: dict, jobs: dict):
    # `env` context is not available in job-level `if:` — the target travels as an expression / job output.
    assert "target || 'prod') != 'dev'" in jobs["test"]["if"]
    assert "outputs.target == 'prod'" in jobs["deploy_prod"]["if"]
    env = wf["env"]
    assert "inputs.target" in env["TARGET"] and "'prod'" in env["TARGET"]
    assert "workflow_run.head_sha" in env["DEPLOY_REF"]
    assert "vars.PROD_URL" in env["PROD_URL"]
    # every checkout deploys the commit CI tested
    for name in ("gates", "deploy_dev", "test", "deploy_prod"):
        checkouts = [s for s in jobs[name]["steps"] if str(s.get("uses", "")).startswith("actions/checkout@")]
        assert checkouts, name
        assert checkouts[0]["with"]["ref"] == "${{ env.DEPLOY_REF }}", name
    # hook-only fallback: prod may run when test was skipped only because the CLI secrets are absent
    assert "needs.test.result == 'skipped' && needs.secrets_check.outputs.has_cli != 'true'" in jobs["deploy_prod"]["if"]
