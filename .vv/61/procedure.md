# Procedure — #61 live ingest + patch wiring

## V-61-A — Local dry ingest (no GCP)

```bash
cd "$(git rev-parse --show-toplevel)"
python3 -m pytest tests/test_ingest_app.py tests/test_public_html.py -q
```

**Expected:** all pass.

## V-61-B — Public phone path (Vercel)

Baked defaults in `public/index.html` point at production Vercel patch + `/api/ingest`.
Set project env **names** `IOT_ASP_GCS_BUCKET` + `GCP_SA_JSON` (values never in git), redeploy Vercel.

```bash
curl -fsS -X POST https://hop-ultrasonic-1digital-design.vercel.app/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"schemaVersion":1,"deviceId":"node1","ts":"2026-09-08T00:00:00Z","algo":"hop","peakHz":19000,"holdManual":false}'
```

**Expected:** HTTP 200 + GCS object; or HTTP 503 until env is set.

## V-61-C — Cloud Run twin (authenticated / ADK)

```bash
bash scripts/deploy_ingest_cloudrun.sh
```

Org policy blocks `allUsers` invoker — do not expect public Safari access to `*.run.app`.

## V-61-D — Field (3 phones)

Open live Vercel URL on 2× TX + optional node-3; confirm `#telemetryUrlLabel` is not `off`; Hold/Manual freezes apply; Copy log JSON has no secrets.

## V-61-E — No secrets in HTML

```bash
bash scripts/ci_static_gates.sh
```
