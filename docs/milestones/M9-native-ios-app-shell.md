# M9 — Native iOS app shell (SensorKit-ready successor)

**Milestone:** [M9 — Native iOS app (SensorKit + Swift libs)](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)  
**Issue:** [#109](https://github.com/team-project-pikachu/IoT-ASP/issues/109)  
**Package:** [`native/IoTASPHome/`](../../native/IoTASPHome/) (extends M8 HomeNestAlarm; does **not** re-stub Nest Playground)

## Relationship to M8

| M8 (#102 / PR #116) | M9 (#109) |
|---------------------|-----------|
| `HomeNestRootView` — ASP note · HomeNestAlarm · Glass Shatter | `AppShellRootView` — same M8 tabs **+** SensorKit · Motion · Mic placeholders |
| `HomeNestAlarm` / `HomeNestAlarmUI` | New `AppShell` target + UI host |
| `make home-ios-build` | Same gate — stub `swift build` without GoogleHomeSDK |

Sibling lanes (do not duplicate here):

- #110 — `native/IoTASPSensorKit` entitlement-gated stub  
- #111 — `native/IoTASPMotionAudio` CoreMotion + mic stubs  
- #112 — CI / docs for `make home-ios-build` green  
- #113 — privacy / entitlements docs (PR #124)

## Shell layout

```text
AppShellRootView (TabView)
├── ASP Ultrasonic (sibling note → native/IoTASP)
├── Home Nest Alarm          (M8)
├── Glass Shatter            (M8)
├── SensorKit placeholder    → later #110
├── Motion placeholder       → later #111
└── Mic placeholder          → later #111
```

## Agent constraints

- No invented OAuth / Nest client IDs / SensorKit entitlement grants.
- Do not uncomment `com.apple.developer.sensorkit.reader.allow` without human Apple approval.
- Prefer CLI (`gh` / `git` / `gcloud` help) — no browser OAuth.

## Verify

```bash
make home-ios-build
# or
cd native/IoTASPHome && swift build
```

Open in Xcode: `open native/IoTASPHome/Package.swift` → present `AppShellRootView()`.
