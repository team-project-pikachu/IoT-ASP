# Context7 notes — Web Audio + DeviceMotion

Fetched via Context7 MCP (`resolve-library-id` → `query-docs`). CLI `context7_stable.sh` had no usable `--help` verb in this environment; MCP used as fallback per research-cli-kit.

## Libraries

| Topic | Library ID | Why |
|-------|------------|-----|
| Web Audio | `/websites/webaudio_github_io_web-audio-api` | Official Web Audio API; high snippets |
| DeviceMotion | `/mdn/content` | MDN content repo; DeviceMotion + permissions |

## AudioContext / sampleRate

- `AudioContext` constructor takes optional `AudioContextOptions`: `latencyHint`, **`sampleRate`**, `sinkId`, `renderSizeHint`.
- If requested `sampleRate` differs from the output device, the UA may resample (latency impact).
- HOP fleet targets **48000 Hz** so Nyquist (24 kHz) covers the 17–23 kHz hop band.
- Prefer `latencyHint: "playback"` for continuous tone blasting.

## OscillatorNode

- `OscillatorNode` generates periodic waveforms; `type` defaults to `"sine"`; `frequency` is an `AudioParam` (default 440 Hz).
- Used for continuous hop carrier and FSK TX in `public/index.html`.

## DeviceMotionEvent (physical vib channel)

- iOS Safari: call `DeviceMotionEvent.requestPermission()` from a user gesture; resolves `"granted"` | `"denied"`.
- `event.acceleration` — linear accel **excluding gravity** (preferred for shake/vib).
- `event.accelerationIncludingGravity` — includes gravity; can estimate linear by subtracting gravity if `acceleration` is null.
- Web cannot use **SensorKit** (native entitlement); DeviceMotion is the Safari path.

## Coupling to IoT-ASP policy

- Physical vib → DeviceMotion linear |a|
- Acoustic vib → Web Audio AnalyserNode / mic spectrum (separate channel)
- Material-dependent arming chooses which channel is live

## Sources

- https://webaudio.github.io/web-audio-api/
- https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent
