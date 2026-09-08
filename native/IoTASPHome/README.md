# IoTASPHome — Google Home APIs iOS + Nest / Gemini acoustic MVP (M8)

Second first-class native feature alongside [`../IoTASP`](../IoTASP) (ASP ultrasonic / hop).

| Path | Role |
|------|------|
| `Sources/HomeNestAlarm/` | Detector event classes, escalating alarm, Home SDK facade, Nest camera stubs, **glass shatter** pipeline |
| `Sources/HomeNestAlarmUI/` | SwiftUI tabs: ASP Ultrasonic (sibling note) · **HomeNestAlarm** · **Glass Shatter** |
| `Package.swift` | SPM library — **builds without proprietary GoogleHomeSDK** (`#if canImport(GoogleHomeSDK)`) |

## Home APIs iOS get-started (known summary)

Source: https://developers.home.google.com/apis/ios/get-started (last updated 2026-08-28). Agents must **not** browser-fetch this URL and must **not** scrape `console.nest.google.com`.

1. Sample App concepts
2. Get SDK (SPM / CocoaPods — **not checked in**; use `#if canImport(GoogleHomeSDK)`)
3. Set up OAuth (owner: **bettyctai@gmail.com**)
4. Initialize home
5. Integrate APIs (Structure, Device / Camera traits, Automation, Commissioning, …)
6. Test → Register / Launch (coming soon per docs)

## Features

1. **HomeNestAlarm** — Nest camera discovery stub + sound-burst detect → reactive **louder** alarm (`EscalatingAlarmController` ↔ fleet `volBlast` / `alarmState` concepts).
2. **Glass Shatter** — event-triggered class `glass_shatter` sharing the same Gemini/gcloud detector interface (`AcousticEventClass`: `sound_burst` | `glass_shatter` | `unknown`).
3. Sibling ASP ultrasonic remains in `native/IoTASP`.

## Build (stub mode — required green)

```bash
# from repo root (macOS; Swift toolchain required)
make home-ios-build
# or
bash scripts/home_ios_build.sh

# direct
cd native/IoTASPHome && swift build
```

Linux CI does **not** run `swift build`. It only checks that `Package.swift` + the Python detector stub exist (`home_ios_stub` job). Full Xcode.app device/simulator builds need the live Google Home SDK + OAuth client (owner-gated). CLT-only hosts: stub `swift build` is the local gate; `swift test` may NOTE if XCTest is missing.

## gcloud bootstrap

```bash
bash scripts/home_apis_gcloud_bootstrap.sh          # dry-run (default; no mutations)
bash scripts/home_apis_gcloud_bootstrap.sh --apply # owner confirmation required
```

Never run `--apply` without explicit owner confirmation. Dry-run prints service names only.

## OAuth scopes (document only — do not mint tokens)

Owner (named only): **bettyctai@gmail.com**. Configure clients in Google Home Developer Console + GCP; store values in 1Password `dev` by **item name**. Never commit client IDs, client secrets, Nest tokens, refresh tokens, or cookies.

Documented scope names (owner enables in consoles; this repo does not request them at runtime):

| Surface | Scope / service (names only) |
|---------|------------------------------|
| Smart Device Management (Nest camera events) | `https://www.googleapis.com/auth/sdm.service` |
| Google Home APIs iOS | Home Developer Console OAuth client (Structure / Device / Automation / Commissioning as listed in the get-started guide) |
| Vertex / Gemini Enterprise (optional live detector) | `aiplatform.googleapis.com` via `gcloud services enable` **only** with `--apply` |
| Pub/Sub (SDM event delivery) | `pubsub.googleapis.com` — same `--apply` gate |

This stub never performs the OAuth dance and never calls those APIs.

## Recording consent

- Nest camera **audio/video recording, clip export, and cloud history** stay off unless the owner explicitly consents in the Google Home / Nest product UI.
- This package does **not** capture, store, or upload media. Detector input is numeric feature vectors (`energyDeltaDb`, `riseMs`, optional `eventClassHint`).
- Glass-shatter / sound-burst classes are labels on those features, not recordings.
- Do not scrape Nest consoles or invent device serials / structure IDs.

## Secrets

Never commit OAuth client IDs, Nest tokens, or API keys. Reference 1Password `dev` item **names** only.

## Cross-links

- Apple Home / HomeKit (#15) is **parked and separate** — this is **Google** Home / Nest.
- Milestone: [`docs/milestones/M8-nest-gemini-soundburst-mvp.md`](../../docs/milestones/M8-nest-gemini-soundburst-mvp.md)
- Detector stub: [`services/gemini-burst-detect/`](../../services/gemini-burst-detect/)
- Spec: [`docs/specs/87-gemini-burst-detector-stub.md`](../../docs/specs/87-gemini-burst-detector-stub.md)
