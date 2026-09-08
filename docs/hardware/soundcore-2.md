# Soundcore 2 — A2DP fleet sink (TODO manufacturer specs)

**Issue:** [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43)  
**Status:** Placeholder until official Anker/Soundcore sources are fetched and cited.  
**Fleet:** Nodes **1–2** = iPhone 16 ↔ Soundcore 2 over **iOS native A2DP** ([DESIGN_CONSTRAINTS.md](../DESIGN_CONSTRAINTS.md) **C1**). Node **3** = Sonos Beam AirPlay ([sonos-beam.md](../sonos-beam.md)).

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

- [ ] Firecrawl / fetch official Anker Soundcore 2 spec pages only
- [ ] Fill FR / codec / power table with citations
- [ ] Update `SPEC.md` cross-links if numbers change
