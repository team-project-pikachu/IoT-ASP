# iOS device capability matrix (#149)

Unknown cells are **unknown** — do not treat this as a lab report. Nyquist / BT codec resampling can still destroy 17–23 kHz even when 48 kHz capture is granted.

| Device | iOS | Mic 48 kHz? | US band usable? | CoreMotion | A2DP Soundcore | Sonos route | SensorKit entitled build | Notes |
|--------|-----|-------------|-----------------|------------|----------------|-------------|--------------------------|-------|
| iPhone 16 (node 1) | unknown | unknown | unknown (A2DP roll-off expected) | expected yes | expected yes (C1) | n/a | **no** | Fleet phone; verify on-device (#151) |
| iPhone 16 (node 2) | unknown | unknown | unknown | expected yes | expected yes (C1) | n/a | **no** | Different room |
| iPhone 14 (node 3 candidate) | unknown | unknown | unknown | expected yes | expected yes | AirPlay if Beam present (#39) | **no** | Chair-taped role (#18) |
| Simulator | host | no device mic | no | often unavailable | no | no | no | CLT smoke only |

Ambient light: **n/a** on public iOS APIs (#142).

BT resampling: AAC/SBC + Soundcore DSP — do not claim calibrated ultrasonic TX over A2DP (`SPEC.md`).
