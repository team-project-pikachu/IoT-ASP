# Field note — #61 three-phone fleet (template)

**Date:** YYYY-MM-DD  
**Operator:**  
**Vercel base:** `https://hop-ultrasonic-1digital-design.vercel.app/`  
**Telemetry:** `https://hop-ultrasonic-1digital-design.vercel.app/api/ingest`  
**Patch:** `https://hop-ultrasonic-1digital-design.vercel.app/patch.json`  

| Phone | Role | `deviceId` (from UI) | Query override? | Beacon ok? | Patch hot-apply ≤5s? | Hold freezes apply? |
|-------|------|---------------------|-----------------|------------|----------------------|---------------------|
| 1 | TX | | baked / `?…` | | | |
| 2 | TX | | baked / `?…` | | | |
| 3 | optional | | baked / `?…` | | | |

**GCS spot-check:** `gcloud storage ls gs://$IOT_ASP_GCS_BUCKET/meta/telemetry/<deviceId>/`  
**Notes / blockers:** Vercel env `GCP_SA_JSON` + `IOT_ASP_GCS_BUCKET` required for 200 (else 503).
