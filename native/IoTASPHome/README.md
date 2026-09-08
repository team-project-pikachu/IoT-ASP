# IoTASPHome — Acoustic event class model (M8 / #96)

Shared `AcousticEventClass` + stub detector (`sound_burst` | `glass_shatter` | `unknown`).

| Path | Role |
|------|------|
| `Sources/HomeNestAlarm/AcousticEventClass.swift` | Wire enum + features + `AcousticDetectResult` (`eventClass`, `escalateDb`) |
| `Sources/HomeNestAlarm/BurstDetectClient.swift` | Offline stub thresholds (`onsetDb`, `glassRiseMsMax`) |
| `services/gemini-burst-detect/detect.py` | Python twin — same camelCase JSON keys |

Home app wiring / Glass Shatter tab / Automation notify TODOs: issue **#97**.

```bash
make home-ios-build
python3 -m pytest tests/test_gemini_burst_detect.py -q
```

No secrets. Live Gemini / GoogleHomeSDK are owner-gated.
