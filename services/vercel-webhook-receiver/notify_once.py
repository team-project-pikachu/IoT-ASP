#!/usr/bin/env python3
"""CLI: verify a captured Vercel body and optionally fire repository_dispatch.

Wraps handler.handle_post for one-shot notify without a long-lived server.

  export VERCEL_WEBHOOK_SECRET   # from op read — do not echo
  # dry-run (default if no GitHub token):
  python3 services/vercel-webhook-receiver/notify_once.py \\
    --body-file /tmp/vercel-event.json --signature "$SIG"

  # live notify:
  export GITHUB_TOKEN=…   # Contents write on this repo only
  python3 services/vercel-webhook-receiver/notify_once.py \\
    --body-file /tmp/vercel-event.json --signature "$SIG" --live
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from handler import WebhookError, handle_post  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="One-shot Vercel webhook verify + notify")
    p.add_argument("--body-file", required=True, help="raw webhook body file")
    p.add_argument("--signature", required=True, help="x-vercel-signature hex")
    p.add_argument(
        "--live",
        action="store_true",
        help="require GitHub token and fire repository_dispatch (default: dry-run)",
    )
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPO", "team-project-pikachu/IoT-ASP"))
    args = p.parse_args(argv)

    try:
        raw = Path(args.body_file).read_bytes()
    except OSError as exc:
        print(f"FAIL: body file: {exc}", file=sys.stderr)
        return 1

    env = dict(os.environ)
    dry = not args.live
    if args.live:
        env.pop("WEBHOOK_DRY_RUN", None)
        if not (env.get("GITHUB_TOKEN") or env.get("GH_APP_INSTALLATION_TOKEN")):
            print(
                "FAIL: --live requires GITHUB_TOKEN or GH_APP_INSTALLATION_TOKEN "
                "(Contents write on this repo only)",
                file=sys.stderr,
            )
            return 1
    else:
        env["WEBHOOK_DRY_RUN"] = "1"

    try:
        status, body = handle_post(
            raw_body=raw,
            header_sig=args.signature.strip(),
            environ=env,
            dry_run=dry,
            repo=args.repo,
        )
    except WebhookError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(body, indent=2, sort_keys=True))
    if args.live and not body.get("notified"):
        print("FAIL: --live completed without notified=true", file=sys.stderr)
        return 1
    return 0 if status == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
