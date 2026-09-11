# #60 — ADK autoroute production deploy — status evidence

Worker: iot-asp-issue-queue-drain  
Date: 2026-09-11  
Main SHA at branch cut: `dab7afb1b0c3afcebe34380c8c55196ebcaa3576`

## What is already on `main`

| Path | Role |
|------|------|
| `services/autoroute-adk/` | Full ADK package: `iot_asp_autoroute/agent.py` (`root_agent`), tools, clamps, dry_run, fleet_log, nest stubs, vendored `algo_timestore` |
| `services/autoroute-adk/ingest_main.py` | Optional HTTP ingest entry for Cloud Run / CF |
| `services/autoroute-adk/requirements.txt` | Runtime deps (no secret values) |
| `docs/adk-autoroute.md` | Deploy commands for Agent Engine / Cloud Run; independent of Vercel |
| `docs/api-contract.md` | `schemaVersion: 1` patch/telemetry contract (unchanged) |
| `scripts/autoroute_dev.sh` | Local dry-run (no GCP, no keys) |
| `adk_agent/` | Compatibility shim (PR #190) re-exporting `root_agent` |

Service code and dry-run path exist. Production deploy URL is **not** the fleet default.

## Residual (owner-gated)

- GCP project `bear-iot-asp-rec` billing / IAM / ADC for the deploy identity
- `adk deploy agent_engine` **or** `adk deploy cloud_run` for `services/autoroute-adk/iot_asp_autoroute`
- Optional ingest Cloud Run/CF with `IOT_ASP_GCS_BUCKET` + runtime SA
- Documented base URL for phones (`?patch=` / `?telemetry=` or `BACKEND_*`)
- Live smoke that schemaVersion-1 patch JSON round-trips (no invented URLs or secrets in this evidence)

## Invariants preserved

- `vol_hard_max=100` (clamps.py)
- Hold / Manual freeze remote patch apply
- No API keys / Gemini credentials in `public/`
- No wire/schema change; no `schemaVersion` bump
- No secret VALUES in git

## Out of scope for this PR

- Live Cloud Run / Agent Engine deploy (owner)
- Vercel Actions secrets (#27)
- Live GCS credentials (#26)
- Hardware / on-device results

## Acceptance mapping

| Spec item | State |
|-----------|--------|
| Service code under `services/autoroute-adk/` | **Done on main** |
| Local `bash scripts/autoroute_dev.sh` remains green | **Done** (CI `autoroute` job) |
| Deployed service returns schemaVersion-1 patch JSON | **Owner residual** |
| Documented base URL for fleet | **Owner residual** |

This PR closes the docs/evidence slice only. Live deploy remains owner-gated.
