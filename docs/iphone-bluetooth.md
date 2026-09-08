# iPhone native Bluetooth (A2DP) for carrier TX

**Formal constraint:** [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) **C1**.

## MVP (Safari web tooling)

1. User pairs **1 iPhone ↔ 1 Soundcore 2** in **Settings → Bluetooth**.
2. Route output via **Control Center** (or Now Playing) to that speaker — **iOS native A2DP**.
3. Web app plays near-ultrasonic carriers with **Web Audio** (`OscillatorNode` / gain). The app **cannot** enumerate or select BT devices.
4. **Do not** use Web Bluetooth for the carrier path.

### Maximize native-BT-compatible Web Audio today

| Setting | Guidance |
|---------|----------|
| Unlock | Resume `AudioContext` on a user gesture (`Signal on` / **Arm sensors** / Transmit) |
| Sample rate | Prefer **48 kHz** when the device exposes it (`AudioContext` options / observe `ctx.sampleRate`) |
| Mic capture | On arm: request `echoCancellation: false`, `noiseSuppression: false`, `autoGainControl: false`, 48 kHz where the browser allows |
| Motion / orientation | `DeviceMotionEvent` / `DeviceOrientationEvent` + `requestPermission` on iOS WebKit (Chrome iOS included) — see [sensors-chrome-ios.md](sensors-chrome-ios.md) |
| Latency | Classic A2DP adds tens–hundreds of ms; hop dwell schedules are **soft** — do not assume sample-accurate sync across phones |
| Volume | App default **100%** Web Audio gain (max practical path). **BT absolute volume + speaker hardware still limit SPL** — raise phone/Soundcore volume separately |
| Codec | Consumer path is typically **AAC** or **SBC** over BT 5.x; Soundcore 2 + BassUp/DSP → expect **near-ultrasonic roll-off** (`SPEC.md`) |

### Out of scope for Safari MVP

- Choosing codec (AAC vs SBC) from the page
- Forcing BT absolute volume APIs
- HFP / headset profile mic-on-speaker
- BLE GATT control of the speaker

## Future native / Xcode shell (#9)

Research closeout: [sensorkit-research-closeout.md](sensorkit-research-closeout.md). Entitlement / Xcode **not** in this wave.

| Capability | API surface |
|------------|-------------|
| Session category / BT options | `AVAudioSession` (playback, possible `.allowBluetoothA2DP`) |
| Mic on accessory | HFP only if elected; separate from A2DP TX science path |
| BLE sensors later | CoreBluetooth — **sensors only**, not carrier TX substitute |
| SensorKit | Research closed; entitlement path remains parked |

## Soundcore 2 A2DP fleet constraints (#43)

Official FR (A3105 owner manual): **70 Hz – 20 kHz**. Hop band 17–23 kHz sits on/above that ceiling; gated **10–20 Hz** LF is below the 70 Hz floor → **na** on Soundcore/A2DP. Rated power **12 W**; C4 100% Web Audio still limited by BT absolute volume + DSP. Spec: [`docs/specs/43-soundcore-2-a2dp.md`](specs/43-soundcore-2-a2dp.md) · root [`SPEC.md`](../SPEC.md).

## Node 3 — Sonos Beam Gen 2 (not A2DP parity)

Third iPhone 16 + Beam Gen 2 is researched under issue **#39**. Expected phone→Beam path is **AirPlay 2**, not Soundcore-style A2DP. LAN control (SoCo CLI / sonos-web) is separate from C1 TX. See [sonos-beam.md](sonos-beam.md).

## Related

- Sensors (Chrome iOS): [sensors-chrome-ios.md](sensors-chrome-ios.md)
- SDD via app: [sdd-app-control.md](sdd-app-control.md)
- Algorithms: [algorithms.md](algorithms.md)
- Autoroute: [autoroute.md](autoroute.md)
- Sonos / Node 3: [sonos-beam.md](sonos-beam.md) (issue **#39**)
- Pi USB-C parked: issue **#14**, [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) **C2**
- Soundcore 2 manufacturer specs: [specs/43-soundcore-2-a2dp.md](specs/43-soundcore-2-a2dp.md) (issue **#43**)
