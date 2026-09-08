# Context7 baselines (Swift / Apple)

Verified resolve hits while authoring `awesome-swift-ios` (2026-09-07). Re-resolve before coding if IDs drift.

Sonos OSS (`soco-cli`, `sonos-web`) are scraped via Firecrawl, not Context7 — see `SKILL.md` Firecrawl section.

| Library ID | Trust / notes | Typical ASP query |
|------------|---------------|-------------------|
| `/websites/developer_apple_avfoundation` | Apple portal mirror | `AVAudioSession` `.playback`, AirPlay `policy: .longFormAudio`, `AVRouteDetector` |
| `/websites/developer_apple_corebluetooth` | Apple portal mirror | BLE vs Classic BR/EDR; not A2DP hop TX |
| `/swiftlang/swift-package-manager` | Official SPM | `Package.swift` `.package(url:from:)`, `.iOS(.vNN)` platforms |
| `/swiftlang/swift` | Language | concurrency / language baselines |

Example `Package.swift` dependency shape (from SPM docs):

```swift
dependencies: [
    .package(url: "https://github.com/apple/example-package-playingcard", from: "3.0.0"),
],
```

AirPlay-oriented session sketch (from AVFoundation docs — adapt; do not copy blindly into ASP):

```swift
let audioSession = AVAudioSession.sharedInstance()
try audioSession.setCategory(.playback, mode: .default, policy: .longFormAudio)
```
