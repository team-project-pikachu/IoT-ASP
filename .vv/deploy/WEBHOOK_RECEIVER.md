# Vercel webhook receiver — evidence (issue #37)

**Config item:** `services/vercel-webhook-receiver/` + `.github/workflows/vercel-webhook.yml`  
**Docs:** `docs/vercel-webhooks.md`, `docs/specs/37-vercel-webhooks.md`  
**Date:** 2026-09-08 (UTC)  
**Git revision:** `feat/37-vercel-webhook-receiver` (see PR #59)  
**Status:** offline gates **PASS**; public HTTPS host + secrets **PENDING** (owner)

## Procedure

```bash
cd "$(git rev-parse --show-toplevel)"
python3 -m pytest tests/test_vercel_webhook.py tests/test_vercel_webhook_receiver.py -q
# Dry-run one-shot (dummy secret — never a real value in evidence):
SECRET=test-webhook-secret-not-real
BODY='{"type":"deployment.succeeded","id":"evt_demo","payload":{"deployment":{"url":"hop-ultrasonic-1digital-design.vercel.app"}}}'
TMP=$(mktemp); printf '%s' "$BODY" > "$TMP"
SIG=$(python3 -c "import hmac,hashlib; print(hmac.new(b'$SECRET', open('$TMP','rb').read(), hashlib.sha1).hexdigest())")
VERCEL_WEBHOOK_SECRET=$SECRET python3 services/vercel-webhook-receiver/notify_once.py \
  --body-file "$TMP" --signature "$SIG"; echo exit:$?
rm -f "$TMP"
```

## Observed results (2026-09-08)

| Step | Exit | Notes |
|------|------|-------|
| pytest webhook suites | **0** | match/mismatch, dry-run, live mock dispatch, `--live` without token fails |
| `notify_once.py` dry-run | **0** | `ok: true`, `notified: false`, URL normalized to `https://…` |

## Pass/fail

| Item | Status |
|------|--------|
| HMAC verify + redacted dispatch payload (offline) | **PASS** |
| Workflow YAML: `repository_dispatch` `vercel-deployment` + summary | **PASS** (structure tests) |
| Vercel UI webhook + `VERCEL_WEBHOOK_SECRET` in 1Password/GitHub | **PENDING** owner |
| Public HTTPS host for receiver | **PENDING** owner |

Secret **values** are never recorded here — names only (`VERCEL_WEBHOOK_SECRET`, `GITHUB_TOKEN` / `GH_APP_INSTALLATION_TOKEN`).
