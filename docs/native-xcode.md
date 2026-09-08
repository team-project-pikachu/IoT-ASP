# Native Xcode path — iOS + watchOS (#41)

**SensorKit research closeout (docs):** [sensorkit-research-closeout.md](sensorkit-research-closeout.md) · [`.vv/9/`](../.vv/9/).  
**App sketch:** [`native/IoTASP/`](../native/IoTASP/) · [`native/README.md`](../native/README.md)  
**Honesty:** no SensorKit entitlement grant · no signed App Store build · CLT-only hosts cannot `xcodebuild`.

MVP remains **Safari + iOS native A2DP** ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) C1). Native adds session control, Watch companion, and alarm/impulse shared logic.

## Build matrix (Balanced PR4)

| Host | What works | What does not |
|------|------------|---------------|
| macOS + **Xcode.app** | `open native/IoTASP/IoTASP.xcodeproj` · device/simulator · `cd native/IoTASP && swift test` (`.testTarget` → `Tests/AlarmStateMachineTests.swift`) | — |
| macOS **CLT only** (this Studio default) | `cd native/IoTASP && swift build` + `swift Scripts/alarm_smoke.swift` (no XCTest under CLT) | `swift test` / `xcodebuild` / Simulator |
| Linux / CI | `swift build` if toolchain present; XCTest only with full SDK | iOS/Watch app targets |

## Entitlement / capability honesty

| Capability | Code present? | Runtime |
|------------|---------------|---------|
| CoreMotion 1–100 Hz | Yes (`PhoneMotionLogger`) | Device; Simulator limited |
| Alarm / impulse state machine | Yes (`AlarmStateMachine`, unit-tested) | Simulator + device |
| AVRoutePicker / A2DP / AirPlay session | Yes | Device preferred |
| watchOS UI + Hold/impulse | Yes (`IoTASPWatch`) | Watch sim/device |
| SensorKit readers | Compile-gated `ASP_SENSORKIT_ENTITLED` | **Always stub** until entitlement |
| Soundcore FR clamps | Honesty strings from #43 dossier | Not a lab measurement |
| Sonos Beam | AirPlay sink enum + docs (#39) | Needs Beam HW systems check |

## Workflow (when scheduled)

1. Select Xcode.app (`xcode-select -s /Applications/Xcode.app/Contents/Developer`).
2. Scheme **IoTASP** (iPhone) / **IoTASPWatch**.
3. Device for real Bluetooth A2DP (C1); AirPlay/Beam is a **C1 exception** (research-only). Simulator for UI; Shared: `swift test` under Xcode.app, or `swift build` + `Scripts/alarm_smoke.swift` on CLT.
4. Never invent SensorKit / App Store credentials in git.

## Related

- [sonos-beam.md](sonos-beam.md) (#39) · [hardware/soundcore-specs.md](hardware/soundcore-specs.md) (#43)
- [sensorkit-watch.md](sensorkit-watch.md) · [algorithms.md](algorithms.md) (#42)
- [iphone-bluetooth.md](iphone-bluetooth.md) · [ux-tooling.md](ux-tooling.md)
