# SensorKit / edge companions — research closeout (#9)

**Status:** Research ACs complete · **native entitlement / Xcode shell implementation parked**  
**Issue:** [team-project-pikachu/IoT-ASP#9](https://github.com/team-project-pikachu/IoT-ASP/issues/9)  
**Evidence:** [`.vv/9/`](../.vv/9/)  
**Revision anchor:** see evidence package (git HEAD at closeout)

This document freezes the research deliverable for Project 5 Todo **#9**. It does **not** authorize SensorKit entitlement work, App Store research-study approval, or an Xcode shell in this wave.

---

## Verdict (one line)

**Safari / Chrome-iOS (WKWebView) cannot use SensorKit.** Fleet sensors stay **DeviceMotion + Web Audio + mic**; richer motion/ambient stays native-only; edge depth comes from companions **#14 / #15 / #18**.

---

## R1 — Web cannot SensorKit

| Claim | Evidence |
|-------|----------|
| SensorKit is an **iOS native** framework (iOS 14+) | Apple docs ingest: [`reference/knowledge/apple-sensorkit/`](../reference/knowledge/apple-sensorkit/sensorkit-apple-developer-documentation.md) |
| Access requires entitlement **`com.apple.developer.sensorkit.reader.allow`** | Same ingest — “preapproved research study” entitlement path |
| Entitlement is **not** exposable to WebKit / Safari / Chrome iOS | No Web IDL; Systems check reports SensorKit **na** (`public/index.html`) |
| Web stand-ins | `DeviceMotionEvent` / `DeviceOrientationEvent` + `requestPermission` on iOS; mic + AnalyserNode for acoustic vib |

**Policy coupling:** [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) **C1** — carrier TX remains **iOS native A2DP**; SensorKit is orthogonal sensing, never a Web Bluetooth TX substitute.

### What SensorKit would add (parked)

From Apple overview (research only — not implemented):

- Processed / select raw sensor streams (accel, rotation, ambient light, usage metrics, Watch pairing context, etc. via `SRSensor`)
- Authorization via `SRSensorReader` + research entitlement
- **Not** available to Mac Catalyst / visionOS-compat shells for this purpose

MVP does **not** need those streams. Physical vib channel is already DeviceMotion linear |a|; acoustic vib is mic spectrum.

---

## R2 — Edge companions (parallel paths, not entitlement substitutes)

Companions expand **edge sensing / room context**. They do **not** unlock SensorKit in the browser.

| Companion | Issue | Role relative to #9 | Status |
|-----------|-------|---------------------|--------|
| Raspberry Pi 5 field node | [#14](https://github.com/team-project-pikachu/IoT-ASP/issues/14) | USB-C edge telemetry / optional mic·accel·GPIO; pull same autoroute patches | Backlog / parked |
| Apple Home / HomeKit or Matter | [#15](https://github.com/team-project-pikachu/IoT-ASP/issues/15) | Accessory / room sensors without SensorKit first | Backlog |
| Node-3 chair-taped | [#18](https://github.com/team-project-pikachu/IoT-ASP/issues/18) | Structure-borne accel bias; infrasound **LF-accel proxy** (`infra_felt`) | Backlog |

### Chair-taped node 3 (routing bias)

Future third phone mechanically coupled to a chair → prefer structure-borne vibration; algorithm routing bias toward accel-triggered pulse/shriek — see [algorithms.md](algorithms.md). Related priors: [#16](https://github.com/team-project-pikachu/IoT-ASP/issues/16), [physics.md](physics.md).

### Related active control-plane work

- Gemini continuous autoroute: [#12](https://github.com/team-project-pikachu/IoT-ASP/issues/12)
- NS / seismo-acoustic priors: [#16](https://github.com/team-project-pikachu/IoT-ASP/issues/16)

---

## R3 — Chrome iOS sensor arm (field checklist)

Canonical procedure: **[sensors-chrome-ios.md](sensors-chrome-ios.md)**.

Arm sequence (one user gesture — **Arm sensors** / **Systems check** / **Signal on**):

1. Resume `AudioContext` (prefer 48 kHz)
2. `getUserMedia` mic (AEC/NS/AGC off where allowed)
3. `DeviceMotionEvent.requestPermission()` when present
4. `DeviceOrientationEvent.requestPermission()` when present
5. Ambient Light / Generic Sensor → report **na** honestly if missing

| Channel | Chrome iOS typical | Notes |
|---------|-------------------|-------|
| Web Audio | ok after gesture | Required for TX |
| Mic | ok after prompt | OS may still enforce some DSP |
| DeviceMotion | ok after permission | SensorKit **not** available |
| DeviceOrientation | often ok | Same permission family |
| Ambient Light / Generic Sensor | **na** | Unreliable on iOS WebKit |
| Web Bluetooth sink pick | **na** | A2DP only — [iphone-bluetooth.md](iphone-bluetooth.md) |
| SensorKit | **na** | Native entitlement only |

Dedicated-node hygiene: [iphone-dedicated-mode.md](iphone-dedicated-mode.md).

---

## R4 — Native Xcode shell (explicit non-goal this wave)

Tracked workflow only: [native-xcode.md](native-xcode.md).

| This wave | Deferred |
|-----------|----------|
| Research closeout + companion cross-links | Apple Developer research-study SensorKit entitlement |
| Chrome iOS arm checklist | Xcode project, provisioning profiles |
| Honest Systems check **na** row | `AVAudioSession` / Core Motion / SensorKit reader code |

**Do not** file entitlement requests or ship a native shell under #9 research scope.

---

## Close criteria (research)

- [x] Document that Web cannot SensorKit (entitlement + no Web API)
- [x] Link companions #14 / #15 / #18 with roles
- [x] Chrome iOS sensor arm checklist present and linked
- [x] Explicit “no native entitlement this wave”
- [x] Evidence package under `.vv/9/`

**Implementation** remains parked. Project board Status → Done is owned by the **integrate** lane (may defer promotion until Gemini #12 evidence is green if the board gate requires all Todo issues together).

## Sources

- https://developer.apple.com/documentation/sensorkit
- https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.sensorkit.reader.allow
- Local ingest: `reference/knowledge/apple-sensorkit/`, `reference/knowledge/mdn-devicemotion/`, `reference/knowledge/CONTEXT7.md`
