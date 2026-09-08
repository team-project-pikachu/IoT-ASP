# #87 — gcloud/Vertex Gemini Enterprise burst detector stub (no metered calls by default)

## Status

implemented stub — heuristic detector + pytest (independent M8 PR onto `main`)

## Goal

gcloud/Vertex Gemini Enterprise burst detector stub (no metered calls by default). Wire names must agree with Swift `AcousticEventClass` / `AcousticDetectResult`.

## Prior art

In-repo: `native/IoTASP` alarm clamps (`alarmState`, `volBlast`, Hold / Manual); `iot_asp_autoroute.vib_anomaly` is the SciPy anomaly owner (do not fork detection into this stub). HomeNest is a second first-class iOS feature (`native/IoTASPHome`), not a PWA rewrite.

Reuse the heuristic stub in `services/gemini-burst-detect/detect.py` rather than calling paid Gemini. Live Vertex is owner-gated (`scripts/home_apis_gcloud_bootstrap.sh --apply`).

## Shipped on this branch

- `services/gemini-burst-detect/detect.py` — stdlib `detect()`; JSON keys `burst`, `eventClass` (`sound_burst` \| `glass_shatter` \| `unknown`), `confidence`, `escalateDb`
- `tests/test_gemini_burst_detect.py` — threshold, glass vs burst rise-ms boundary, snake_case aliases, zero-value presence
- Swift `AcousticEventClass` raw values match those strings (`native/IoTASPHome/Sources/HomeNestAlarm/AcousticEventClass.swift`)
- `EscalatingAlarmController` — louder while sustaining (`sustainStepDb`); Hold / Manual clears and blocks re-escalate

## Remaining scope

Optional live Gemini Enterprise path after owner enablement. No metered calls from this stub.

## Wire fields

Prefer shared alarm fields in `docs/api-contract.md` (`alarmState`, `volBlast`, `holdManual`, `vol`). Detector JSON uses camelCase wire keys (`eventClass`, `escalateDb`) matching Swift `AcousticDetectResult`. Additive only; `schemaVersion` stays `1`.

## Clamps / safety

Hold / Manual clears blast escalation. No secrets or OAuth tokens in git. Metered Gemini / `--apply` gcloud enables require owner confirmation. Do not scrape `console.nest.google.com`.

## Acceptance tests

- `pytest tests/test_gemini_burst_detect.py` — `eventClass` ∈ {`sound_burst`, `glass_shatter`, `unknown`}
- `make home-ios-build` on macOS — `swift build` without GoogleHomeSDK; `EscalatingAlarmController` tests when XCTest is present
- `bash scripts/home_apis_gcloud_bootstrap.sh` dry-run exits 0

## CI gate

Linux: `.github/workflows/ci.yml` job `home_ios_stub` (`M8 Home iOS stub presence`) — file presence + Python stub pytest; **not** a required merge check; **not** `swift build` (ubuntu has no Swift toolchain in this workflow). Local `make home-ios-build` is macOS-only. Evidence: `.vv/m8/EVIDENCE.md`.

## Risks / HW limits

Proprietary GoogleHomeSDK, Nest premium linking, and live SDM events are owner-gated. CLT hosts may lack XCTest (`scripts/home_ios_build.sh` NOTES that case). Safari + BT cannot capture true infrasound; this detector is a feature-vector stub.

## Sources

- `docs/milestones/M8-nest-gemini-soundburst-mvp.md`
- https://developers.home.google.com/apis/ios/get-started (do not browser-fetch from agents)
- `docs/api-contract.md` (alarmState / volBlast / Hold Manual)
- `native/IoTASPHome/README.md` (scopes + recording consent)
