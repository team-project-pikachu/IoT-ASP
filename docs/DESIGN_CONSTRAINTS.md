# Design constraints (formal)

Public IoT-ASP scientific tooling. **These are non-negotiable product constraints**, not optional notes. No site PII.

## C1 — iPhone ↔ speaker = native Bluetooth only

| Rule | Detail |
|------|--------|
| Carrier TX path | **iOS system Bluetooth A2DP** (phone pairs in Settings; route via Control Center / system audio output) to Soundcore 2 (or equivalent) |
| Not allowed (MVP) | **Web Bluetooth API**, custom BLE GATT, or in-page device picker for the **carrier / hop / pulse / shriek** audio out |
| Why | Safari cannot select BT sinks; OS owns the audio route. Pairing is 1 phone ↔ 1 speaker. |
| Maximize today | Gesture-unlock `AudioContext`, prefer **48 kHz**, disable AEC/NS/AGC on mic capture where supported, document BT latency for hop timing — see [iphone-bluetooth.md](iphone-bluetooth.md) |
| Fuller BT features | Future **native/Xcode** shell (`AVAudioSession`, Bluetooth options, optional HFP if mic-on-speaker). CoreBluetooth only if BLE **sensors** are added later — never fake Web Bluetooth TX. Tracked: GitHub **#9** |

## C2 — Raspberry Pi field node = USB-C (parked)

| Rule | Detail |
|------|--------|
| Connector | Future **Raspberry Pi 5** field node uses **USB-C** for power / data / optional USB audio interface |
| MVP | **Not** in the public web blaster. Phones remain A2DP TX. |
| Tracking | GitHub **#14** |

## Downstream docs

- [iphone-bluetooth.md](iphone-bluetooth.md) — A2DP, codecs, Safari limits
- [autoroute.md](autoroute.md) — sudden-freq → Gemini autorotate control loop
- [algorithms.md](algorithms.md) — carrier algorithms over OS BT route
- [mvp-tooling.md](mvp-tooling.md) — verified libraries (no `web-bluetooth` for TX)
