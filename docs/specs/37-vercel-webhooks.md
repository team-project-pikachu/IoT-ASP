# Spec: Vercel webhooks — hop-ultrasonic deploy notifications

Issue: [#37](https://github.com/team-project-pikachu/IoT-ASP/issues/37)  
Board: [Project 5](https://github.com/orgs/team-project-pikachu/projects/5)  
Related: [#27](https://github.com/team-project-pikachu/IoT-ASP/issues/27) continuous ship

## Status

Receiver + Actions notify path **implemented in-repo**. Hosting the public HTTPS
endpoint and storing `VERCEL_WEBHOOK_SECRET` remain **owner-gated**.

## Goal

Vercel POSTs deploy lifecycle events to a public HTTPS receiver that:

1. Verifies `x-vercel-signature` (HMAC-SHA1 of **raw** body).
2. Fires GitHub `repository_dispatch` `event_type=vercel-deployment` with a
   **redacted** `client_payload` (`type`, `url`, `id` — no secrets).
3. Triggers `.github/workflows/vercel-webhook.yml` to write a job summary and
   best-effort comment on #37.

## Prior art

- Vercel Webhooks docs + `x-vercel-signature` HMAC-SHA1
- Repo `scripts/vercel_webhook_verify.py` (signature-only stub from #38)
- Continuous ship Deploy Hooks (#27) — opposite direction (GitHub → Vercel)

## Shipped on this branch

- `services/vercel-webhook-receiver/handler.py` — verify + redact + dispatch
- `server.py` / `notify_once.py` — HTTP listen / one-shot CLI
- `.github/workflows/vercel-webhook.yml` — summary + #37 comment
- Offline tests: `tests/test_vercel_webhook.py`, `tests/test_vercel_webhook_receiver.py`

## Remaining scope (owner)

- Create webhook in Vercel UI for `hop-ultrasonic`
- Store `op://dev/VERCEL_WEBHOOK_SECRET/credential` → `gh secret set`
- Host receiver behind public HTTPS; set `GITHUB_TOKEN` / App token on host

## Wire fields

None (ops notification only; no `schemaVersion` / telemetry change).

## Clamps / safety

- Fail closed on missing secret / signature mismatch (HTTP 403)
- Never log secret values; never put secrets in `client_payload`
- Separate Vercel HMAC secret from GitHub dispatch token

## Acceptance tests

| ID | Check |
|----|-------|
| VW-01 | `vercel_webhook_verify.py` match/mismatch offline |
| VW-02 | `notify_once.py` dry-run returns `ok` + `notified: false` |
| VW-03 | `--live` without GitHub token exits non-zero |
| VW-04 | Scheme-less `deployment.url` hostnames normalize to `https://` |
| VW-05 | Workflow listens for `repository_dispatch` `vercel-deployment` |

## CI gate

`python3 -m pytest tests/test_vercel_webhook.py tests/test_vercel_webhook_receiver.py -q`

## Risks / HW limits

- Actions cannot expose a public HTTPS endpoint — receiver must be hosted
- Secret shown once in Vercel UI — rotate via 1Password if lost

## Sources

- [`docs/vercel-webhooks.md`](../vercel-webhooks.md)
- <https://vercel.com/docs/webhooks>
- <https://vercel.com/docs/headers/request-headers#x-vercel-signature>
