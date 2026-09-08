# Vercel webhook receiver stub (HMAC verify → optional repository_dispatch)

Not a hosted service in this repo. Use this sketch when standing up a public HTTPS
endpoint for `hop-ultrasonic` webhooks.

Docs: [`docs/vercel-webhooks.md`](../../docs/vercel-webhooks.md) · Issue #37

## Contract

1. Env **name** `VERCEL_WEBHOOK_SECRET` (value from `op://dev/VERCEL_WEBHOOK_SECRET/credential`
   or GitHub Actions secret of the same name). Authenticates **Vercel → receiver** only.
   Never invent or commit the value.
2. Env **name** for GitHub auth when firing `repository_dispatch` (pick one; names only):
   | Secret name | Source | Least privilege |
   |-------------|--------|-----------------|
   | `GITHUB_TOKEN` | Fine-grained PAT or classic PAT on the receiver host | Contents: **Read and write** on `team-project-pikachu/IoT-ASP` only (required for [`repository_dispatch`](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)); no other repos |
   | `GH_APP_INSTALLATION_TOKEN` | Short-lived GitHub App installation token | Same Contents write on this repo; prefer App over long-lived PAT |
   Store via 1Password references such as `op://dev/GITHUB_DISPATCH_TOKEN/credential` (or your App
   private-key item) and inject at deploy time — never commit values. Do **not** reuse
   `VERCEL_WEBHOOK_SECRET` for GitHub; do **not** put either secret in `client_payload`.
3. On `POST /`:
   - Read **raw** body bytes.
   - Compute HMAC-SHA1 hex; compare to `x-vercel-signature` with constant-time compare.
   - On mismatch → HTTP 403; do not log the secret.
   - On match → parse JSON; read `type` / deployment URL from `payload`; optionally fire
     GitHub `repository_dispatch` `event_type=vercel-deployment` with the GitHub token above
     (see `.github/workflows/vercel-webhook.yml`).
4. Local signature check without a server:
   `python3 scripts/vercel_webhook_verify.py --body-file … --signature …`

## Minimal stdlib sketch (illustrative)

```python
# sketch only — host elsewhere; wire secrets from the environment (names only)
import hashlib, hmac, json, os, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRET = os.environ["VERCEL_WEBHOOK_SECRET"]  # fail closed if unset
# PAT or App installation token — Contents write on this repo only
GH_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ["GH_APP_INSTALLATION_TOKEN"]

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
        payload = json.dumps({
            "event_type": "vercel-deployment",
            "client_payload": {
                "type": event.get("type"),
                "url": (event.get("payload") or {}).get("url") or "",
                "id": event.get("id") or "",
            },
        }).encode()
        req = urllib.request.Request(
            "https://api.github.com/repos/team-project-pikachu/IoT-ASP/dispatches",
            data=payload,
            headers={
                "Authorization": f"Bearer {GH_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            method="POST",
        )
        urllib.request.urlopen(req)  # production: handle errors; never log tokens
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true}')

# HTTPServer(("0.0.0.0", 8080), H).serve_forever()  # terminate TLS at the edge
```

Prefer a managed HTTPS front (Cloud Run / Worker / separate Vercel project) over exposing
plain HTTP. Pair with the Actions workflow named **Vercel webhook notify**.
