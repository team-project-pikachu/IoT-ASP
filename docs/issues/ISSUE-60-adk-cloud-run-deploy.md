# ISSUE-60 — ADK Cloud Run / Agent Engine deploy

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/60  
**Classification:** owner-gated deploy (Balanced PR8 dry-check)  
**Status:** package dry-check script — **no live Cloud Run / Agent Engine claim**

## Did

- Mapped under M6 in `docs/mvp-roadmap.md`
- Local dry-run remains `bash scripts/autoroute_dev.sh`
- PR8: `bash scripts/adk_deploy_dry_check.sh` (layout + docs + names-only env presence)

## Didn't

- Provision Cloud Run / Agent Engine
- Invent GCP project IDs or SA JSON in git
- Call `gcloud` / `adk deploy` from this agent

## Next

- Owner: choose Cloud Run vs Agent Engine; set names-only secrets; deploy from `docs/adk-autoroute.md`
- Then unblock `#61` live patch/telemetry URLs
