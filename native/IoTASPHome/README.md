# IoTASPHome — Google Home APIs iOS + Nest / Gemini acoustic MVP (M8)

Second first-class native feature alongside [`../IoTASP`](../IoTASP) (ASP ultrasonic / hop).

| Path | Role |
|------|------|
| `Sources/HomeNestAlarm/` | Detector event classes, escalating alarm, Home SDK facade, Nest camera stubs, **glass shatter** pipeline |
| `Sources/HomeNestAlarmUI/` | SwiftUI tabs: ASP Ultrasonic (sibling note) · **HomeNestAlarm** · **Glass Shatter** |
| `Package.swift` | SPM library — **builds without proprietary GoogleHomeSDK** |

## Home APIs iOS get-started (known summary)

Source: https://developers.home.google.com/apis/ios/get-started (last updated 2026-08-28). Agents must **not** browser-fetch this URL.

1. Sample App concepts  
2. Get SDK (SPM / CocoaPods — **not checked in**; use `#if canImport(GoogleHomeSDK)`)  
3. Set up OAuth (owner: **betty@bearresearch.io**)  
4. Initialize home  
5. Integrate APIs (Structure, Device / Camera traits, Automation, Commissioning, …)  
6. Test → Register / Launch (coming soon per docs)

## Features

1. **HomeNestAlarm** — Nest camera discovery stub + sound-burst detect → reactive **louder** alarm (`EscalatingAlarmController` ↔ fleet `volBlast` / `alarmState` concepts).  
2. **Glass Shatter** — event-triggered class `glass_shatter` sharing the same Gemini/gcloud detector interface (`AcousticEventClass`).  
3. Sibling ASP ultrasonic remains in `native/IoTASP`.

## Build (stub mode — required green)

```bash
# from repo root
make home-ios-build
# or
bash scripts/home_ios_build.sh

# direct
cd native/IoTASPHome && swift build
```

Full Xcode.app device/simulator builds need the live Google Home SDK + OAuth client (owner-gated). CLT-only hosts: stub `swift build` is the CI gate.

## gcloud bootstrap

```bash
bash scripts/home_apis_gcloud_bootstrap.sh          # dry-run
bash scripts/home_apis_gcloud_bootstrap.sh --apply # owner confirmation required
```

## Secrets

Never commit OAuth client IDs, Nest tokens, or API keys. Reference 1Password `dev` item **names** only. Identity: betty@bearresearch.io.

## Cross-links

- Apple Home / HomeKit (#15) is **parked and separate** — this is **Google** Home / Nest.  
- Milestone: M8 — Nest cameras + Gemini sound-burst MVP (+ glass shatter).  
- Spec doc: `docs/milestones/M8-nest-gemini-soundburst-mvp.md`

## Swift Playgrounds / Xcode (#102)

This SPM package is the **Swift Playground–adjacent** learning/prototype target for HomeNestAlarm.

### Open in Xcode (recommended on Mac)

1. `open native/IoTASPHome/Package.swift` (or File → Open in Xcode).
2. Build the `HomeNestAlarm` / `HomeNestAlarmUI` schemes — stub mode needs **no** GoogleHomeSDK.
3. SwiftUI previews / a tiny App playground can import `HomeNestAlarmUI` and present `HomeNestRootView()` (tabs: ASP Ultrasonic note · **HomeNestAlarm** · **Glass Shatter**).

### Swift Playgrounds (iPad / Mac)

1. Create an App playground.
2. Add the local package folder `native/IoTASPHome` (File → Add Package / shared playground package), or paste the `Sources/HomeNestAlarm` + `Sources/HomeNestAlarmUI` files.
3. Entry: `HomeNestRootView()` — second-feature tabs already include HomeNestAlarm + Glass Shatter.

### Build gate

```bash
make home-ios-build   # exit 0 without proprietary GoogleHomeSDK
# equivalent: cd native/IoTASPHome && swift build
```

CLT-only hosts may skip `swift test` when XCTest is missing; full Xcode.app runs tests green.

