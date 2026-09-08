# IoTASPSensorKit — SensorKit entitlement stub (M9 / #110)

Standalone SPM library for SensorKit **stub vs entitled** compile paths.
Does **not** own the iOS app shell ([#109](https://github.com/team-project-pikachu/IoT-ASP/issues/109)).

| Path | Role |
|------|------|
| `Sources/IoTASPSensorKit/` | `SensorKitGate`, sample + product hooks |
| `Resources/SensorKit.entitlements.example` | Entitlement keys **commented** — no fake Apple approval |
| `Resources/Info-SensorKit.plist.example` | Privacy usage string scaffolds |
| `Package.swift` | Builds on macOS CLT / CI **without** SensorKit entitlement |

## What requires Apple SensorKit entitlement vs stub mode

| Mode | When | Behavior |
|------|------|----------|
| **Stub (default)** | CI, CLT, unsigned Simulator, no research grant | `entitlementDeclared == false`; `startReadersIfEntitled()` is a no-op; CoreMotion / mic remain primary |
| **Entitled** | Owner has Apple research-study grant for `com.apple.developer.sensorkit.reader.allow` | Uncomment keys in entitlements example → merge into #109 app target; build with `-DASP_SENSORKIT_ENTITLED` |

**Never** invent entitlement approvals, provisioning profiles, or OAuth / Nest client IDs in git.

Related research closeout (M5, closed): [`docs/sensorkit-research-closeout.md`](../../docs/sensorkit-research-closeout.md) · [`docs/sensorkit-watch.md`](../../docs/sensorkit-watch.md).

## Build (stub mode — CI green)

```bash
# from repo root
make sensorkit-stub-build
# or
bash scripts/sensorkit_stub_build.sh

# direct
cd native/IoTASPSensorKit && swift build
```

## Product hooks

`SensorKitProductHook` / `SensorKitOnsetSink` let HomeNestAlarm / Glass Shatter / hop surfaces ingest stub or live samples without linking proprietary SDKs.

## Cross-links

- App shell (#109): merge entitlements + Info keys into the iOS target when ready.
- Motion / mic libs (#111): `native/IoTASPMotionAudio/` (sibling package).
- Existing sketch gate in `native/IoTASP/Shared/Sensors/SensorKitGate.swift` — this package is the **SPM-buildable** source of truth for M9 CI.
