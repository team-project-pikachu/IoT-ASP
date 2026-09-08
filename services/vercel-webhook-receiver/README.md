# Vercel webhook receiver — HMAC verify → GitHub notify

stdlib Python receiver for **hop-ultrasonic** deploy webhooks. Verifies
`x-vercel-signature`, then fires `repository_dispatch` `vercel-deployment` so
[`.github/workflows/vercel-webhook.yml`](../../.github/workflows/vercel-webhook.yml)
writes a job summary (the “notify”).

Docs: [`docs/vercel-webhooks.md`](../../docs/vercel-webhooks.md) · Issue #37 · related #27

## Contract

| Env **name** | Required | Role |
|--------------|----------|------|
| `VERCEL_WEBHOOK_SECRET` | yes | HMAC secret from Vercel webhook create dialog → `op://dev/VERCEL_WEBHOOK_SECRET/credential` |
| `GITHUB_TOKEN` **or** `GH_APP_INSTALLATION_TOKEN` | for live notify | Contents **Read and write** on `team-project-pikachu/IoT-ASP` only (`repository_dispatch`) |
| `WEBHOOK_DRY_RUN=1` | optional | Verify + redact payload; **do not** call GitHub |
| `GITHUB_REPO` | optional | default `team-project-pikachu/IoT-ASP` |
| `WEBHOOK_BIND` / `WEBHOOK_PORT` | optional | default `127.0.0.1:8080` |

Never invent, echo, or commit secret **values**. Do not reuse `VERCEL_WEBHOOK_SECRET` as the GitHub token. Do not put secrets in `client_payload`.

## Run locally (dry-run)

```bash
cd services/vercel-webhook-receiver
export VERCEL_WEBHOOK_SECRET   # from: op read "op://dev/VERCEL_WEBHOOK_SECRET/credential"
export WEBHOOK_DRY_RUN=1
python3 server.py --bind 127.0.0.1 --port 8080
# POST http://127.0.0.1:8080/ with raw body + x-vercel-signature
```

One-shot against a captured POST (no server):

```bash
python3 notify_once.py --body-file /tmp/vercel-event.json --signature "$SIG"
# live:
# export GITHUB_TOKEN=…   # Contents write on this repo only
# python3 notify_once.py --body-file /tmp/vercel-event.json --signature "$SIG" --live
```

Signature-only check (existing stub):

```bash
python3 ../../scripts/vercel_webhook_verify.py --body-file /tmp/vercel-event.json --signature "$SIG"
```

## Host (public HTTPS)

Terminate TLS at the edge (Cloud Run, Cloudflare, Caddy, or a separate Vercel project). Point the
Vercel webhook URL at `https://<host>/vercel-webhook` (aliases: `/`, `/webhook`).

Vercel UI: <https://vercel.com/1digital-design/hop-ultrasonic/settings/webhooks>

## Files

| Path | Role |
|------|------|
| `handler.py` | verify + redact + `repository_dispatch` |
| `server.py` / `__main__.py` | Threading HTTP server |
| `notify_once.py` | one-shot CLI |
| `README.md` | this file |

## Tests

```bash
python3 -m pytest tests/test_vercel_webhook_receiver.py tests/test_vercel_webhook.py -q
```
