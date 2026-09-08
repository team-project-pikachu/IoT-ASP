# Soundcore 2 — A2DP fleet sink

**Issue:** [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43)  
**Status:** Canonical manufacturer FR + honesty in `docs/hardware/soundcore-specs.md` and `docs/specs/43-soundcore-2-a2dp.md` (PR #55). This file is the native-wiring pointer.  
**Fleet:** Nodes **1–2** = iPhone 16 ↔ Soundcore 2 over **iOS native A2DP** ([DESIGN_CONSTRAINTS.md](../DESIGN_CONSTRAINTS.md) **C1**). Node **3** = Sonos Beam AirPlay ([sonos-beam.md](../sonos-beam.md)) — not this file (#39).

## Known product constraints (already in-repo; not a substitute for #43)

| Topic | Current honesty | Cite when #43 lands |
|-------|-----------------|---------------------|
| Power | ~12 W dual drivers (C4 / SPEC) | Official Anker page |
| Ultrasonic 17–23 kHz | Expect AAC/SBC + BassUp/DSP roll-off | Lab FR / manufacturer FR |
| 10–20 Hz TX | Typically **na** on A2DP path; gate `lfDriveCapable` | Manufacturer LF claim if any |
| Volume blast | App vol→100 still limited by BT absolute volume + hardware | Rated SPL / impedance |

## Native wiring

`SoundcoreConstraints` in `native/IoTASP/Shared/Fleet/FleetConfig.swift` points here. UI picker defaults nodes 1–2 to `.soundcore2A2DP`.

## TODO

- [x] Official FR cited via #43 / PR #55 (70 Hz–20 kHz A3105 manual)
- [x] Longer table: [`soundcore-specs.md`](soundcore-specs.md)
