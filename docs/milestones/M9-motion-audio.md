# M9 — CoreMotion + AVFoundation mic libs (#111)

**Status:** stub package landed · device HW optional  
**Package:** [`native/IoTASPMotionAudio/`](../../native/IoTASPMotionAudio/)  
**Gate:** `make motion-audio-build` / `bash scripts/motion_audio_build.sh`

## Acceptance map

| AC | How |
|----|-----|
| Motion permission + sample stream stub | `MotionStreamStub.requestPermissionIfNeeded` + `start` (no crash if unavailable) |
| Mic / AVAudioSession + privacy strings | `MicCaptureStub` + `Resources/Info-MotionMic.plist.example` |
| Hooks for HomeNestAlarm / Glass Shatter | `ProductSensorHooks` / `ProductSensorOnset` |
| CI / simulator safe | `stubOnly=true` default; honest unavailable samples |

App shell (#109) merges privacy keys and wires UI toggles — this PR is **lib only**.
