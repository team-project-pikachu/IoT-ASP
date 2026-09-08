# #60 — ADK autoroute production deploy

## Status

Open MVP control-plane work; design landed in earlier ADK issues.

## Goal

Deploy `services/autoroute-adk/` to Cloud Run or Agent Engine so phones can poll a live `patch.json` and optionally beacon telemetry independently of Vercel (#27).

## Prior art

Reuse `docs/adk-autoroute.md`, `docs/api-contract.md`, and the existing ADK service tree. Prefer Cloud Run/`bear-iot-asp-rec` patterns already documented over a greenfield agent host.

## Shipped on `main`

Service code and dry-run path exist under `services/autoroute-adk/`; production deploy URL is not yet the fleet default.

## Remaining scope

Owner-gated GCP deploy, documented base URL, and smoke that `?patch=` / telemetry round-trip against the live service.

## Wire fields

No new contract fields; `docs/api-contract.md` remains canonical for patch/telemetry.

## Clamps / safety

`vol_hard_max=100`; Hold / Manual must still win over live patches.

## Acceptance tests

Deployed service returns schemaVersion-1 patch JSON; local `bash scripts/autoroute_dev.sh` remains green.

## CI gate

`autoroute` job + static gates; live GCP deploy remains manual/owner-gated.

## Risks / HW limits

GCP billing, IAM, and Agent Engine quotas are outside the static CI surface.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/60
- `docs/adk-autoroute.md`, `docs/api-contract.md`
