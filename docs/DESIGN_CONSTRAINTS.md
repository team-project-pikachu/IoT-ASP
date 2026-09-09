# Design constraints (formal)

**TL;DR:** C1 = phone→speaker is **native A2DP only** (no Web Bluetooth TX). C5 = continuous 120 V AC. C6 = public TX band **17–23 kHz**. Full table below; agent rules: [rules-index.md](rules-index.md).

Public IoT-ASP scientific tooling. **These are non-negotiable product constraints**, not optional notes. No site PII. **Index:** [README.md](README.md).

## C1 — iPhone ↔ speaker = native Bluetooth only

| Rule | Detail |
|------|--------|
| Carrier TX path | **iOS system Bluetooth A2DP** (phone pairs in Settings; route via Control Center / system audio output) to Soundcore 2 (or equivalent) |
| Not allowed (MVP) | **Web Bluetooth API**, custom BLE GATT, or in-page device picker for the **carrier / hop / pulse / shriek** audio out |
| Why | Safari/Chrome-iOS cannot select BT sinks; OS owns the audio route. Pairing is 1 phone ↔ 1 speaker. |
| Maximize today | Gesture-unlock `AudioContext`, prefer **48 kHz**, disable AEC/NS/AGC on mic capture where supported, **Arm sensors** on Signal on — see [iphone-bluetooth.md](iphone-bluetooth.md), [sensors-chrome-ios.md](sensors-chrome-ios.md) |
| Fuller BT features | Future **native/Xcode** shell (`AVAudioSession`, Bluetooth options, optional HFP if mic-on-speaker). CoreBluetooth only if BLE **sensors** are added later — never fake Web Bluetooth TX. Tracked: GitHub **#9** |

## C2 — Raspberry Pi field node = USB-C (parked)

| Rule | Detail |
|------|--------|
| Connector | Future **Raspberry Pi 5** field node uses **USB-C** for power / data / optional USB audio interface |
| MVP | **Not** in the public web blaster. Phones remain A2DP TX. |
| Tracking | GitHub **#14** |

## C3 — Software-defined driving via the app

| Rule | Detail |
|------|--------|
| Control surface | The **public web app** is the SDD surface: discover → model → plan → execute for hop / suddenFreq / Gemini autoroute |
| Drivers | Human UI + Gemini/ADK patches drive the acoustic plant; speaker hardware knobs alone are not the control plane |
| Detail | [sdd-app-control.md](sdd-app-control.md) |

## C4 — Maximum practical Web Audio loudness

| Rule | Detail |
|------|--------|
| Default / clamps | **vol locked = 100%** (no UI attenuator); autoroute soft/hard clamp ceiling **100** UI percent — not neighbor-safe 8% |
| Hold | **Hold / Manual** freezes remote patches; Web Audio gain stays at 100% (cannot lower via UI) |
| Warning | **BT absolute volume + speaker hardware/DSP still limit SPL**; app requests max Web Audio gain path only |
| Drivers | Utilize Soundcore **12 W** dual drivers via OS A2DP + max in-app gain; SDD via the app (**C3**) |

## C5 — Continuous 120 V AC fleet power

| Rule | Detail |
|------|--------|
| Invariant | Phones, Soundcore (AC / always charging), and future nodes are on **continuous 120 V AC** — not battery-limited for the study/tooling path |
| Dedicated mode | Low Power Mode **off**; no battery duty-cycle |
| Autoroute / night | Do **not** assume brownout or battery-drain caps when setting gain or the 22:00–07:00 America/New_York volume curve |
| Detail | [power-fleet.md](power-fleet.md), [iphone-dedicated-mode.md](iphone-dedicated-mode.md) |

## C6 — Public TX band is 17–23 kHz only (LF UI removed)

| Rule | Detail |
|------|--------|
| Default / only public TX band | Near-ultrasonic **17–23 kHz** (OS audio → Sonos Beam Gen 2 / phone BT) |
| Removed | Optional **10–20 Hz** arm UI on the public control surface (was hardware-gated) |
| Telemetry | Web fleet always tags `band=17-23k`; `lfArmed` / `lfDriveCapable` stay **false** |
| Node-3 / infrasound sensing | LF **accel proxy** remains primary for `infra_felt` (#18); true infrasound mic/geophone parked |
| Beam clean max (AirPlay) | UI 100% (C4) + digital peak **0.40** (−8.0 dBFS) headroom; macOS/AirPlay ≤~60% or Volume Limit; Night/Speech/Loudness **OFF** — avoids click/clip/**static** on **Mac Studio (M4 Max) → Beam** field path ([sonos-beam-gen2-airplay-volume-constraints.md](sonos-beam-gen2-airplay-volume-constraints.md)) |
| Chromecast (optional) | CAF Web Sender + Default Media Receiver (`CC1AD845`) or `?castAppId=` custom receiver; same **0.40** peak when `audioSink=chromecast`; Chrome/Edge + HTTPS — [chromecast.md](chromecast.md) |

## Downstream docs

- [sdd-app-control.md](sdd-app-control.md) — SDD loop via the app
- [power-fleet.md](power-fleet.md) — 120 V continuous (**C5**)
- [iphone-dedicated-mode.md](iphone-dedicated-mode.md) — dedicated node checklist
- [sensors-chrome-ios.md](sensors-chrome-ios.md) — Chrome iOS sensor arm
- [sensorkit-research-closeout.md](sensorkit-research-closeout.md) — #9 research (Web ≠ SensorKit; companions)
- [iphone-bluetooth.md](iphone-bluetooth.md) — A2DP, codecs, Safari/Chrome-iOS limits
- [chromecast.md](chromecast.md) — optional Google Cast / Chromecast Web Sender
- [autoroute.md](autoroute.md) — sudden-freq → Gemini autorotate control loop
- [multi-llm-registry.md](multi-llm-registry.md) — #13 design sketch (no prod non-Gemini)
- [algorithms.md](algorithms.md) — carrier algorithms over OS BT route
- [timestore.md](timestore.md) — 24 h / year quantum package
- [ai-edge-portal.md](ai-edge-portal.md) — parked optional edge portal
- [mvp-tooling.md](mvp-tooling.md) — verified libraries (no `web-bluetooth` for TX)
