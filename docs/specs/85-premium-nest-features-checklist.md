# #85 — Document premium Nest features required for the MVP (owner account)

## Status

parked — owner premium account checklist

## Goal

Document premium Nest features required for the MVP (owner account).

## Prior art

See `docs/milestones/M8-nest-gemini-soundburst-mvp.md` and `reference/nest-device-access/`. Reuse `native/IoTASP` alarm clamps; HomeNest is a second first-class iOS feature.

## Shipped on `main`

Not on `main` until PR #105 merges. Track delivery on `feat/m8-nest-gemini-home-ios`.

## Remaining scope

Owner verifies Nest premium linking on betty@bearresearch.io.

## Wire fields

Prefer shared alarm fields in `docs/api-contract.md` (`alarmState`, `volBlast`, `holdManual`, `vol`). Detector JSON uses camelCase wire keys (`eventClass`, `escalateDb`) matching Swift `AcousticDetectResult`.

## Clamps / safety

Hold / Manual clears blast escalation. No secrets or OAuth tokens in git. Metered Gemini / `--apply` gcloud enables require owner confirmation.

## Acceptance tests

See milestone acceptance for this issue; stub builds covered by `make home-ios-build` and `pytest tests/test_gemini_burst_detect.py` where applicable. Honest pending items must stay pending until implemented.

## CI gate

CI presence/dry checks in `.github/workflows/ci.yml` for M8 paths; local `make home-ios-build` on macOS. Evidence: `.vv/m8/EVIDENCE.md`.

## Risks / HW limits

Proprietary GoogleHomeSDK, Nest premium linking, and live SDM events are owner-gated. CLT hosts may lack XCTest.

## Sources

- `docs/milestones/M8-nest-gemini-soundburst-mvp.md`
- https://developers.home.google.com/apis/ios/get-started
- `docs/api-contract.md` (alarmState / volBlast / Hold Manual)
