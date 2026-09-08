# IoTASPHome — Google Home / Nest + M9 SensorKit-ready app shell

Second first-class native feature alongside [`../IoTASP`](../IoTASP) (ASP ultrasonic / hop).

| Path | Role |
|------|------|
| `Sources/HomeNestAlarm/` | M8: detector event classes, escalating alarm, Home SDK facade, Nest camera stubs, glass shatter |
| `Sources/AppShell/` | **M9 (#109):** SensorKit / CoreMotion / Mic **module placeholders** (no entitlement invent) |
| `Sources/HomeNestAlarmUI/` | `HomeNestRootView` (M8) · **`AppShellRootView`** (M9 successor tabs) |
| `Resources/Info-AppShell.plist.example` | Motion + mic usage-string scaffold for a future host `.app` |
| `Package.swift` | SPM — **builds without proprietary GoogleHomeSDK** |

## Home APIs iOS get-started (known summary)

Source: https://developers.home.google.com/apis/ios/get-started (last updated 2026-08-28). Agents must **not** browser-fetch this URL.

1. Sample App concepts  
2. Get SDK (SPM / CocoaPods — **not checked in**; use `#if canImport(GoogleHomeSDK)`)  
3. Set up OAuth (owner: **betty@bearresearch.io**)  
4. Initialize home  
5. Integrate APIs (Structure, Device / Camera traits, Automation, Commissioning, …)  
6. Test → Register / Launch (coming soon per docs)

## Features

1. **HomeNestAlarm** — Nest camera discovery stub + sound-burst detect → reactive **louder** alarm.  
2. **Glass Shatter** — event-triggered class `glass_shatter` sharing the Gemini/gcloud detector interface.  
3. **AppShell (M9)** — tabs for SensorKit / Motion / Mic placeholders; wire to #110 / #111 packages later.  
4. Sibling ASP ultrasonic remains in `native/IoTASP`.

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

Never commit OAuth client IDs, Nest tokens, or API keys. Reference 1Password `dev` item **names** only. Identity: betty@bearresearch.io. SensorKit entitlement remains human + Apple gated (`entitlementDeclared == false` in shell).

## Cross-links

- Apple Home / HomeKit (#15) is **parked and separate** — this is **Google** Home / Nest.  
- M8 milestone: `docs/milestones/M8-nest-gemini-soundburst-mvp.md`  
- M9 shell: `docs/milestones/M9-native-ios-app-shell.md`  
- Sibling libs: #110 SensorKit stub · #111 CoreMotion/mic · #112 CI · #113 privacy docs

## Swift Playgrounds / Xcode

### Open in Xcode (recommended on Mac)

1. `open native/IoTASPHome/Package.swift` (or File → Open in Xcode).
2. Build `AppShell` / `HomeNestAlarm` / `HomeNestAlarmUI` — stub mode needs **no** GoogleHomeSDK.
3. Present **`AppShellRootView()`** for the full M9 shell (or `HomeNestRootView()` for M8-only Nest/Glass).

### Swift Playgrounds (iPad / Mac)

1. Create an App playground.
2. Add the local package folder `native/IoTASPHome`.
3. Entry: `AppShellRootView()` — includes M8 Nest/Glass + M9 module placeholder tabs.

### Build gate

```bash
make home-ios-build   # exit 0 without proprietary GoogleHomeSDK
```

CLT-only hosts may skip `swift test` when XCTest is missing; full Xcode.app runs tests green.
