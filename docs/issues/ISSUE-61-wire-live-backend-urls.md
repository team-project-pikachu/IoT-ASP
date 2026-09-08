# #61 — Wire live telemetry + patch URLs

Tracking: https://github.com/team-project-pikachu/IoT-ASP/issues/61
See `docs/mvp-roadmap.md` for MVP pillar mapping.
# ISSUE-61 — Wire live BACKEND_TELEMETRY_URL + patch URL
**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/61  
**Classification:** ship polish (names + query overrides); **live HTTPS endpoints owner-gated**  
**Status:** PWA already supports offline defaults + `?patch=` / `?telemetry=` / `?pollMs=` (stack PR6 UI label)
## Did
- Documented constants in `public/index.html`:
  - `BACKEND_BASE_URL` / `BACKEND_PATCH_URL` / `BACKEND_TELEMETRY_URL` (empty = offline / static mock)
  - Query overrides: `?patch=` · `?telemetry=` · `?pollMs=`
- UI shows **patch** + **telemetry** URL labels (telemetry `off` when empty) — no secrets embedded
- Tests: `tests/test_public_html.py` asserts `telemetryUrlLabel` + query override comments
## Didn't
- Hard-code a production Cloud Run / ingest host
- Claim 3-phone live beacon path works end-to-end
## Next
1. Owner publishes HTTPS ingest + patch after `#60`
2. Field verify with `?telemetry=https://…/ingest&patch=https://…/patch.json` on three phones
3. Optional: bake non-secret public URLs into constants once stable (still no keys)
