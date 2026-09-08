# Vercel webhook receiver stub (HMAC verify → optional repository_dispatch)

Not a hosted service in this repo. Use this sketch when standing up a public HTTPS
endpoint for `hop-ultrasonic` webhooks.

Docs: [`docs/vercel-webhooks.md`](../../docs/vercel-webhooks.md) · Issue #37

## Contract

1. Env **name** `VERCEL_WEBHOOK_SECRET` (value from `op://dev/VERCEL_WEBHOOK_SECRET/credential`
   or GitHub Actions secret of the same name). Never invent or commit the value.
2. On `POST /`:
   - Read **raw** body bytes.
   - Compute HMAC-SHA1 hex; compare to `x-vercel-signature` with constant-time compare.
   - On mismatch → HTTP 403; do not log the secret.
   - On match → parse JSON; read `type` / deployment URL from `payload`; optionally fire
     GitHub `repository_dispatch` `event_type=vercel-deployment` (see
     `.github/workflows/vercel-webhook.yml`).
3. Local signature check without a server:
   `python3 scripts/vercel_webhook_verify.py --body-file … --signature …`

## Minimal stdlib sketch (illustrative)

```python
# sketch only — host elsewhere; wire VERCEL_WEBHOOK_SECRET from the environment
import hashlib, hmac, json, os
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRET = os.environ["VERCEL_WEBHOOK_SECRET"]  # fail closed if unset

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n)
        sig = self.headers.get("x-vercel-signature", "")
        expect = hmac.new(SECRET.encode(), raw, hashlib.sha1).hexdigest()
        if not hmac.compare_digest(expect, sig):
            self.send_response(403); self.end_headers(); return
        event = json.loads(raw)
        # side effects: repository_dispatch with redacted client_payload only
        _ = event.get("type")
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true}')

# HTTPServer(("0.0.0.0", 8080), H).serve_forever()  # terminate TLS at the edge
```

Prefer a managed HTTPS front (Cloud Run / Worker / separate Vercel project) over exposing
plain HTTP. Pair with the Actions workflow named **Vercel webhook notify**.
