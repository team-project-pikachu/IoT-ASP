# ISSUE-61 — Wire live BACKEND_TELEMETRY_URL + patch URL

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/61  
**Classification:** M0 ship — public URL wiring  
**Status:** Wired to Vercel production absolute URLs + `/api/ingest` proxy (2026-09-08)

## Did

- Bake non-secret public constants in `public/index.html`:
  - `BACKEND_PATCH_URL` → production `/patch.json`
  - `BACKEND_TELEMETRY_URL` → production `/api/ingest`
- Add `api/ingest.js` (CORS + GCS write when `IOT_ASP_GCS_BUCKET` + `GCP_SA_JSON` set)
- Deploy authenticated Cloud Run twin `iot-asp-ingest` (`services/autoroute-adk/Dockerfile`)
- Document org-policy blocker: `allUsers` / `allAuthenticatedUsers` invoker refused on `bear-iot-asp-rec`
- Fleet notes in `public/README.txt`; evidence under `.vv/61/`

## Didn't / residual

- Full ADK autoroute author loop (#60) — ingest is write-only (`IOT_ASP_AUTOROUTE_ON_INGEST=0`)
- Vercel env `GCP_SA_JSON` / `IOT_ASP_GCS_BUCKET` may still need owner set for live GCS (else 503)
- Field checklist on three phones remains #62

## Next

1. Owner: set Vercel project env names above (1Password → Vercel; no git)
2. Redeploy Vercel so `/api/ingest` is live on production
3. Field-verify beacons → GCS; then #62
