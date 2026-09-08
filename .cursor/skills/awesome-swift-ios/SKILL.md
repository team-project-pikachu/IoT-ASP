---
name: awesome-swift-ios
description: >-
  Routes Swift/iOS and Sonos third-device work through awesome-swift, awesome-ios,
  Apple docs, soco-cli, sonos-web, Firecrawl prior-art search, and Context7 CLI
  before inventing native ASP/Sonos control. Use for Xcode shells, AVAudio/BT,
  AirPlay, or iPhone IoT-ASP sinks including Sonos Beam Gen 2 (#39).
---

## When to use this skill

Use before writing or inventing **native Swift/iOS** or **Sonos control** code for
IoT-ASP hop fleets, Bluetooth/AirPlay audio sinks, SensorKit/Xcode shells, or
Sonos/third-device phone pairing. Prefer curated awesome lists + Apple docs +
Sonos OSS priors + Firecrawl scrape over model recall.

# Awesome Swift / iOS / Sonos priors (Bear Labs)

Installed in-repo from [skills-repo PR #1](https://github.com/team-project-pikachu/skills-repo/pull/1)
(`.cursor/skills/awesome-swift-ios/` and `.claude/skills/awesome-swift-ios/`). Marketplace remains optional:

```
/plugin marketplace add team-project-pikachu/skills-repo
/plugin install bearlabs-core@bearlabs
```

## Canonical sources (do not redistribute wholesale)

| List / project | URL | Use for |
|------|-----|---------|
| awesome-swift | https://github.com/matteocrippa/awesome-swift | Swift libs: Bluetooth, Network, Audio, SwiftUI |
| awesome-ios | https://github.com/vsouza/awesome-ios | iOS ecosystem: Audio, Bluetooth, Media, Networking, AirPlay-related |
| soco-cli | https://github.com/avantrec/soco-cli | CLI control of Sonos speakers (SoCo); third-device pairing / discovery priors |
| sonos-web | https://github.com/sonos-web/sonos-web | Web UI for Sonos control; HTTP/control-plane patterns before inventing |

Prefer live GitHub README + Firecrawl scrape over stale workstation upload copies.

## Apple documentation portal

- Developer docs home: https://developer.apple.com/documentation/
- Key frameworks for ASP audio routing:
  - **AVFoundation** / `AVAudioSession` — playback category, AirPlay long-form policy, route detection
  - **Core Bluetooth** — BLE (+ limited Classic); **not** a substitute for A2DP carrier TX
  - **Swift Package Manager** — `Package.swift` dependencies for native shells

Context7 library IDs (resolve/query via `context7-cli-stable`):

| ID | Concept |
|----|---------|
| `/websites/developer_apple_avfoundation` | `AVAudioSession` playback, AirPlay `longFormAudio`, `AVRouteDetector` |
| `/websites/developer_apple_corebluetooth` | BLE / BR-EDR discovery limits vs system A2DP |
| `/swiftlang/swift-package-manager` | `Package.swift` deps + iOS platform floors |
| `/swiftlang/swift` | Language / concurrency baselines |

```bash
STABLE=~/.cursor/plugins/local/research-cli-kit/scripts/context7_stable.sh
bash "$STABLE" resolve "AVFoundation" "AVAudioSession Bluetooth A2DP"
bash "$STABLE" docs /websites/developer_apple_avfoundation "AVAudioSession category playback AirPlay longFormAudio"
bash "$STABLE" docs /websites/developer_apple_corebluetooth "Core Bluetooth Classic vs BLE audio"
bash "$STABLE" docs /swiftlang/swift-package-manager "Package.swift dependencies iOS platform"
```

If CLI docs are empty, fall back to Context7 MCP `query-docs` with the same library IDs (see `context7-cli-stable`).

## Firecrawl: search/scrape before inventing native ASP/Sonos code

**Invariant:** Do not invent native Swift/iOS ASP, Sonos control, or AirPlay bridging
code until Firecrawl has searched and (for promising hits) scraped priors —
including **soco-cli** and **sonos-web** when the work touches Sonos or third-device
pairing.

```bash
FC=~/.cursor/plugins/local/research-cli-kit/scripts/firecrawl_stable.sh
bash "$FC" search "iOS AVAudioSession allowBluetoothA2DP Web Audio Safari" --limit 8
bash "$FC" search "Sonos Beam Gen 2 AirPlay 2 vs A2DP iPhone" --limit 8
bash "$FC" developer "Swift CoreBluetooth BLE not A2DP audio sink" --limit 10
bash "$FC" scrape "https://github.com/matteocrippa/awesome-swift"
bash "$FC" scrape "https://github.com/vsouza/awesome-ios"
bash "$FC" scrape "https://github.com/avantrec/soco-cli"
bash "$FC" scrape "https://github.com/sonos-web/sonos-web"
bash "$FC" scrape "https://developer.apple.com/documentation/avfoundation/avaudiosession"
```

Cache under `.firecrawl/`. Prefer `developer` index for library/API bugs; `search` for product/route research.

### Sonos control priors (third-device pairing)

| Project | Role for agents |
|---------|-----------------|
| [avantrec/soco-cli](https://github.com/avantrec/soco-cli) | SoCo-based CLI: discover/group/play/volume on LAN Sonos. Firecrawl scrape README + usage **before** inventing discovery or control APIs. Useful as a research twin for “can we reach Beam Gen 2 on the LAN?” — not a substitute for C1 A2DP hop TX. |
| [sonos-web/sonos-web](https://github.com/sonos-web/sonos-web) | Browser UI over Sonos control plane. Firecrawl scrape architecture/API notes **before** inventing a web control surface alongside the ASP blaster PWA. |

Use these **alongside** awesome-swift / awesome-ios / Apple docs when evaluating AirPlay vs Sonos-app vs A2DP for issue #39. Do not vendor their code into IoT-ASP without an explicit dependency election.

### Awesome-list sections to open first

From **awesome-swift**: Bluetooth (CoreBluetooth wrappers), Audio (`SwiftAudioPlayer` / AVAudioEngine), Network.

From **awesome-ios**: Bluetooth, Media → Audio (`AudioKit`, players), Media Processing (`Airstream` AirPlay-related), Networking.

Treat list entries as **leads to evaluate**, not defaults to vendor into the product.

## IoT-ASP product context (iPhone fleet + Sonos #39)

- Repo: https://github.com/team-project-pikachu/IoT-ASP
- Issue: [Sonos Beam Gen 2 as ASP audio sink (iPhone 16 fleet)](https://github.com/team-project-pikachu/IoT-ASP/issues/39) — labels `enhancement`, `research`, `parked`
- Constraint **C1** today: **Web Audio + iOS native Bluetooth A2DP** (Safari/PWA). App cannot enumerate BT sinks.
- Sonos Beam Gen 2 commonly prefers **AirPlay 2**, Sonos app, and/or **HDMI eARC** — do **not** assume Soundcore-style A2DP hop-blaster parity.
- Web Audio path is effectively **stereo**; Dolby Atmos is hardware marketing, not a guaranteed ASP transport feature.
- Acceptance remains parked until Beam Gen 2 hardware is in hand.
- Native app: `native/IoTASP/`; research stub: `native/ios-sonos-shell/`; docs: `docs/sonos-beam.md`, `docs/native-xcode.md`, `docs/iphone-bluetooth.md`.

## Agent workflow (ordered)

1. **Read** issue #39 + C1 / `iphone-bluetooth.md` / `docs/sonos-beam.md` if touching audio sinks.
2. **Firecrawl** search + scrape awesome-swift, awesome-ios, **soco-cli**, **sonos-web**, and Apple AVAudioSession docs.
3. **Skim** awesome-list sections + Sonos OSS READMEs for candidate libraries/control patterns.
4. **Context7** (`context7-cli-stable`) for any Swift package or Apple framework API before coding.
5. **Apple docs** for session category, route policy, and BLE scope honesty.
6. Only then draft native/control code or research notes — document A2DP vs AirPlay vs Sonos LAN control vs eARC explicitly.

## Honesty gates

- CoreBluetooth ≠ classic A2DP stereo TX for ASP carriers.
- Safari MVP cannot pick BT devices; Control Center / system route owns the sink.
- **soco-cli** / **sonos-web** are LAN control-plane priors — they do not prove Beam Gen 2 A2DP hop-blaster parity with Soundcore.
- Do not commit purchase, pricing, or Atmos-over-BT claims.
- Do not vendor entire awesome-list or Sonos project READMEs into this skill or the product repo (links + section pointers only).
