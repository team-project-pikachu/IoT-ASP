# Native Xcode path — iOS + watchOS (#41)

**SensorKit research closeout (docs):** [sensorkit-research-closeout.md](sensorkit-research-closeout.md) · [`.vv/9/`](../.vv/9/).  
**App sketch:** [`native/IoTASP/`](../native/IoTASP/) · [`native/README.md`](../native/README.md)  
**Honesty:** no SensorKit entitlement grant · no signed App Store build · CLT-only hosts cannot `xcodebuild`.

MVP remains **Safari + iOS native A2DP** ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) C1). Native adds session control, Watch companion, and alarm/impulse shared logic.

## Build matrix (Balanced PR4)

| Host | What works | What does not |
|------|------------|---------------|
| macOS + **Xcode.app** | `open native/IoTASP/IoTASP.xcodeproj` · device/simulator | — |
| macOS **CLT only** (this Studio default) | `bash scripts/native_compile_check.sh` / `make native-check` · `swift Scripts/alarm_smoke.swift` · SPM Shared build | `xcodebuild` / Simulator |
| Linux / CI | Shared Swift tests if toolchain present | iOS/Watch app targets |

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
3. Device for real Bluetooth A2DP / AirPlay; Simulator for UI + `swift test` for Shared.
4. Never invent SensorKit / App Store credentials in git.

## Related

- [sonos-beam.md](sonos-beam.md) (#39) · [hardware/soundcore-specs.md](hardware/soundcore-specs.md) (#43)
- [sensorkit-watch.md](sensorkit-watch.md) · [algorithms.md](algorithms.md) (#42)
- [iphone-bluetooth.md](iphone-bluetooth.md) · [ux-tooling.md](ux-tooling.md)
| Feature | Safari MVP | Native |
|---------|------------|--------|
| A2DP route | OS / Control Center | Same OS route + session category control |
| Pick BT sink in-app | No | Still limited; system UI |
| Disable AEC/NS/AGC | Partial (`getUserMedia` constraints) | Stronger `AVAudioSession` / audio unit control |
| SensorKit | No | Research closed (#9); entitlement parked |
| CoreBluetooth sensors | No | Optional later — **not** carrier TX |

Author UX wireframes in **Chrome**; validate HIG on Simulator + device Safari/native. See [iphone-bluetooth.md](iphone-bluetooth.md), [ux-tooling.md](ux-tooling.md).
## Soundcore A2DP honesty (#43)
Native shells must treat Soundcore 2 FR **70 Hz – 20 kHz** (A3105 manual) as the published box: do not claim calibrated 17–23 kHz or 10–20 Hz playback over A2DP. See [`docs/specs/43-soundcore-2-a2dp.md`](specs/43-soundcore-2-a2dp.md). SensorKit remains entitlement-gated (#9 / #41).
## Sonos AirPlay shell sketch (#39)
Canonical app: [`native/IoTASP/`](../native/IoTASP/) (iOS + Watch) — fleet sink picker includes Soundcore A2DP and Sonos Beam AirPlay. Legacy sketch: [`native/ios-sonos-shell/`](../native/ios-sonos-shell/). Docs: [sonos-beam.md](sonos-beam.md), [sensorkit-watch.md](sensorkit-watch.md). Full `xcodebuild` needs Xcode.app (Command Line Tools alone are insufficient on this Studio). Shared alarm/impulse logic: `swift test` in `native/IoTASP/`.
