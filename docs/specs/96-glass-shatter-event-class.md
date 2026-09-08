# #96 — Glass shatter model / event class (`sound_burst` | `glass_shatter`)

## Status

implemented stub — shared Python + Swift wire keys

## Goal

Formalize `AcousticEventClass` and stub thresholds (`riseMs`, `energyDeltaDb`).
Python + Swift stubs must agree on JSON field names.

## Prior art

Nest ADK detector labels in `services/autoroute-adk/iot_asp_autoroute/nest/detector.py`
(`glass_shatter` / `sound_burst` / `other`). This issue adds the HomeNest twin:
`AcousticDetectResult` camelCase keys and `services/gemini-burst-detect/detect.py`.

## Shipped

- `native/IoTASPHome/Sources/HomeNestAlarm/AcousticEventClass.swift`
- `native/IoTASPHome/Sources/HomeNestAlarm/BurstDetectClient.swift`
- `services/gemini-burst-detect/detect.py`
- `tests/test_gemini_burst_detect.py`
- `docs/api-contract.md` § M8 acoustic detector result

## Remaining scope

Calibrated thresholds on real glass events; live Gemini (owner-gated). Home UI / notify: #97.

## Wire fields

Canonical: `docs/api-contract.md` — `eventClass`, `escalateDb`, `burst`, `confidence`.

## Acceptance tests

- `pytest tests/test_gemini_burst_detect.py`
- `make home-ios-build` (macOS)

## CI gate

`home_ios_stub` job in `.github/workflows/ci.yml`.
