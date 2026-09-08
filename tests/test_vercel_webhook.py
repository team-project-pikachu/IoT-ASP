"""Regression tests for Vercel webhook HMAC verify + notify workflow (issue #37).

Offline / deterministic: no network, dummy secrets only (never printed).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "vercel_webhook_verify.py"
WORKFLOW = ROOT / ".github" / "workflows" / "vercel-webhook.yml"
DUMMY_SECRET = "test-webhook-secret-not-real"


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha1).hexdigest()


def _run_verify_bytes(
    env: dict[str, str] | None,
    args: list[str],
    stdin: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    full_env = os.environ.copy()
    full_env.pop("VERCEL_WEBHOOK_SECRET", None)
    if env is not None:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(VERIFY), *args],
        input=stdin,
        capture_output=True,
        env=full_env,
        cwd=str(ROOT),
        check=False,
    )


@pytest.fixture
def body_file(tmp_path: Path) -> Path:
    p = tmp_path / "body.json"
    p.write_bytes(b'{"type":"deployment.succeeded","id":"evt_test"}')
    return p


# ── HMAC verifier ─────────────────────────────────────────────────────────────


def test_verify_match_body_file(body_file: Path):
    raw = body_file.read_bytes()
    sig = _sign(DUMMY_SECRET, raw)
    r = _run_verify_bytes(
        {"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
        ["--body-file", str(body_file), "--signature", sig],
    )
    assert r.returncode == 0
    assert b"OK vercel_webhook_verify" in r.stdout
    assert DUMMY_SECRET.encode() not in r.stdout + r.stderr


def test_verify_mismatch(body_file: Path):
    r = _run_verify_bytes(
        {"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
        ["--body-file", str(body_file), "--signature", "0" * 40],
    )
    assert r.returncode == 1
    assert b"mismatch" in r.stderr.lower()
    assert DUMMY_SECRET.encode() not in r.stdout + r.stderr


def test_verify_signature_file(body_file: Path, tmp_path: Path):
    sig = _sign(DUMMY_SECRET, body_file.read_bytes())
    sig_path = tmp_path / "sig.txt"
    sig_path.write_text(sig + "\n", encoding="utf-8")
    r = _run_verify_bytes(
        {"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
        ["--body-file", str(body_file), "--signature-file", str(sig_path)],
    )
    assert r.returncode == 0


def test_verify_stdin(body_file: Path):
    raw = body_file.read_bytes()
    sig = _sign(DUMMY_SECRET, raw)
    r = _run_verify_bytes(
        {"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
        ["--signature", sig],
        stdin=raw,
    )
    assert r.returncode == 0


def test_verify_missing_secret(body_file: Path):
    r = _run_verify_bytes(
        None,
        ["--body-file", str(body_file), "--signature", "abc"],
    )
    assert r.returncode == 1
    assert b"VERCEL_WEBHOOK_SECRET" in r.stderr


def test_verify_missing_signature_usage(body_file: Path):
    r = _run_verify_bytes(
        {"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
        ["--body-file", str(body_file)],
    )
    assert r.returncode == 2
    assert b"usage:" in r.stderr


def test_verify_both_signature_flags_usage(body_file: Path, tmp_path: Path):
    sig_path = tmp_path / "sig.txt"
    sig_path.write_text("deadbeef", encoding="utf-8")
    r = _run_verify_bytes(
        {"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
        [
            "--body-file",
            str(body_file),
            "--signature",
            "abc",
            "--signature-file",
            str(sig_path),
        ],
    )
    assert r.returncode == 2


def test_verify_empty_signature(body_file: Path):
    r = _run_verify_bytes(
        {"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
        ["--body-file", str(body_file), "--signature", "   "],
    )
    assert r.returncode == 1
    assert b"empty signature" in r.stderr


# ── Workflow structure ────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def wf_raw() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def wf(wf_raw: str) -> dict:
    return yaml.safe_load(wf_raw)


@pytest.fixture(scope="module")
def on(wf: dict) -> dict:
    return wf.get("on", wf.get(True))


def test_webhook_workflow_parses_and_name(wf: dict):
    assert wf["name"] == "Vercel webhook notify"


def test_webhook_workflow_triggers(on: dict):
    assert on["repository_dispatch"]["types"] == ["vercel-deployment"]
    wd = on["workflow_dispatch"]["inputs"]
    assert wd["type"]["required"] is True
    assert wd["type"]["default"] == "deployment.succeeded"
    assert "url" in wd


def test_webhook_workflow_minimal_permissions(wf: dict):
    assert wf["permissions"] == {"contents": "read"}


def test_webhook_workflow_summary_wiring(wf_raw: str, wf: dict):
    job = wf["jobs"]["summarize"]
    step = job["steps"][0]
    env = step["env"]
    assert "github.event.client_payload.type" in env["EVENT_TYPE"]
    assert "inputs.type" in env["EVENT_TYPE"]
    assert "github.event.client_payload.url" in env["DEPLOY_URL"]
    assert "inputs.url" in env["DEPLOY_URL"]
    assert env["EVENT_NAME"] == "${{ github.event_name }}"
    run = step["run"]
    assert "EVENT_NAME" in run
    assert "GITHUB_STEP_SUMMARY" in run
    # Must not hard-code both triggers as the source row.
    assert "repository_dispatch` / `workflow_dispatch" not in wf_raw
    assert "secrets.VERCEL_WEBHOOK_SECRET" not in run  # HMAC stays outside Actions
