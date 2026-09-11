# #122 Hosted Vercel webhook HTTPS receiver — status (2026-09-11)

## Summary

Issue #122 noted `services/vercel-webhook-receiver/` as README-only. On current `main` the product code is already present:

| Path | Role |
|------|------|
| `services/vercel-webhook-receiver/handler.py` | HMAC-SHA1 verify (`x-vercel-signature`), redact public payload fields, optional `repository_dispatch` `vercel-deployment` |
| `services/vercel-webhook-receiver/server.py` | Threading HTTPServer (`WEBHOOK_BIND`/`WEBHOOK_PORT`) |
| `services/vercel-webhook-receiver/notify_once.py` | One-shot CLI |
| `services/vercel-webhook-receiver/__main__.py` | Entry |
| `services/vercel-webhook-receiver/README.md` | Contract, env **names** only, dry-run path |

Related parent #37 (closed) delivered the notify path; this issue tracks the **hosted public HTTPS** residual.

## Acceptance residual (owner-gated)

1. **Deploy** behind TLS (Cloud Run / Worker / separate Vercel project) — requires live `VERCEL_WEBHOOK_SECRET` and GitHub token **values** from 1Password / Actions secrets. Not inventable in-repo.
2. Point Vercel webhook URL at `https://<host>/vercel-webhook` (aliases `/`, `/webhook`).
3. Smoke: signed POST → 200; bad sig → 403 (covered by existing tests once secret is present locally).

## Invariants preserved

- No secret **values** in git or this evidence file (names only: `VERCEL_WEBHOOK_SECRET`, `GITHUB_TOKEN` / `GH_APP_INSTALLATION_TOKEN`).
- `WEBHOOK_DRY_RUN=1` path does not call GitHub.
- No wire/schema change; no `schemaVersion` bump; `vol_hard_max=100` and Hold/Manual untouched.
- No keys in `public/`.

## Out of scope for this closeout

- Applying live deploy credentials (#27 continuous ship secrets).
- Mutating branch-protection or inventing hardware results.

## Verified paths (main tip at branch create)

- `services/vercel-webhook-receiver/{handler,server,notify_once,__main__}.py`
- `docs/vercel-webhooks.md` (cross-link expected)
- Tests referenced in README: `tests/test_vercel_webhook_receiver.py`, `tests/test_vercel_webhook.py`
