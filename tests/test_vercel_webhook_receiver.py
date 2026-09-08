"""Tests for services/vercel-webhook-receiver (issue #37 notify path)."""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECV = ROOT / "services" / "vercel-webhook-receiver"
HANDLER = RECV / "handler.py"
NOTIFY = RECV / "notify_once.py"
DUMMY_SECRET = "test-webhook-secret-not-real"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def handler():
    return _load("vercel_webhook_handler", HANDLER)


def _sign(body: bytes, secret: str = DUMMY_SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()


def test_verify_ok(handler):
    raw = b'{"type":"deployment.succeeded","id":"evt_1","payload":{"url":"https://example.vercel.app"}}'
    assert handler.verify_signature(secret=DUMMY_SECRET, raw_body=raw, header_sig=_sign(raw))


def test_verify_rejects_mismatch(handler):
    raw = b'{"type":"deployment.error"}'
    assert not handler.verify_signature(secret=DUMMY_SECRET, raw_body=raw, header_sig="deadbeef")


def test_handle_post_dry_run(handler):
    event = {
        "type": "deployment.succeeded",
        "id": "evt_abc",
        "payload": {"url": "https://hop-ultrasonic-1digital-design.vercel.app"},
    }
    raw = json.dumps(event, separators=(",", ":")).encode()
    status, body = handler.handle_post(
        raw_body=raw,
        header_sig=_sign(raw),
        environ={"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET, "WEBHOOK_DRY_RUN": "1"},
        dry_run=True,
    )
    assert status == 200
    assert body["ok"] is True and body["notified"] is False and body["dryRun"] is True
    assert body["client_payload"]["type"] == "deployment.succeeded"
    assert body["client_payload"]["url"].startswith("https://")
    assert body["client_payload"]["id"] == "evt_abc"


def test_handle_post_bad_sig(handler):
    raw = b'{"type":"deployment.created"}'
    with pytest.raises(handler.WebhookError) as ei:
        handler.handle_post(
            raw_body=raw,
            header_sig="00" * 20,
            environ={"VERCEL_WEBHOOK_SECRET": DUMMY_SECRET},
            dry_run=True,
        )
    assert ei.value.status == 403


def test_handle_post_live_dispatch(handler):
    event = {"type": "deployment.error", "id": "e2", "payload": {"url": "https://x.vercel.app"}}
    raw = json.dumps(event).encode()
    calls: list[Any] = []

    class Resp:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=20.0):
        calls.append((req.full_url, req.data, dict(req.header_items())))
        return Resp()

    with mock.patch("urllib.request.urlopen", fake_urlopen):
        status, body = handler.handle_post(
            raw_body=raw,
            header_sig=_sign(raw),
            environ={
                "VERCEL_WEBHOOK_SECRET": DUMMY_SECRET,
                "GITHUB_TOKEN": "ghs_test_not_real",
            },
            dry_run=False,
        )
    assert status == 200 and body["notified"] is True
    assert len(calls) == 1
    url, data, headers = calls[0]
    assert url.endswith("/repos/team-project-pikachu/IoT-ASP/dispatches")
    payload = json.loads(data.decode())
    assert payload["event_type"] == "vercel-deployment"
    assert payload["client_payload"]["type"] == "deployment.error"
    assert "Authorization" in {k.title(): v for k, v in headers.items()} or any(
        k.lower() == "authorization" for k in headers
    )


def test_redact_normalizes_schemeless_deployment_url(handler):
    event = {
        "type": "deployment.succeeded",
        "id": "evt_host",
        "payload": {"deployment": {"url": "hop-ultrasonic-1digital-design.vercel.app"}},
    }
    out = handler.redact_client_payload(event)
    assert out["url"] == "https://hop-ultrasonic-1digital-design.vercel.app"


def test_public_https_url_rejects_dangerous_schemes(handler):
    assert handler._public_https_url("vbscript:alert(1)") == ""
    assert handler._public_https_url("javascript:alert(1)") == ""
    assert handler._public_https_url("data:text/html,hi") == ""
    assert handler._public_https_url("http://evil.example") == ""
    assert handler._public_https_url("https://ok.vercel.app") == "https://ok.vercel.app"


def test_notify_once_cli_dry(tmp_path, monkeypatch):
    mod = _load("vercel_webhook_notify_once", NOTIFY)
    event = {"type": "deployment.canceled", "id": "c1", "payload": {"url": "https://y.vercel.app"}}
    body_path = tmp_path / "body.json"
    raw = json.dumps(event).encode()
    body_path.write_bytes(raw)
    monkeypatch.setenv("VERCEL_WEBHOOK_SECRET", DUMMY_SECRET)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_APP_INSTALLATION_TOKEN", raising=False)
    rc = mod.main(["--body-file", str(body_path), "--signature", _sign(raw)])
    assert rc == 0


def test_notify_once_live_requires_token(tmp_path, monkeypatch):
    mod = _load("vercel_webhook_notify_once_live", NOTIFY)
    event = {"type": "deployment.succeeded", "id": "l1", "payload": {"url": "https://z.vercel.app"}}
    body_path = tmp_path / "body.json"
    raw = json.dumps(event).encode()
    body_path.write_bytes(raw)
    monkeypatch.setenv("VERCEL_WEBHOOK_SECRET", DUMMY_SECRET)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_APP_INSTALLATION_TOKEN", raising=False)
    rc = mod.main(["--body-file", str(body_path), "--signature", _sign(raw), "--live"])
    assert rc == 1
