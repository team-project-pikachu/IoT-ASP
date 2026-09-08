# IoTASPHome — Google Home / Nest + glass shatter (M8)

Second first-class native feature alongside [`../IoTASP`](../IoTASP) (ASP ultrasonic / hop).

| Path | Role |
|------|------|
| `Sources/HomeNestAlarm/` | Event classes (#96), escalating alarm, Home SDK facade, Nest camera stubs, **GlassShatterPipeline** + Automation/notify TODO (#97) |
| `Sources/HomeNestAlarmUI/` | SwiftUI tabs: ASP Ultrasonic · **HomeNestAlarm** · **Glass Shatter** |
| `Package.swift` | SPM — builds without proprietary GoogleHomeSDK |

## Features

1. **HomeNestAlarm** — Nest camera discovery stub + sound-burst → reactive louder alarm (`alarmState` / `volBlast`).
2. **Glass Shatter** — event-triggered `glass_shatter` → snapshot stub → `HomeAutomationNotifyClient` TODO → hotter escalate.
3. Sibling ASP ultrasonic remains in `native/IoTASP`.

```bash
make home-ios-build
```

OAuth / Nest premium: owner-gated (`bettyctai@gmail.com`). No secrets in git.
