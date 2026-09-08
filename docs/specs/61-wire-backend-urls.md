# #61 — Wire live backend URLs for 3-phone fleet

## Status (2026-09-08)

| Layer | State |
|-------|--------|
| PWA constants | Baked non-secret Vercel `BACKEND_PATCH_URL` + `BACKEND_TELEMETRY_URL` (`/api/ingest`) |
| Vercel ingest | `api/ingest.js` → GCS when `IOT_ASP_GCS_BUCKET` + `GCP_SA_JSON` set |
| Cloud Run twin | `iot-asp-ingest` Ready; **not** phone-public (`allUsers` blocked by org policy) |
| `gcs_io` container | `_default_dry_root()` survives `/app` shallow path (import 500 fixed) |
| Field 3-phone | Template `.vv/61/field-note.md` → close with #62 |

## Chosen override path (acceptance #1)

1. **Default:** `BACKEND_*` absolute HTTPS on production Vercel (no secrets, no `?` in constants).
2. **Override:** `?telemetry=` / `?patch=` / `?pollMs=` still win (query > constants).
3. Contract: `docs/api-contract.md`. Hold/Manual: `.vv/hot-apply.md`.

## Why not Cloud Run as phone target

`gcloud run services add-iam-policy-binding … --member=allUsers` → `FAILED_PRECONDITION`
(`iam.allowedPolicyMemberDomains`). Safari `sendBeacon` cannot attach Cloud Run ID tokens, so
phones use the public Vercel `/api/ingest` proxy.

## Acceptance mapping

| AC | How |
|----|-----|
| Document override path | This spec + `docs/adk-autoroute.md` + `.vv/61/WIRING.md` |
| Beacon → GCS | `/api/ingest` after Vercel env set |
| Patch ≤5 s + Hold freeze | Existing PWA poll/apply (unchanged) |
| No secrets in payload | Existing redaction e2e + ingest scrub |
| 3-phone field note | `.vv/61/field-note.md` (filled under #62) |

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/61
- `.vv/61/WIRING.md`
