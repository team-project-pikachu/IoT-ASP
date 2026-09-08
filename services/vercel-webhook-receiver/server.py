#!/usr/bin/env python3
"""HTTP entry for Vercel webhook notify (HMAC → repository_dispatch).

Usage:
  WEBHOOK_DRY_RUN=1 VERCEL_WEBHOOK_SECRET=… \\
    python3 services/vercel-webhook-receiver/server.py --bind 127.0.0.1 --port 8080
  # or from this directory: python3 server.py --bind 127.0.0.1 --port 8080

Env names only (never commit values):
  VERCEL_WEBHOOK_SECRET          required — Vercel → receiver HMAC
  GITHUB_TOKEN | GH_APP_INSTALLATION_TOKEN  optional — fire repository_dispatch
  WEBHOOK_DRY_RUN=1              skip GitHub call; return redacted payload
  GITHUB_REPO                    default team-project-pikachu/IoT-ASP

Terminate TLS at the edge (Cloud Run / Caddy / Cloudflare). Pair with
.github/workflows/vercel-webhook.yml (event_type=vercel-deployment).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# Allow `python3 -m` from services/ or repo root.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from handler import DEFAULT_REPO, WebhookError, handle_post  # noqa: E402


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "iot-asp-vercel-webhook/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        # Avoid logging bodies or Authorization; path + status only.
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] in ("/", "/healthz", "/health"):
            self._json(200, {"ok": True, "service": "vercel-webhook-receiver"})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in ("/", "/vercel-webhook", "/webhook"):
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"ok": False, "error": "bad Content-Length"})
            return
        if length < 0 or length > 1_000_000:
            self._json(413, {"ok": False, "error": "body too large"})
            return
        raw = self.rfile.read(length)
        sig = self.headers.get("x-vercel-signature", "") or ""
        repo = os.environ.get("GITHUB_REPO", DEFAULT_REPO)
        try:
            status, body = handle_post(raw_body=raw, header_sig=sig, repo=repo)
        except WebhookError as exc:
            self._json(exc.status, {"ok": False, "error": str(exc)})
            return
        self._json(status, body)

    def _json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Vercel webhook receiver (notify GitHub)")
    p.add_argument("--bind", default=os.environ.get("WEBHOOK_BIND", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("WEBHOOK_PORT", "8080")))
    args = p.parse_args(argv)
    # Fail closed early if secret missing (unless dry health-only — still require for POST).
    if not os.environ.get("VERCEL_WEBHOOK_SECRET"):
        print(
            "FAIL: set VERCEL_WEBHOOK_SECRET before listen "
            "(op://dev/VERCEL_WEBHOOK_SECRET/credential)",
            file=sys.stderr,
        )
        return 1
    httpd = ThreadingHTTPServer((args.bind, args.port), WebhookHandler)
    print(
        f"OK vercel-webhook-receiver listening on http://{args.bind}:{args.port}/ "
        f"(dry_run={os.environ.get('WEBHOOK_DRY_RUN', '')!r})",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutdown", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
