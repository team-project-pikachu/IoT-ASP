# #140 — Full CoreMotion suite (accel / gyro / mag / attitude / pedometer skip / altimeter)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/140 · Labels: `enhancement`, `mvp`, `area:drivers` · Milestone: [iOS / iPhone](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)

## Status

**Implemented on this branch.** Foundation-only models + policy live in `native/IoTASP/Shared/Sensors/CoreMotionSuite.swift` (CLT `swift build` / `swift run IoTASPSmoke`). Hardware I/O expands `PhoneMotionLogger` (iOS-only; excluded from SPM). Pedometer is skipped with rationale; altimeter is optional when `CMAltimeter.isRelativeAltitudeAvailable`. No SensorKit entitlement invented.

## Goal

Expand beyond the deviceMotion-only stub so fleet phones can feed vib / impulse paths (1–100 Hz science, intense 10–20 Hz band) and telemetry `ax/ay/az`, `gx/gy/gz`, `absA`, `absOmega` per `docs/api-contract.md`.

## Prior art

Searched 2026-09-08 UTC (`CLAUDE.md` order):

1. **This repo:** `PhoneMotionLogger` already starts `deviceMotion` at clamped 1–100 Hz and maps `userAcceleration` + `rotationRate` → `VibSample`. `ImpulseDetector` consumes `VibSample`. SensorKit remains `#if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED` (false). **Reuse** those types; do not fork `VibSample`.
2. **Owner Mac clone / open PRs:** #111 SPM stub (`native/IoTASPMotionAudio`) is a parallel M9 package, not merged. This issue extends the **canonical** `native/IoTASP/` tree on `main`.
3. **Org repos:** no other CoreMotion fleet wrapper.
4. **awesome-ios / awesome-swift:** IMU helpers (Arduino/MPU libs) are not iOS; AudioKit is out of scope. **Do not vendor.**
5. **Firecrawl developer + Apple docs:** [CMMotionManager](https://developer.apple.com/documentation/coremotion/cmmotionmanager) (`isAccelerometerAvailable`, `startAccelerometerUpdates`, gyro / magnetometer / deviceMotion). Background CoreMotion is limited (SO 21947864) — continuous sensing honesty is #145, not this issue.

**Decision: build** thin models + `PhoneMotionLogger` streams on Apple CoreMotion. Do not adopt SpeziSensorKit (entitlement-gated; #143 / #148).

## Shipped on `main`

Verified at `origin/main` @ `6de20b5`:

| What | Where |
|------|-------|
| deviceMotion-only logger | `native/IoTASP/Shared/Sensors/PhoneMotionLogger.swift` |
| `VibSample` ax..gz + absA/absOmega | `ImpulseDetector.swift` |
| SPM excludes PhoneMotionLogger (CLT) | `native/IoTASP/Package.swift` |
| Info.plist motion usage 1–100 Hz / 10–20 Hz | `IoTASPApp/Info.plist` `NSMotionUsageDescription` |

## Remaining scope

On-device Xcode.app validation of `isAccelerometerAvailable` etc. (Studio is CLT-only). Magnetometer indoor calibration. Relative altimeter only when hardware bit is true.

## Wire fields

No new `schemaVersion`. Mapping only:

| Field | Source |
|-------|--------|
| `ax` `ay` `az` / `absA` | deviceMotion `userAcceleration` (g); raw accel only if fused DM unavailable |
| `gx` `gy` `gz` / `absOmega` | deviceMotion `rotationRate` (rad/s); raw gyro fallback |
| mag `mx` `my` `mz` | optional; **not** required contract keys — omitted when nil |

## Clamps / safety

- Sample rate clamped to **[1, 100] Hz** (`CoreMotionSuite.clampHz`); NaN/inf → 50 Hz.
- Pedometer never started.
- Simulator / unavailable hardware → `MotionAvailability.simulatorSafe` (all false); `start` is a no-op when nothing is available (existing `guard` pattern).
- Hold / Manual, vol clamps, C1 A2DP: untouched.
- No SensorKit grant, no OAuth, no Nest tokens.

## Acceptance tests

| ID | Check |
|----|-------|
| CM-01 | `CoreMotionSuite.clampHz(0.1)==1`, `clampHz(400)==100` (`IoTASPSmoke`) |
| CM-02 | `productUse(.pedometer)==.skip` with rationale string |
| CM-03 | `productUse` accel/gyro/deviceMotion == `.fleetVib`; mag/altimeter `.optional` |
| CM-04 | Simulator availability plan `armsAnything == false` |
| CM-05 | `FullMotionSample(0.3,-0.4,0).absA == 0.5`; `telemetryAxes()` has `ax`/`absA` |
| CM-06 | `tests/test_coremotion_suite.py` greps source + spec headings |
| CM-07 | `bash scripts/native_compile_check.sh` prints `IoTASPSmoke OK` |

## CI gate

`tests` job runs `test_coremotion_suite.py` + `test_native_compile_check.py`. `native_compile_check.sh` now `swift run IoTASPSmoke`. No `xcodebuild` claim.

## Risks / HW limits

- Simulator reports most CoreMotion streams unavailable — UI must show `no`, not fake g-values.
- Raw `CMAccelerometerData` includes gravity; fused `userAcceleration` is preferred when both armed.
- Magnetometer is heading/noise, not `vibClass`.
- True 100 Hz depends on device; interval is a request (`deviceMotionUpdateInterval`), not a guarantee.
- Background execution is **not** this issue (#145).

## Sources

- Issue #140
- https://developer.apple.com/documentation/coremotion/cmmotionmanager
- https://developer.apple.com/documentation/coremotion/cmaltimeter/isrelativealtitudeavailable()
- Firecrawl developer: CMMotionManager Apple docs; background CoreMotion limits
- `docs/api-contract.md` axes rows; `docs/specs/41-native-ios-watchos.md`
