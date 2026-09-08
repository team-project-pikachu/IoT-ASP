# Vercel webhooks — hop-ultrasonic deploy notifications

Issue: [#37](https://github.com/team-project-pikachu/IoT-ASP/issues/37) · Related continuous ship:
[#27](https://github.com/team-project-pikachu/IoT-ASP/issues/27) · Deploy ownership:
[`docs/deploy.md`](deploy.md)

**Deploy Hooks** (`VERCEL_DEPLOY_HOOK_PROD`, issue #27) *trigger* a Vercel build. **Webhooks** are the
opposite direction: Vercel POSTs lifecycle events *to you* so GitHub / Slack / a receiver can notify
without inventing secrets in git.

Project settings (create UI):
<https://vercel.com/1digital-design/hop-ultrasonic/settings/webhooks>

Team/account webhooks (same events, broader scope): Settings → Webhooks on team `1digital-design`.

## Events to subscribe (hop-ultrasonic)

Prefer these deployment events (API `type` strings):

| UI label (approx.) | `type` | Why |
|--------------------|--------|-----|
| Deployment Created | `deployment.created` | new deploy started |
| Deployment Succeeded | `deployment.succeeded` | preview/prod ready |
| Deployment Error | `deployment.error` | fail path / paging |
| Deployment Cancelled | `deployment.canceled` | aborted deploys |
| Deployment Promoted | `deployment.promoted` | promote to production |
| Deployment Rollback | `deployment.rollback` | instant rollback accepted |

Scope the webhook to project **`hop-ultrasonic`** (team `1digital-design`) so other team projects do
not fan into this repo. Prod URL for smoke context:
`https://hop-ultrasonic-1digital-design.vercel.app`.

Envelope shape (all events): `{ "id", "type", "createdAt", "payload", ... }` — see
[Webhooks API](https://vercel.com/docs/webhooks/webhooks-api).

## (a) Create in the Vercel UI

1. Open <https://vercel.com/1digital-design/hop-ultrasonic/settings/webhooks> (or team Settings →
   Webhooks).
2. Select the deployment events above.
3. Choose target project **`hop-ultrasonic`** (not “All Team Projects” unless you intend that).
4. Enter a public **HTTPS endpoint URL** (see wire-up options below). Localhost will not receive
   Vercel POSTs.
5. Create the webhook. The dialog shows a **secret once** — store it immediately; it is not shown
   again.

CLI alternative (account/team scoped where the CLI supports it):

```bash
vercel webhooks create https://example.com/vercel-webhook \
  --event deployment.created \
  --event deployment.succeeded \
  --event deployment.error
```

(Exact flags: `vercel webhooks --help`; pin events to the project in the dashboard if the CLI create
is team-wide.)

## (b) Secret hygiene — names only

| Name | 1Password reference | GitHub Actions secret |
|------|---------------------|------------------------|
| `VERCEL_WEBHOOK_SECRET` | `op://dev/VERCEL_WEBHOOK_SECRET/credential` | `VERCEL_WEBHOOK_SECRET` |

Never invent, paste, echo, or commit the value. Pipe into GitHub on stdin:

```bash
op read "op://dev/VERCEL_WEBHOOK_SECRET/credential" \
  | gh secret set VERCEL_WEBHOOK_SECRET --repo team-project-pikachu/IoT-ASP
```

Optional: add a line to `.github/secrets.op.env` (gitignored; see `.github/secrets.op.env.example`)
and run `scripts/op_secrets_to_gh.sh push` once the item exists in vault `dev`.

`scripts/vercel_secrets_check.sh` treats this name as **optional** (webhook path is independent of
the CLI deploy secrets in #27).

## (c) Verify `x-vercel-signature` (HMAC-SHA1)

Vercel signs the **raw request body** with HMAC-SHA1 using the webhook secret and sends the hex
digest in the `x-vercel-signature` header
([request headers](https://vercel.com/docs/headers/request-headers#x-vercel-signature)).

Local / CI stub (stdlib only):

```bash
# Compute expected signature for a captured body (never prints the secret):
export VERCEL_WEBHOOK_SECRET  # from op read / Actions secret — do not echo
python3 scripts/vercel_webhook_verify.py --body-file /tmp/vercel-event.json \
  --signature "$HEADER_FROM_REQUEST"
# exit 0 → OK; exit 1 → mismatch / missing; never logs the secret value
```

Rules for any receiver:

1. Read the **raw** body bytes before JSON parse (parsers that re-serialize break the HMAC).
2. `hmac.new(secret, raw_body, hashlib.sha1).hexdigest()` and compare with
   `hmac.compare_digest` (constant-time) to `x-vercel-signature`.
3. Reject with HTTP 403 on mismatch; do not log body + secret together.
4. Only then parse JSON and branch on `type`.

## (d) Wire-up options

GitHub Actions **cannot** expose a public HTTPS endpoint for Vercel to POST to. Use one of:

### 1. HTTPS receiver → `repository_dispatch` (recommended path)

1. Host a tiny HTTPS handler (Cloud Run, Cloudflare Worker, another Vercel project, etc.) that:
   - verifies HMAC with env **name** `VERCEL_WEBHOOK_SECRET`;
   - on success, calls GitHub
     [`repository_dispatch`](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)
     with `event_type: vercel-deployment` and a **redacted** `client_payload` (event `type`,
     deployment URL / id from `payload` — no secrets), authenticated with a **separate** GitHub
     credential (`GITHUB_TOKEN` fine-grained PAT or `GH_APP_INSTALLATION_TOKEN` — Contents write
     on this repo only; see receiver README). Never reuse `VERCEL_WEBHOOK_SECRET` for GitHub.
2. Workflow [`.github/workflows/vercel-webhook.yml`](../.github/workflows/vercel-webhook.yml)
   listens for that dispatch and writes a job summary (extend later: issue comment, Slack, check run).

Stub receiver sketch (not production-hosted here):
[`services/vercel-webhook-receiver/README.md`](../services/vercel-webhook-receiver/README.md).

### 2. Docs-only / manual verify

Until a public URL exists: create the webhook pointing at a temporary request-bin you control, run
`scripts/vercel_webhook_verify.py` against one captured POST, then rotate the secret into 1Password
and GitHub.

## Owner checklist

- [ ] Webhook created in Vercel UI for `hop-ultrasonic` with events above
- [ ] Secret stored as `op://dev/VERCEL_WEBHOOK_SECRET/credential` (not in chat/issues)
- [ ] `gh secret set VERCEL_WEBHOOK_SECRET` via stdin
- [ ] Receiver GitHub auth: `GITHUB_TOKEN` or `GH_APP_INSTALLATION_TOKEN` (Contents write on this
      repo only; separate from the Vercel webhook secret — see receiver README)
- [ ] Public HTTPS endpoint URL configured (or deferred with temporary bin for signature dry-run)
- [ ] Receiver verifies HMAC before any side effect
- [ ] `repository_dispatch` `vercel-deployment` exercised once (Actions run URL recorded in
      `.vv/deploy/VERCEL.md` — no secrets)
- [ ] Cross-check #27 CLI / Deploy Hook secrets still tracked separately

## Sources

- Vercel — *Setting Up Webhooks* <https://vercel.com/docs/webhooks>
- Vercel — *Webhooks API* (event `type` strings) <https://vercel.com/docs/webhooks/webhooks-api>
- Vercel — *x-vercel-signature* HMAC-SHA1 <https://vercel.com/docs/headers/request-headers>
- Context7 `/websites/vercel` — verify signature with `crypto.createHmac('sha1', secret)` +
  `timingSafeEqual` / compare_digest
- Repo continuous ship: `docs/deploy.md`, issue #27; this issue #37
