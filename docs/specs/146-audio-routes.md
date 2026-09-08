# #146 — AVAudioSession + Bluetooth routes (Soundcore / Sonos vs built-in)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/146

## Status

**Implemented on this branch.** `AudioRouteMatrix` + `configureForFleetSink(_:micArmed:)`. Default A2DP TX + phone mic RX. HFP rejected. AirPlay long-form for Sonos is not C1 parity.

## Goal

Harden TX/RX routing matching C1 (native Bluetooth only; no Web Bluetooth).

## Prior art

Existing `ASPAudioSession` playback-only; `AVRoutePickerView`; Apple `allowBluetoothA2DP`; #39 AirPlay research. **Build** matrix; do not use CoreBluetooth for carrier TX.

## Shipped on `main`

Playback category only.

## Remaining scope

On-device Soundcore ↔ built-in switch. Route-change observer UI. HFP never elected.

## Wire fields

Systems-check `audioSink` parity with web `hwCaps.audioSink`. No schemaVersion bump.

## Clamps / safety

C1: no Web Bluetooth. No HFP for hop TX. Hold / Manual unchanged.

## Acceptance tests

Soundcore+mic → playAndRecord + allowBluetoothA2DP, hfpRisk false; Sonos → longFormAudio playback.

## CI gate

IoTASPSmoke + `tests/test_audio_routes.py`.

## Risks / HW limits

OS may still pick HFP if the user selects a headset mic. Documented; not silently accepted as C1.

## Sources

https://developer.apple.com/documentation/avfaudio/avaudiosession/category-swift.struct/playandrecord
Issue #146, `docs/iphone-bluetooth.md`, C1.
