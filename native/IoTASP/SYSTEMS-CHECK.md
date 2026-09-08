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

## Alarm / impulse

- [ ] Simulate impulse → `triggered` / `volBlast`
- [ ] Hold / Manual → `cleared` + freeze
- [ ] Quiet ~2.5 s → re-arm

## Explicit non-claims

- SensorKit entitlement: **not granted**
- App Store / TestFlight: **not this checklist**
- LF 10–20 Hz TX on Soundcore: **na** (`lfDriveCapable=false`)
