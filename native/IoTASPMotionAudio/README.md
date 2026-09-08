# IoTASPMotionAudio — CoreMotion + AVFoundation mic stubs (M9 / #111)

Standalone SPM library for ultrasonic / hop motion + mic paths.
Does **not** own the iOS app shell ([#109](https://github.com/team-project-pikachu/IoT-ASP/issues/109)).

| Path | Role |
|------|------|
| `MotionStreamStub` | CoreMotion 1–100 Hz stream; simulator / CI safe when HW missing |
| `MicCaptureStub` | Mic / `AVAudioSession` path; `stubOnly` default for CI |
| `ProductSensorHooks` | Onset events for HomeNestAlarm / Glass Shatter / hop alarm |
| `Resources/Info-MotionMic.plist.example` | `NSMotionUsageDescription` + `NSMicrophoneUsageDescription` |

## Feature flags / stub mode

| Flag / setting | Default | Effect |
|----------------|---------|--------|
| `MicCaptureStub.stubOnly` | `true` | No `AVAudioEngine` tap; idle unavailable sample |
| `MotionStreamStub.allowSyntheticFallback` | `false` | Prefer honest `motion_unavailable` over fake HW |
| App Info.plist privacy keys | example only | Merge into #109 shell when wiring UI |

`make motion-audio-build` must stay green on CLT without device sensors.

## Product hooks (M8 alignment)

`ProductSensorOnset` kinds: `motionImpulse`, `micDiff`, `soundBurstHint`, `glassShatterHint`.  
HomeNestAlarm / Glass Shatter can subscribe via `ProductSensorOnsetSink` without linking GoogleHomeSDK.

## Build

```bash
make motion-audio-build
# or
bash scripts/motion_audio_build.sh
cd native/IoTASPMotionAudio && swift build
```

## Cross-links

- SensorKit stub (#110): `native/IoTASPSensorKit/`
- Existing sketch: `native/IoTASP/Shared/Sensors/PhoneMotionLogger.swift`, `Shared/Audio/ASPAudioSession.swift`
- Docs: [`docs/milestones/M9-motion-audio.md`](../../docs/milestones/M9-motion-audio.md)
