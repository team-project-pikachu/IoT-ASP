# Sonos Beam Gen 2 — Node 3 audio sink (research, issue #39)

**Status:** parked research until Beam Gen 2 hardware is in hand for systems check.  
**Board:** [Project 5](https://github.com/orgs/team-project-pikachu/projects/5) · issue [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39).  
**Formal constraint:** [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) **C1** requires **iOS native Bluetooth A2DP** for carrier TX (not Web Bluetooth). **AirPlay 2 to Beam is a researched exception** — OS-owned route, but **not** currently C1-compliant A2DP; do not treat this doc as revising C1.  
**Evidence cache:** `.firecrawl/` (gitignored) from Firecrawl search/scrape; Apple API notes via Context7 `/websites/developer_apple_avfaudio` + [Apple Developer Documentation](https://developer.apple.com/documentation/).  
**Agent skill priors:** [skills-repo PR #1](https://github.com/team-project-pikachu/skills-repo/pull/1) (`awesome-swift-ios` + SoCo CLI + sonos-web) — install via `bearlabs-core@bearlabs` marketplace.

## Fleet role — Node 3

| Node | Device | Sink | Primary phone→speaker path |
|------|--------|------|----------------------------|
| 1–2 | iPhone 16 (fleet) | Soundcore 2 | **iOS native A2DP** (C1 MVP) |
| **3** | **Third iPhone 16** | **Sonos Beam Gen 2** | **AirPlay 2** (researched C1 exception — not A2DP) |

Node 3 is the **third-device** path: one dedicated iPhone 16 paired/routed to the Beam for ASP scientific tooling alongside (not instead of) phones 1–2. Chair-taped Node-3 sensing (#18) remains a separate bias; this doc is the **Sonos audio sink** research for that third phone.

## Routing conclusion (honesty)

**Prefer AirPlay 2. Do not assume A2DP stereo-sink parity with Soundcore.**

| Claim | Finding | Sources |
|-------|---------|---------|
| Phone BT A2DP sink | Beam Gen 2 is **not** a generic iPhone Bluetooth stereo sink for Web Audio hop-blasting | Official guide lists Wi‑Fi + AirPlay 2 + HDMI eARC; RTINGS: wireless phone streaming is Wi‑Fi / no Bluetooth support; Sonos community threads treat Beam as non-BT |
| AirPlay 2 | Supported on Beam Gen 2 (iOS 11.4+) — Control Center / app AirPlay picker routes iPhone system audio to Sonos | [Sonos Beam Gen 2 guide](https://www.sonos.com/en-us/guides/beam), [Stream AirPlay to Sonos](https://support.sonos.com/en-us/article/stream-airplay-audio-to-sonos) |
| Safari / Chrome iOS PWA | Still cannot pick BT/AirPlay devices in-page; user must set **OS route** (Control Center AirPlay) before/during Web Audio TX | Same OS-route pattern as C1 A2DP, but AirPlay itself remains a **C1 exception** until DESIGN_CONSTRAINTS is revised; see [iphone-bluetooth.md](iphone-bluetooth.md) |
| Dolby Atmos | Hardware/marketing Atmos is primarily **HDMI eARC** (and selected Sonos/app music paths). **iPhone AirPlay of Web Audio is effectively stereo** — do not treat Atmos as an ASP transport feature | Sonos Atmos notes; community: Atmos via AirPlay from phone is unreliable / often stereo |
| Official Sonos Control API | Cloud Control API (OAuth) for household/groups/volume — complementary to LAN tools; does **not** replace AirPlay for phone Web Audio TX | [About Control API](https://docs.sonos.com/reference/about-control-api) |

Shop marketing may show a “Bluetooth” badge in ecosystem feature grids; that is **not** evidence that Beam Gen 2 accepts iPhone A2DP like a Soundcore. Treat phone→Beam ASP TX as **AirPlay 2 over the LAN (Google Home Wi‑Fi)** until a hardware systems check proves otherwise.

## Third-device pairing / control (LAN)

These tools run on a machine on the **same LAN** as the Beam (Google Home Wi‑Fi). They **control** Sonos (volume, mute, grouping, queue, play/pause). They do **not** replace the phone’s native audio route for Web Audio hop blasting unless a future doc explicitly proves a SoCo-injected local file / clip path is the scientific TX path (parked; not MVP).

### SoCo CLI ([avantrec/soco-cli](https://github.com/avantrec/soco-cli))

- Python CLI over local UPnP (SoCo); **no Sonos cloud**.
- Install: `pip install -U soco-cli` or `pipx install soco-cli`.
- Shape: `sonos SPEAKER ACTION <params>` (alias `soco`).
- Examples (names are placeholders — use the Beam’s Sonos room name after discovery):

```bash
sonos-discover
sonos "Beam" volume
sonos "Beam" volume 40
sonos "Beam" mute off
sonos "Beam" status
```

Optional HTTP API server mode for scripted LAN ops. Fit for ASP: **deterministic volume/group clamps** beside the phone hop blaster; exit codes suitable for `cron` / CI-style scripts.

### sonos-web ([sonos-web/sonos-web](https://github.com/sonos-web/sonos-web))

- Browser controller via [node-sonos](https://github.com/bencevans/node-sonos).
- Install (host npm): `npm install -g sonos-web-cli` → `sonos-web install` → `http://localhost:5050`.
- **Docker caveat:** images typically need `network_mode: host` for Sonos discovery. Host networking was historically Linux-only on Docker Desktop; Docker Desktop 4.34+ documents opt-in host networking on Mac/Windows — **verify Sonos discovery on your host** rather than assuming it works. Prefer bare `sonos-web-cli` on macOS Studio, or a Linux box / Apple `container` Linux VM on the same Wi‑Fi as the Beam.

### Honesty boundary

```
iPhone 16 (Node 3)  --AirPlay 2-->  Beam Gen 2   ← carrier / Web Audio TX path
LAN host (SoCo / sonos-web)  --UPnP-->  Beam Gen 2   ← volume / group / queue control
```

SoCo / sonos-web **do not** satisfy C1 by themselves for the public hop blaster. AirPlay is an OS-owned route but **not** the formal C1 A2DP requirement — the blaster still needs a verified native/OS route, and Node 3 remains a parked exception until C1 is revised or Beam A2DP is proven.

## Native shell sketch (AirPlay picker)

Stub: [`native/ios-sonos-shell/`](../native/ios-sonos-shell/) — SwiftUI shell with `AVRoutePickerView` + `AVAudioSession` `.playback` / `.longFormAudio` (and explicit `.allowAirPlay` when using `playAndRecord`). Coexists with SoCo/sonos-web for LAN control.

Apple docs (cite):

- [AVRoutePickerView](https://developer.apple.com/documentation/avkit/avroutepickerview)
- [Supporting AirPlay in your app](https://developer.apple.com/documentation/avfoundation/supporting-airplay-in-your-app)
- [allowAirPlay](https://developer.apple.com/documentation/avfaudio/avaudiosession/categoryoptions-swift.struct/allowairplay)
- [allowBluetoothA2DP](https://developer.apple.com/documentation/avfaudio/avaudiosession/categoryoptions-swift.struct/allowbluetootha2dp) — relevant to Soundcore nodes 1–2, **not** Beam Gen 2 as sink

**Compile check (this machine):** `xcodebuild -version` reports Command Line Tools only (`active developer directory '/Library/Developer/CommandLineTools'`). Full Xcode.app is required to build the stub; treat sources as compile-ready sketches for Swift Playgrounds or Xcode on a Mac with Xcode installed.

## Acceptance (parked until HW)

- [ ] Systems check: iPhone 16 → Beam Gen 2 via **AirPlay 2**; confirm Web Audio carriers audible
- [ ] Negative control: Settings Bluetooth does **not** offer Beam as A2DP sink (or document exception if firmware changed)
- [ ] SoCo CLI: discover Beam on Google Home Wi‑Fi; set volume; does not interrupt AirPlay TX unexpectedly
- [ ] sonos-web (or SoCo) usable for grouping/mute without street PII in logs
- [ ] Atmos: document as **na** for ASP Web Audio AirPlay path



## Pre-arrival protocol (Balanced PR4 — no HW claim)

Until a Beam Gen 2 is on the bench, treat Node 3 as **research-only**:

1. Keep fleet defaults: nodes 1–2 Soundcore A2DP (C1); node 3 AirPlay enum only.
2. Shared package gate: with Xcode.app → `cd native/IoTASP && swift test`; on CLT-only → `swift build` + `swift Scripts/alarm_smoke.swift` (XCTest requires full Xcode).
3. Printable first-session checklist: [`native/IoTASP/SYSTEMS-CHECK.md`](../native/IoTASP/SYSTEMS-CHECK.md) — AirPlay labeled **C1 exception / non-compliant** (not MVP carrier TX).
4. Do **not** mark #39 Done or remove `parked` until AirPlay systems check boxes above are ticked on real hardware, and only after an explicit product decision if promoting AirPlay toward C1.

## Out of scope

- No street PII; no purchase/pricing claims (listing link only on #39)
- No Web Bluetooth / BLE GATT as carrier TX
- No assumption that Sonos cloud Control API is required for Node 3 MVP

## Related

- [iphone-bluetooth.md](iphone-bluetooth.md) — C1 A2DP MVP (nodes 1–2 Soundcore)
- [hardware/soundcore-2.md](hardware/soundcore-2.md) — Soundcore manufacturer TODO (#43)
- [native-xcode.md](native-xcode.md) — SensorKit / native shell (#9)
- [sensorkit-watch.md](sensorkit-watch.md) — iPhone+Watch vib / alarm (#41)
- [algorithms.md](algorithms.md) — impulse→blast / alarm state machine (#42)
- [connectivity-wifi.md](connectivity-wifi.md) — Google Home Wi‑Fi
- Specs index: [specs/README.md](specs/README.md) (Project 5 notes for #39 / #41 / #42)
- Native app: [`native/IoTASP/`](../native/IoTASP/) (fleet sink picker includes Sonos AirPlay)
- Skills: [skills-repo PR #1](https://github.com/team-project-pikachu/skills-repo/pull/1)
