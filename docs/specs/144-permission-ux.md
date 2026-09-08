# #144 — Permission UX (Info.plist + request sequencing)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/144 · Milestone: [iOS / iPhone](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)

## Status

**Implemented on this branch.** `PermissionSequencer` encodes explain → mic → motion, SensorKit only if entitled. Denied states are recoverable (no crash). Info.plist mic string refined to “on-device”.

## Goal

Deliberate permission UX for mic, motion, and (when entitled) SensorKit matching hop Arm-sensors / Signal-on.

## Prior art

Repo Info.plist already had `NSMotionUsageDescription` / `NSMicrophoneUsageDescription`. Web path requests DeviceMotion from a user gesture. Apple `AVAudioSession.requestRecordPermission`. SensorKit must not be requested in non-entitled builds (#110 / #113). **Build** sequencer; do not invent SK prompts.

## Shipped on `main`

Usage strings only; no sequenced first-run flow.

## Remaining scope

On-device: confirm iOS actually prompts for CoreMotion (accel often has no extra dialog). Settings deep-link when denied is optional.

## Wire fields

None. Status is local UI (`permissionSteps`).

## Clamps / safety

No SensorKit API calls when `entitlementDeclared == false`. Denied mic unarms capture. Hold / Manual unchanged.

## Acceptance tests

`sequence(false) == [microphone, motion]`; entitled appends sensorkit; `skippedUngated` for SK; `IoTASPSmoke`; plist contains on-device copy.

## CI gate

`native_compile_check.sh` + `tests/test_permission_ux.py`.

## Risks / HW limits

Mic prompt is the real first-run gate. Motion usage string covers activity/pedometer; raw accel may not prompt. Never fake an entitled SensorKit dialog.

## Sources

- https://developer.apple.com/documentation/avfaudio/avaudiosession/requestrecordpermission(_:)
- `native/IoTASP/IoTASPApp/Info.plist`
- Issue #144 / #113
