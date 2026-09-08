# #61 — Wire live backend URLs (3-phone fleet)

## Status (2026-09-08)

- **PWA:** `?patch=` / `?telemetry=` / `?pollMs=` + empty `BACKEND_*` constants already on `main` (PR #73 UI label).
- **Ingest packaging:** `services/autoroute-adk/ingest_app.py` + `Dockerfile` + `scripts/deploy_ingest_cloudrun.sh`.
- **Live service:** `https://iot-asp-ingest-eehtcwqbzq-uc.a.run.app` exists (image tag `:61`) but was **not** phone-ready:
  1. IAM invoker = `betty@bearresearch.io` only → unauthenticated `sendBeacon` **403**.
  2. `gcs_io.DRY_ROOT` used `parents[3]` → **500** on import inside `/app` container (fixed in this branch).

## Goal

Point the shipped blaster at a real ingest + patch surface so three phones beacon and hot-apply **without** embedding Vertex/ADK keys.

## Chosen override path (acceptance #1)

| Priority | Mechanism | Notes |
|----------|-----------|--------|
| 1 | Query `?telemetry=` + `?patch=` (+ optional `?pollMs=`) | Field fleet preferred — no Vercel redeploy |
| 2 | `BACKEND_BASE_URL` / `BACKEND_PATCH_URL` / `BACKEND_TELEMETRY_URL` in `public/index.html` | Optional bake of **non-secret** HTTPS hosts after stable; keep empty until IAM + health green |

Contract: `docs/api-contract.md`. Hot-apply / Hold: `.vv/hot-apply.md`.

## Deploy + verify (owner / integrator)

```bash
# From IoT-ASP checkout (ADC + project bear-iot-asp-rec)
bash scripts/deploy_ingest_cloudrun.sh
# Expect TELEMETRY_URL=…/ingest PATCH_URL=…/patch.json and healthz HTTP 200
# Script warns if allUsers run.invoker is missing.

# Phone URLs (example — use printed INGEST_URL):
# https://hop-ultrasonic.vercel.app/?telemetry=https://iot-asp-ingest-….run.app/ingest&patch=https://iot-asp-ingest-….run.app/patch.json&pollMs=3000
```

Do **not** open a separate PR for this shard; fold into the combined M0 MVP PR with #62.

## Field note (acceptance #5)

Record in `.vv/61/field-note.md` (template below) or as an issue comment after 3-phone run:

- 2× TX + optional node-3
- Query URL used (redact any signed query strings if present)
- Confirm Hold/Manual freezes apply; heartbeats land under `gs://…/meta/telemetry/<deviceId>/`

## Out of scope

- Service worker / offline cache of `index.html`
- Native iOS ingest (#41)
- Enrichment schema (#22)
- Sonos / #62 field Playwright promotion (sibling shards)
