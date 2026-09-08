"""Vercel webhook → GitHub repository_dispatch notify (issue #37).

stdlib only. Never logs secret values.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_REPO = "team-project-pikachu/IoT-ASP"
EVENT_TYPE = "vercel-deployment"
API_VERSION = "2022-11-28"


class WebhookError(Exception):
    """Fail-closed receiver error with an HTTP status code."""

    def __init__(self, message: str, *, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def require_vercel_secret(environ: dict[str, str] | None = None) -> str:
    env = environ if environ is not None else os.environ
    secret = env.get("VERCEL_WEBHOOK_SECRET")
    if not secret:
        raise WebhookError(
            "VERCEL_WEBHOOK_SECRET unset (op://dev/VERCEL_WEBHOOK_SECRET/credential)",
            status=500,
        )
    return secret


def github_token(environ: dict[str, str] | None = None) -> str | None:
    """Return a GitHub auth token for repository_dispatch, or None (dry-run)."""
    env = environ if environ is not None else os.environ
    return env.get("GITHUB_TOKEN") or env.get("GH_APP_INSTALLATION_TOKEN")


def verify_signature(*, secret: str, raw_body: bytes, header_sig: str) -> bool:
    """HMAC-SHA1(raw body) vs x-vercel-signature (constant-time)."""
    if not header_sig or not isinstance(header_sig, str):
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha1).hexdigest()
    if len(expected) != len(header_sig):
        return False
    return hmac.compare_digest(expected, header_sig)


def redact_client_payload(event: dict[str, Any]) -> dict[str, str]:
    """Public fields only — never secrets."""
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    url = ""
    if isinstance(payload, dict):
        for key in ("url", "deploymentUrl", "alias"):
            val = payload.get(key)
            if isinstance(val, str) and val.startswith("https://"):
                url = val
                break
        meta = payload.get("deployment") if isinstance(payload.get("deployment"), dict) else {}
        if not url and isinstance(meta, dict):
            for key in ("url", "id"):
                val = meta.get(key)
                if isinstance(val, str) and val:
                    url = val if val.startswith("https://") else url
                    break
    eid = event.get("id")
    return {
        "type": str(event.get("type") or "unknown"),
        "url": url,
        "id": str(eid) if eid is not None else "",
    }


def parse_verified_event(*, secret: str, raw_body: bytes, header_sig: str) -> dict[str, Any]:
    if not verify_signature(secret=secret, raw_body=raw_body, header_sig=header_sig):
        raise WebhookError("signature mismatch", status=403)
    try:
        event = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookError(f"invalid JSON body: {exc}", status=400) from exc
    if not isinstance(event, dict):
        raise WebhookError("event root must be an object", status=400)
    return event


def fire_repository_dispatch(
    client_payload: dict[str, str],
    *,
    token: str,
    repo: str = DEFAULT_REPO,
    timeout_s: float = 20.0,
) -> None:
    body = json.dumps(
        {"event_type": EVENT_TYPE, "client_payload": client_payload},
        separators=(",", ":"),
    ).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/dispatches",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "iot-asp-vercel-webhook-receiver/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            # GitHub returns 204 No Content on success.
            if resp.status not in (200, 201, 204):
                raise WebhookError(f"GitHub dispatch HTTP {resp.status}", status=502)
    except urllib.error.HTTPError as exc:
        raise WebhookError(f"GitHub dispatch HTTP {exc.code}", status=502) from exc
    except urllib.error.URLError as exc:
        raise WebhookError(f"GitHub dispatch network error: {exc.reason}", status=502) from exc


def handle_post(
    *,
    raw_body: bytes,
    header_sig: str,
    environ: dict[str, str] | None = None,
    dry_run: bool | None = None,
    repo: str = DEFAULT_REPO,
) -> tuple[int, dict[str, Any]]:
    """Verify HMAC and notify GitHub. Returns (status, JSON body)."""
    env = environ if environ is not None else dict(os.environ)
    secret = require_vercel_secret(env)
    event = parse_verified_event(secret=secret, raw_body=raw_body, header_sig=header_sig)
    client_payload = redact_client_payload(event)
    token = github_token(env)
    do_dry = dry_run if dry_run is not None else env.get("WEBHOOK_DRY_RUN", "") in (
        "1",
        "true",
        "True",
    )
    if do_dry or not token:
        return 200, {
            "ok": True,
            "notified": False,
            "dryRun": True,
            "client_payload": client_payload,
            "hint": "set GITHUB_TOKEN or GH_APP_INSTALLATION_TOKEN to fire repository_dispatch",
        }
    fire_repository_dispatch(client_payload, token=token, repo=repo)
    return 200, {"ok": True, "notified": True, "client_payload": client_payload}
