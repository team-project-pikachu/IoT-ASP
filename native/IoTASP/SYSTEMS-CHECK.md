# Native systems check sketch (#41 / #39 / #43)

**Not a signed build. Not a claim that HW is in hand.** Printable checklist for the first Xcode.app session.

## Preflight

- [ ] `xcode-select -p` points at Xcode.app (not CLT-only)
- [ ] `cd native/IoTASP && swift test` green on Shared
- [ ] iPhone unlocked, Bluetooth on; Watch paired if testing companion

## Nodes 1–2 — Soundcore 2 A3105 (A2DP C1)

- [ ] Settings → Bluetooth → Soundcore 2 connected
- [ ] Control Center route shows Soundcore (not phone speaker)
- [ ] Hop / shriek audible; night vol clamp observed
- [ ] Record honesty: FR unpublished — no flat 17–23 kHz claim (`soundcore-specs.md`)

## Node 3 — Sonos Beam Gen 2 (AirPlay) — **only if Beam present**

- [ ] AirPlay route to Beam; carriers audible
- [ ] Negative: Beam is **not** offered as classic A2DP sink (or document firmware exception)
- [ ] SoCo on LAN (names only in logs; no street PII)

## CoreMotion suite (#140)

- [ ] Arm CoreMotion: systems-check shows accel/gyro/deviceMotion **yes** on device (Simulator may be **no**)
- [ ] `|a|` updates while phone is shaken; `|ω|` updates on rotate
- [ ] Pedometer row stays **skip** (never requested)
- [ ] Magnetometer / altimeter: **yes** only if hardware bit is true — no fake values
- [ ] Sample rate request in 1–100 Hz (`plan Hz`)

## Near-ultrasonic mic (#141)

- [ ] Arm mic: preferred 48000 Hz vs **granted** Hz shown
- [ ] US Nyquist OK only if granted ≥ 46 kHz
- [ ] AEC/NS/AGC off **requested** (measurement mode); note OS may override
- [ ] Simulator: stub note, no crash
- [ ] Do not claim calibrated 17–23 kHz SPL

## Alarm / impulse

- [ ] Simulate impulse → `triggered` / `volBlast`
- [ ] Hold / Manual → `cleared` + freeze
- [ ] Quiet ~2.5 s → re-arm

## SensorKit entitlement (#148)

- [ ] **Not approved** in this public repo (do not check this box unless a real Apple grant exists)
- [ ] Bundle ID `io.bearresearch.iotasp` owned by the team
- [ ] Capability `com.apple.developer.sensorkit.reader.allow` requested in Apple Developer (human)
- [ ] Provisioning regenerated after approval
- [ ] `ASP_SENSORKIT_ENTITLED` still **off** until the above are true

See `docs/sensorkit-entitlement-checklist.md`.

## Explicit non-claims

- SensorKit entitlement: **not granted**
- App Store / TestFlight: **not this checklist**
- LF 10–20 Hz TX on Soundcore: **na** (`lfDriveCapable=false`)
