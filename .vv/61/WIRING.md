# .vv/61 — Wire live backend URLs (2026-09-08)

## Subject

GitHub #61 — public hop ultrasonic / IoT-ASP M0 blaster ↔ live telemetry + patch URLs.

## Configuration

| Item | Value |
|------|-------|
| Patch URL (baked) | `https://hop-ultrasonic-1digital-design.vercel.app/patch.json` |
| Telemetry URL (baked) | `https://hop-ultrasonic-1digital-design.vercel.app/api/ingest` |
| Cloud Run service | `iot-asp-ingest` @ `us-central1` / `bear-iot-asp-rec` |
| Cloud Run URL | `https://iot-asp-ingest-eehtcwqbzq-uc.a.run.app` |
| Public invoker | **blocked** by org policy `iam.allowedPolicyMemberDomains` (customer `C02ljt6z8`) |
| Fleet bucket (runtime env name) | `IOT_ASP_GCS_BUCKET` (value not recorded here) |

## Evidence

1. Local Flask dry-run of `ingest_app.py`: healthz 200, POST /ingest → dry file URI, GET /patch.json 200.
2. Docker image `…/iot-asp-ingest:61` built (linux/amd64) and pushed to Artifact Registry; Cloud Run revision `iot-asp-ingest-00001-n6x` Ready.
3. `gcloud run services add-iam-policy-binding … allUsers` → `FAILED_PRECONDITION` (org policy) — public phones therefore use Vercel `/api/ingest`.
4. Offline gates: `pytest tests/test_public_html.py` (this PR).

## Residual

- Production GCS writes require Vercel env `GCP_SA_JSON` + `IOT_ASP_GCS_BUCKET`.
- Three-phone field note → #62.
- Full ADK patch author on ingest → #60.
