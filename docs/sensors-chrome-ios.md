# Sensors on Chrome for iOS (WebKit)

Chrome on iPhone is **WKWebView** — same WebKit constraints as Safari for permissions and Sensor APIs. This document is the field checklist for **Arm sensors** / Signal on.

## Arm sequence (one user gesture)

Triggered by **Arm sensors**, **Systems check**, or **Signal on** (first gesture). Order:

1. **Web Audio** — create/resume `AudioContext` (prefer 48 kHz).
2. **Microphone** — `getUserMedia({ audio: { echoCancellation:false, noiseSuppression:false, autoGainControl:false, channelCount:1, sampleRate:48000 } })`.
3. **DeviceMotion** — `DeviceMotionEvent.requestPermission()` when that static method exists (iOS); else listen if the API is present.
4. **DeviceOrientation** — same pattern via `DeviceOrientationEvent.requestPermission()` when available.
5. **Optional** — Ambient Light / Generic Sensor APIs: enable if constructible; otherwise report **na** honestly.

Systems check and the monitor grid show each channel as **ok** / **denied** / **na**.

## What usually works on Chrome iOS

| Capability | Typical Chrome iOS | Notes |
|------------|--------------------|-------|
| `AudioContext` resume | ok after gesture | Required for TX |
| Mic `getUserMedia` | ok after prompt | AEC/NS/AGC may still be partially enforced by the OS |
| `DeviceMotionEvent` | ok after permission | Linear accel / gravity; SensorKit entitlement **not** available in web |
| `DeviceOrientationEvent` | often ok after permission | Same permission family on many iOS versions |
| Ambient Light Sensor | **na** | Rare / missing on iOS WebKit |
| Generic Sensor API | **na** | Not a reliable Chrome iOS surface |
| Web Bluetooth sink select | **na** | Carrier TX uses **native A2DP** only ([iphone-bluetooth.md](iphone-bluetooth.md)) |

## Limits (honest)

- Permission prompts must run in a **user-gesture** stack; auto-play without a tap will not unlock audio or motion.
- HTTPS (or localhost) required for mic.
- Chrome ≠ Chromium desktop: no expectation of full Generic Sensor / Ambient Light coverage.
- Native SensorKit / Core Motion richness needs an Xcode shell ([native-xcode.md](native-xcode.md), issue **#9**).
- For Gemini Enterprise / GCP-tied tabs, keep the **active Google account** on the org account (`betty@bearresearch.io`) — see [iphone-dedicated-mode.md](iphone-dedicated-mode.md).

## Related

- [sensorkit-research-closeout.md](sensorkit-research-closeout.md) — issue **#9** research closeout (Web ≠ SensorKit; companions #14/#15/#18)
- [sdd-app-control.md](sdd-app-control.md) — app as SDD control surface
- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md)
- [iphone-bluetooth.md](iphone-bluetooth.md)
