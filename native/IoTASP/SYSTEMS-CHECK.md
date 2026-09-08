# Native systems check sketch (#41 / #39 / #43)

**Not a signed build. Not a claim that HW is in hand.** Printable checklist for the first Xcode.app session.

## Preflight

- [ ] `xcode-select -p` points at Xcode.app (not CLT-only)
- [ ] Shared package: with Xcode.app → `cd native/IoTASP && swift test` green; on CLT-only → `swift build` + `swift Scripts/alarm_smoke.swift` (XCTest unavailable under CLT)
- [ ] iPhone unlocked, Bluetooth on; Watch paired if testing companion

## Nodes 1–2 — Soundcore 2 A3105 (A2DP C1)

- [ ] Settings → Bluetooth → Soundcore 2 connected
- [ ] Control Center route shows Soundcore (not phone speaker)
- [ ] Hop / shriek audible; night vol clamp observed
- [ ] Record honesty: A3105 manual FR **70 Hz–20 kHz**; 17–23 kHz at/above ceiling — no flat FR claim (`soundcore-specs.md` / #43)

## Node 3 — Sonos Beam Gen 2 (AirPlay) — **C1 exception / research-only**

AirPlay is **not** C1-compliant carrier TX (`DESIGN_CONSTRAINTS.md` C1 = iOS Bluetooth A2DP only). Keep this node explicitly non-carrier for MVP until a product decision revises C1. Tick only if Beam HW is present for a research listen — do not treat as fleet TX path.

- [ ] AirPlay route to Beam; carriers audible (**research / non-C1** — not MVP carrier TX)
- [ ] Negative: Beam is **not** offered as classic A2DP sink (or document firmware exception)
- [ ] SoCo on LAN (names only in logs; no street PII)

## Alarm / impulse

- [ ] Simulate impulse → `triggered` / `volBlast`
- [ ] Hold / Manual → `cleared` + freeze
- [ ] Quiet ~2.5 s → re-arm

## Explicit non-claims

- SensorKit entitlement: **not granted**
- App Store / TestFlight: **not this checklist**
- LF 10–20 Hz TX on Soundcore: **na** (`lfDriveCapable=false`; below published 70 Hz floor)
- AirPlay / Beam: **not** a C1-compliant carrier path
