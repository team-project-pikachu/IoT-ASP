# #141 — Near-ultrasonic mic path (48 kHz, AEC/NS/AGC off)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/141 · Labels: `enhancement`, `mvp`, `area:drivers` · Milestone: [iOS / iPhone](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)

## Status

**Implemented on this branch.** CLT-safe metering contract in `UltrasonicMicMeter`. iOS capture in `UltrasonicMicCapture` (SPM-excluded). Simulator stub does not crash. Full on-device FFT bandEnergyUs remains a follow-up; tap currently reports RMS dBFS while `bandEnergyUs(spectrum:)` is tested offline.

## Goal

Native AVFoundation capture matching hop-ultrasonic web constraints: prefer **48 kHz**, AEC/NS/AGC **off**, mono, expose granted sample rate, feed `micEnergy` / `bandEnergyUs` / `micDiff` hooks.

## Prior art

1. **This repo:** web `getUserMedia({echoCancellation:false, noiseSuppression:false, autoGainControl:false, channelCount:1, sampleRate:48000})` in `public/index.html`; `mic_diff.py` α=0.85; `ASPAudioSession` playback-only.
2. **Open PR #133 (#111):** `IoTASPMotionAudio` MicCaptureStub — parallel M9 package, not `native/IoTASP/`.
3. **Org:** none.
4. **awesome-ios:** AudioKit — **do not vendor** (policy + scientific constraints).
5. **Firecrawl / Apple:** `AVAudioEngine.inputNode.installTap` (restart crash if tap not removed — we `removeTap` first); `AVAudioSessionModeMeasurement` vs voice-processing AEC; Switchboard notes iOS echo cancellation is session-mode coupled.

**Decision: build** thin AVAudioEngine tap + Foundation meter. Do not enable voice-processing I/O.

## Shipped on `main`

Playback `ASPAudioSession.configureForFleetSink` only (`native/IoTASP/Shared/Audio/ASPAudioSession.swift`). Mic usage string exists. No 48 kHz capture path.

## Remaining scope

On-device: confirm granted rate and that `.measurement` actually disables VPIO. Real FFT of tap buffers (currently RMS proxy in the engine callback; `bandEnergyUs` is the tested contract). Route/HFP tradeoffs → #146.

## Wire fields

No new schemaVersion. `micEnergy`, `bandEnergyUs`, `micDiff` (`micEnergy − 0.85·outLevel`) per `docs/api-contract.md`.

## Clamps / safety

- Preferred rate 48 kHz; **granted** rate is displayed honestly (44100 → Nyquist 22.05 kHz, US top **not** OK).
- AEC/NS/AGC off is a **request**; `osMayOverride = true` always in status.
- Hold / Manual untouched. No keys. Mic never routed to output (tap only).

## Acceptance tests

| ID | Check |
|----|-------|
| UM-01 | `preferredSampleRate == 48000`, α==0.85 |
| UM-02 | Nyquist OK at 48 kHz, not at 44.1 kHz |
| UM-03 | `micDiff(-20,-30)==5.5` |
| UM-04 | `bandEnergyUs` uses 17–23 kHz bins; empty → -120 |
| UM-05 | SPM excludes `UltrasonicMicCapture.swift` |
| UM-06 | `IoTASPSmoke` + `tests/test_ultrasonic_mic.py` |

## CI gate

`native_compile_check.sh` / `IoTASPSmoke`. pytest source/spec greps.

## Risks / HW limits

- Browser constraints are advisory; native `.measurement` is also best-effort.
- 44.1 kHz hardware cannot represent 23 kHz.
- `installTap` must be removed before re-install (Apple / SO 41805381).
- Soundcore A2DP TX vs built-in mic RX is the default; HFP would destroy US TX (#146).

## Sources

- https://developer.apple.com/documentation/avfaudio/avaudioengine
- https://developer.apple.com/documentation/avfaudio/avaudiosession/mode-swift.struct/measurement
- Firecrawl: installTap restart crash; iOS AEC session notes
- `docs/api-contract.md`, `docs/specs/25-hw-limited-lf-aec-micdiff.md`
