# Native Xcode path (parked — issue #9)

**Research closeout (docs only):** [sensorkit-research-closeout.md](sensorkit-research-closeout.md) · evidence [`.vv/9/`](../.vv/9/).  
**This wave:** no SensorKit entitlement, no Xcode project.

MVP remains **Safari + iOS native A2DP** ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md)). Xcode is for a future shell that can unlock fuller audio/BT APIs.

## Workflow (when scheduled)

1. Open Xcode → iOS App (Swift) targeting current iOS.
2. Run on **Simulator** for UI; **device** required for real Bluetooth A2DP / SensorKit.
3. Configure `AVAudioSession` for playback with Bluetooth A2DP allowed.
4. SensorKit / mic entitlements only with proper provisioning — research gate.

## What native adds vs web

| Feature | Safari MVP | Native |
|---------|------------|--------|
| A2DP route | OS / Control Center | Same OS route + session category control |
| Pick BT sink in-app | No | Still limited; system UI |
| Disable AEC/NS/AGC | Partial (`getUserMedia` constraints) | Stronger `AVAudioSession` / audio unit control |
| SensorKit | No | Research closed (#9); entitlement parked |
| CoreBluetooth sensors | No | Optional later — **not** carrier TX |

Author UX wireframes in **Chrome**; validate HIG on Simulator + device Safari/native. See [iphone-bluetooth.md](iphone-bluetooth.md), [ux-tooling.md](ux-tooling.md).

## Sonos AirPlay shell sketch (#39)

Canonical app: [`native/IoTASP/`](../native/IoTASP/) (iOS + Watch) — fleet sink picker includes Soundcore A2DP and Sonos Beam AirPlay. Legacy sketch: [`native/ios-sonos-shell/`](../native/ios-sonos-shell/). Docs: [sonos-beam.md](sonos-beam.md), [sensorkit-watch.md](sensorkit-watch.md). Full `xcodebuild` needs Xcode.app (Command Line Tools alone are insufficient on this Studio). Shared alarm/impulse logic: `swift test` in `native/IoTASP/`.
