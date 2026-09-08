# Procedure — #61 live ingest + patch wiring

## V-61-A — Local dry ingest (no GCP)

```bash
python3 -m pytest tests/test_ingest_app.py tests/test_public_html.py -q
```

**Expected:** ingest dry-run + public HTML URL gates green (baked HTTPS, no `?` in constants).

## V-61-B — Container DRY_ROOT (regression)

`gcs_io._default_dry_root()` must not raise when package lives at `/app/iot_asp_autoroute`
(Cloud Run image). Covered by `tests/test_ingest_app.py`.

## V-61-C — Vercel public ingest (phone path)

1. Set Vercel project env (names only): `IOT_ASP_GCS_BUCKET`, `GCP_SA_JSON`.
2. Deploy so `POST /api/ingest` is live.
3. `curl -fsS -X POST https://hop-ultrasonic-1digital-design.vercel.app/api/ingest -H 'Content-Type: application/json' -d '{"schemaVersion":1,"deviceId":"node1","ts":"2026-09-08T00:00:00Z","seed":1,"algo":"hop","peakHz":19000,"suddenFreq":false,"holdManual":false,"absA":0.01,"micEnergy":-60,"band":"17-23k","power":"ac120"}'`
4. **Expected:** HTTP 200 + `gs://…/meta/telemetry/node1/…` (503 if env missing).

## V-61-D — Cloud Run twin (authenticated ops only)

```bash
bash scripts/deploy_ingest_cloudrun.sh
# allUsers invoker is blocked by org policy — do not expect phone sendBeacon to succeed here.
```

## V-61-E — Phone query / baked defaults

Open production (or `?telemetry=` / `?patch=` override). Confirm `#telemetryUrlLabel` ≠ `off`,
Hold freezes apply, Copy log JSON has no signed-URL secrets.

## V-61-F — Field note

Fill `.vv/61/field-note.md` (or issue comment) for 2× TX + optional node-3 — tracked with #62.
