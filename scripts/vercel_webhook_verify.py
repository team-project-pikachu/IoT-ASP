#!/usr/bin/env python3
"""Verify a Vercel webhook signature (HMAC-SHA1 of raw body).

Never prints the secret. Exit 0 on match, 1 on mismatch / missing inputs, 2 on usage.

Env:
  VERCEL_WEBHOOK_SECRET  — required (value from 1Password / GitHub Actions; do not echo)

Usage:
  python3 scripts/vercel_webhook_verify.py --body-file PATH --signature HEX
  python3 scripts/vercel_webhook_verify.py --body-file PATH --signature-file PATH
  cat body.json | python3 scripts/vercel_webhook_verify.py --signature HEX

See docs/vercel-webhooks.md (issue #37).
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import sys


def _usage(msg: str | None = None) -> int:
    if msg:
        print(f"FAIL: {msg}", file=sys.stderr)
    print(
        "usage: vercel_webhook_verify.py (--body-file PATH | stdin) "
        "(--signature HEX | --signature-file PATH)",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--body-file", help="raw webhook body file (omit to read stdin)")
    p.add_argument("--signature", help="x-vercel-signature hex digest")
    p.add_argument("--signature-file", help="file containing the hex digest only")
    args = p.parse_args(argv)

    secret = os.environ.get("VERCEL_WEBHOOK_SECRET")
    if not secret:
        print(
            "FAIL: VERCEL_WEBHOOK_SECRET env name is unset "
            "(see docs/vercel-webhooks.md, op://dev/VERCEL_WEBHOOK_SECRET/credential)",
            file=sys.stderr,
        )
        return 1

    if args.signature and args.signature_file:
        return _usage("pass only one of --signature / --signature-file")
    if args.signature_file:
        try:
            with open(args.signature_file, "r", encoding="utf-8") as f:
                header_sig = f.read().strip()
        except OSError as e:
            print(f"FAIL: cannot read signature file: {e}", file=sys.stderr)
            return 1
    elif args.signature:
        header_sig = args.signature.strip()
    else:
        return _usage("missing --signature or --signature-file")

    if not header_sig:
        print("FAIL: empty signature", file=sys.stderr)
        return 1

    if args.body_file:
        try:
            with open(args.body_file, "rb") as f:
                raw = f.read()
        except OSError as e:
            print(f"FAIL: cannot read body file: {e}", file=sys.stderr)
            return 1
    else:
        if sys.stdin.isatty():
            return _usage("no --body-file and stdin is a TTY")
        raw = sys.stdin.buffer.read()

    expected = hmac.new(
        secret.encode("utf-8"),
        raw,
        hashlib.sha1,
    ).hexdigest()

    if not hmac.compare_digest(expected, header_sig):
        print("FAIL: signature mismatch (body or secret does not match)", file=sys.stderr)
        return 1

    print("OK vercel_webhook_verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
