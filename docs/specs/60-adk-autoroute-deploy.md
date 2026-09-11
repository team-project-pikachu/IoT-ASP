# #60 — ADK autoroute production deploy

## Status

**Done on main** for service code + dry-run path. Live GCP deploy remains **owner-gated**.

Evidence: `.vv/60/adk-autoroute-deploy-status.md`

## Goal

Deploy `services/autoroute-adk/` to Cloud Run or Agent Engine so phones can poll a live `patch.json` and optionally beacon telemetry independently of Vercel (#27).

## Prior art

Reuse `docs/adk-autoroute.md`, `docs/api-contract.md`, and the existing ADK service tree. Prefer Cloud Run/`bear-iot-asp-rec` patterns already documented over a greenfield agent host.

## Shipped on `main`

| Deliverable | Location |
|-------------|----------|
| ADK agent package | `services/autoroute-adk/iot_asp_autoroute/` (`root_agent`, tools, clamps) |
| HTTP ingest entry | `services/autoroute-adk/ingest_main.py` |
| Deploy docs | `docs/adk-autoroute.md` (Agent Engine / Cloud Run commands) |
| Local dry-run | `scripts/autoroute_dev.sh`, `IOT_ASP_AUTOROUTE_DRY_RUN=1` |
| Compatibility shim | `adk_agent/` (re-exports `root_agent`) |

Production deploy URL is not yet the fleet default.

## Remaining scope (owner)

Owner-gated GCP deploy, documented base URL, and smoke that `?patch=` / telemetry round-trip against the live service. No secret values or live URLs are invented in-repo.

## Wire fields

No new contract fields; `docs/api-contract.md` remains canonical for patch/telemetry.

## Clamps / safety

`vol_hard_max=100`; Hold / Manual must still win over live patches.

## Acceptance tests

- [x] Service tree + dry-run path present on main
- [x] Local `bash scripts/autoroute_dev.sh` / CI `autoroute` job path exists
- [ ] Deployed service returns schemaVersion-1 patch JSON (owner)
- [ ] Fleet-facing base URL documented after apply (owner)

## CI gate

`autoroute` job + static gates; live GCP deploy remains manual/owner-gated.

## Risks / HW limits

GCP billing, IAM, and Agent Engine quotas are outside the static CI surface.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/60
- `docs/adk-autoroute.md`, `docs/api-contract.md`
- `.vv/60/adk-autoroute-deploy-status.md`
