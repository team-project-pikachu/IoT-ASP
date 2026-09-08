# M9 — SensorKit entitlement stub (#110)

**Status:** stub package landed · Apple entitlement **not** granted  
**Package:** [`native/IoTASPSensorKit/`](../../native/IoTASPSensorKit/)  
**Gate:** `make sensorkit-stub-build` / `bash scripts/sensorkit_stub_build.sh`

## Stub vs entitled

| Needs Apple SensorKit entitlement | Stub mode (CI default) |
|-----------------------------------|-------------------------|
| Live `SRSensorReader` streams | `SensorKitGate.startReadersIfEntitled()` no-op |
| Uncommented `com.apple.developer.sensorkit.reader.allow` | Entitlements example keys stay **commented** |
| `-DASP_SENSORKIT_ENTITLED` build config | Flag unset → `entitlementDeclared == false` |

Do not invent research-study approvals or secrets. M5 research remains closed ([sensorkit-research-closeout.md](../sensorkit-research-closeout.md)); this milestone is build + integrate stubs.

## App shell coordination (#109)

This package is a **lib target only**. Merge `Resources/*.example` into the iOS app entitlements / Info.plist when the shell PR lands — do not rewrite `IoTASPApp` here.
