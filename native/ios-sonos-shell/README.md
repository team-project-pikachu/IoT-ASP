# iOS Sonos shell stub (issue #39)

Minimal SwiftUI sketch for **AirPlay route picking** toward a Sonos Beam Gen 2 (Node 3). Not a shipping app.

## Why this exists

Safari/Chrome iOS cannot select AirPlay sinks in-page. A native shell can embed [`AVRoutePickerView`](https://developer.apple.com/documentation/avkit/avroutepickerview) so the operator routes Web Audio / AVAudioEngine output to the Beam without leaving the scientific tooling surface.

LAN control (volume / group / queue) stays with **SoCo CLI** / **sonos-web** — see [`docs/sonos-beam.md`](../../docs/sonos-beam.md).

## Tooling check

```bash
xcodebuild -version
```

On this Studio checkout (2026-09-07): only **Command Line Tools** are active — `xcodebuild` requires full **Xcode.app**. Open the sources in:

- **Xcode** (preferred): File → New → App, drop in `Sources/`, or
- **Swift Playgrounds** (iPad/Mac): paste `SonosRouteShellApp.swift`, `ContentView.swift`, `RoutePicker.swift`, and `BeamAirPlayHeadroom.swift` into an App playground (`ContentView` references `RoutePicker` and `BeamAirPlayHeadroom`).

## Session policy (sketch)

```swift
try AVAudioSession.sharedInstance().setCategory(
  .playback,
  mode: .default,
  policy: .longFormAudio
)
```

See Apple: [Supporting AirPlay in your app](https://developer.apple.com/documentation/avfoundation/supporting-airplay-in-your-app). Use `.allowAirPlay` explicitly when the category is `playAndRecord`. Do **not** treat `.allowBluetoothA2DP` as the Beam path (that option is for Soundcore-class A2DP sinks on nodes 1–2).

## Files

| Path | Role |
|------|------|
| `Sources/SonosRouteShellApp.swift` | `@main` app entry |
| `Sources/ContentView.swift` | Placeholder tone + `AVRoutePickerView` |
| `Sources/RoutePicker.swift` | `UIViewRepresentable` wrapper |
| `Sources/BeamAirPlayHeadroom.swift` | Shared AirPlay peak headroom constant |

## Honesty

- Stub does not claim Atmos, A2DP, or Web Bluetooth.
- Device build required to validate AirPlay to hardware Beam.
