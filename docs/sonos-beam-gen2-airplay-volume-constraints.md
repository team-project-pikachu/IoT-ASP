# Sonos Beam (Gen 2) — AirPlay volume / click-clip-static constraints

**Status:** field-backed policy (2026-09-08).  
**Path:** macOS / phone **AirPlay 2** → Beam Gen 2. This is **not** the primary SMAPI/UPnP “SetVolume-only” TX path; LAN SoCo/Control API volume is complementary.  
**Verified field sender:** **Apple Mac Studio (M4 Max)** → System Settings / Sound (AirPlay route) → Sonos Beam Gen 2. Prefer **macOS AirPlay / system-volume** semantics when interpreting OS % and headroom; iPhone/iPad AirPlay remains a supported path but was not the reporting node.  
**Related:** [sonos-beam.md](sonos-beam.md) · [SPEC.md](../SPEC.md) · [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) C4/C6 · issue [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39).  
**Evidence cache:** `.firecrawl/` (gitignored), Firecrawl CLI 2026-09-08.

## Symptom triad (operator field report)

Audible artifacts on **Mac Studio (M4 Max) → AirPlay → Sonos Beam Gen 2** when **macOS / AirPlay system volume** is pushed above roughly **~60%**, with IoT-ASP Web Audio (or native tone) already near full-scale:

| Symptom | What operators hear | Likely mechanism (engineering, not a Sonos published “60%” spec) |
|---------|---------------------|------------------------------------------------------------------|
| **Clicking** | Intermittent clicks / pops | Hard digital overs, limiter edge hits, or abrupt gain discontinuities |
| **Clipping** | Harsh overload / flat tops | PCM/AAC path exceeding full-scale into receiver amp/DSP |
| **Staticky / crackle** | Harsh static, crackle, “bit-crush” grit | Classic digital overload / aggressive limiting artifacts on overs |

All three are treated as **real audible defects**, not UI layout “warping.” Prefer mitigations that **prevent digital full-scale overload on the AirPlay send path** (headroom / lower max mapped peak / soft-clip avoidance) — **not** EQ gimmicks.

## What “~60%” is (and is not)

| Claim | Status |
|-------|--------|
| Sonos publishes “Beam Gen 2 clips / goes static above 60% volume” | **Not found** in official Beam guide, AirPlay support article, or Control API docs scraped 2026-09-08 |
| Sonos Control / player volume is an integer **0–100** | **Official** (see below) |
| Beam Gen 2 supports **AirPlay 2** (iOS 11.4+) | **Official** |
| Night Sound / Speech Enhancement / Loudness reshape dynamics | **Official** — leave **OFF** for clean scientific TX |
| **Volume Limit** maps UI 100% → a chosen max on the 0–100 scale | **Official** |
| Clicking + clipping + **staticky/crackle** above ~60% macOS/AirPlay volume with FS digital content | **Field report** (**Mac Studio M4 Max → AirPlay → Beam Gen 2**) — treated as **gain-staging / digital overs / hard limiting**, not a UI layout bug |

Do **not** invent a manufacturer “60% max SPL” number. The IoT-ASP **0.60 peak** constant is a **software headroom policy** aligned with that field threshold and with prior UI history (`max="60"` in older public slider docs).

## Manufacturer / Apple constraints (cited)

### Beam Gen 2 hardware & AirPlay (Sonos guide)

From [Sonos Beam user guide](https://www.sonos.com/en-us/guides/beam) (2026-09-08 scrape):

| Spec | Official claim |
|------|----------------|
| Amplifiers | **Five Class-D** digital amplifiers |
| Drivers | One tweeter + four elliptical midwoofers (shop/guide family) |
| Apple AirPlay 2 | Works with AirPlay 2 on Apple devices **iOS 11.4 and higher** |
| EQ | Bass, treble, **loudness** adjustable in Sonos app |
| Trueplay | Room tuning (iOS) |
| Speech enhancement | Home-theater dialogue clarity |
| Night sound | Enhances quiet sounds; **reduces intensity of loud sounds** |
| **Volume Limit** | Per-room maximum volume in Sonos app ([faq → Volume Limit](https://faq.sonos.com/maxvol)) |
| Published max SPL / wattage / FR curve | **Not published** on guide/shop pages scraped — do not invent |

### AirPlay streaming to Sonos (support)

[Stream AirPlay audio to Sonos](https://support.sonos.com/en-us/article/stream-airplay-audio-to-sonos):

- AirPlay 2 from devices listed in [Apple HT208728](https://support.apple.com/HT208728).
- macOS may also use AirPlay 1 for system audio; Sonos notes possible **delay or audio interruptions** on that path.
- Route via Control Center (iOS) or **System Settings → Sound → Output** (Mac).
- Beam is on the AirPlay-compatible product list (guide + support).
- AirPlay unavailable while the source device is on a phone call; surrounds cannot be AirPlay targets.

**Implication:** IoT-ASP TX is **OS-owned AirPlay audio**. Volume heard is the product of **(digital sample peak) × (AirPlay/OS output volume) × (Sonos player / group volume / DSP)**.

### Control API volume semantics (0–100) — complementary, not the TX codec

Official Control API (not the AirPlay PCM/AAC path, but the same household volume scale):

- [`playerVolume.volume`](https://docs.sonos.com/reference/playervolume-object): number **between 0 and 100**.
- [`setVolume`](https://docs.sonos.com/reference/playervolume-setvolume-playerid): `volume` integer **minimum 0, maximum 100**; values above range rejected; negatives → 0.
- **Fixed volume** players reject `setVolume` (`ERROR_COMMAND_FAILED`) — e.g. CONNECT fixed line-out. Beam is normally changeable unless limited.
- Group `setRelativeVolume` / `setVolume` are for intentional controller UX; **do not** mute by `setVolume(0)` if relative levels must be preserved (group mute docs).

LAN tools (SoCo / sonos-web) use the same 0–100 UPnP/Control scale for clamps — see [sonos-beam.md](sonos-beam.md).

### Volume Limit (Sonos app)

[Setting a volume limit on Sonos products](https://support.sonos.com/en-us/article/setting-a-volume-limit-on-sonos-products):

- Limit is on a **0–100** scale per product.
- UI may still show a full slider; at limit 50%, “100%” UI outputs **50%**.
- Applies to line-in autoplay and alarms (article). Treat as a **hardware-side safety cap** usable beside IoT-ASP software headroom.

### Night Sound / Speech / Loudness

- [Night Sound](https://support.sonos.com/en-us/article/reduce-loud-tv-audio-with-night-sound): reduces intensity of loud sounds / raises quiet — **dynamic compression**, not clean FS TX.
- Speech Enhancement / Loudness: reshape dialogue / equal-loudness curve — **OFF** for scientific carriers ([SPEC.md](../SPEC.md)).

### Apple AirPlay / session notes

- App route picking: [Supporting AirPlay in your app](https://developer.apple.com/documentation/avfoundation/supporting-airplay-in-your-app); fleet uses `AVRoutePickerView` + `.longFormAudio` ([native/ios-sonos-shell](../native/ios-sonos-shell/), [ASPAudioSession](../native/IoTASP/Shared/Audio/ASPAudioSession.swift)).
- System `AVAudioSession.outputVolume` is the **device output volume** (0…1) the OS applies on the active route — including AirPlay when selected. Apple docs do not publish a Beam-specific clip threshold.
- Near-ultrasonic / FS sines through Web Audio → OS → AirPlay (often AAC-family encoding on AirPlay 2) can **hard-limit or produce transient overs** when peaks sit at ±1.0 **and** the receiver volume is high. That matches **audible clicks**, not soft “warped UI.”

### Community / engineering (non-manufacturer)

Firecrawl search (2026-09-08) surfaces Sonos Community threads on **Beam Gen 2 distortion** and **AirPlay 2 initial volume too high** — useful as existence proof of volume/AirPlay sensitivity, **not** as a calibrated 60% spec. Prefer official docs above for policy numbers.

## Gain stack (why click / clip / static appear above ~60%)

```
Web Audio / AVAudioEngine peak  ×  OS AirPlay volume (0–1)  ×  Sonos player volume (0–100)  ×  DSP (Night/Speech/Loudness/Trueplay)
         ↑ C4 wants “max”              ↑ user hears “~60%”              ↑ Control API / app              ↑ leave OFF
```

Prior IoT-ASP copy said: keep Web Audio at **100%** **and** raise **OS + Sonos volume to max**. That **double-stacks** full-scale digital content into the Beam amp/DSP and is the leading hypothesis for **audible clicking, clipping, and staticky/crackle** once OS/AirPlay volume exceeds the field-safe region (~60%).

Secondary click mechanisms (any volume): abrupt `AudioParam` discontinuities (zipper), AirPlay buffer underruns. Prefer smooth ramps; underruns are less likely if the artifact **tracks volume**. Do **not** “fix” static with EQ — fix send-path headroom.

## IoT-ASP policy (fix)

| Layer | Policy |
|-------|--------|
| UI / patch `VOL_PATCH_MAX` | Remains **100** (C4) — “max practical Web Audio request” |
| Digital peak when `audioSink === "sonos-beam-2"` | **`AIRPLAY_BEAM_PEAK = 0.60`** (−4.4 dBFS) via `level()` — maps 100% UI → non-FS PCM peak |
| OS / AirPlay volume | Prefer **≤ ~60%** until systems-check proves higher is clean **or** Sonos **Volume Limit** is set |
| Sonos player volume | Raise for SPL **after** digital headroom; optional Volume Limit ≤60–70 as hardware guard |
| Night Sound / Speech / Loudness / Trueplay | **OFF** / flat for clean TX |
| Native AirPlay shell | Same peak (`BeamAirPlayHeadroom.peakGain` / mixer `outputVolume` 0.60) |

Constant location: `public/index.html` (`AIRPLAY_BEAM_PEAK`) and `native/IoTASP/Shared/Audio/BeamAirPlayHeadroom.swift`.

## How to verify on Beam Gen 2

1. On **Mac Studio (M4 Max)** (primary field path): **System Settings → Sound → Output** → Beam via **AirPlay 2**. (iPhone Control Center AirPlay is OK for parity, not the verified reporter.) Night Sound / Speech / Loudness **OFF**.
2. Signal on (hop or stub tone). Confirm UI still shows **100%** but dBFS ≈ **−4.4** (web) when Beam sink is active.
3. Sweep **macOS / AirPlay** system volume **40% → 100%**. Expect **no clicks, clips, or harsh static/crackle** through the former ~60% cliff.
4. Negative control: temporarily force peak `1.0` (dev only) and confirm click/clip/**static** return near high OS volume — proves headroom, not “speaker broken.”
5. Optional: Sonos app **Volume Limit** at 60; confirm UI 100% cannot exceed that acoustic ceiling.

## Sources (primary)

- https://www.sonos.com/en-us/guides/beam  
- https://support.sonos.com/en-us/article/stream-airplay-audio-to-sonos  
- https://support.sonos.com/en-us/article/setting-a-volume-limit-on-sonos-products  
- https://support.sonos.com/en-us/article/reduce-loud-tv-audio-with-night-sound  
- https://docs.sonos.com/reference/playervolume-object  
- https://docs.sonos.com/reference/playervolume-setvolume-playerid  
- https://developer.apple.com/documentation/avfoundation/supporting-airplay-in-your-app  
- https://support.apple.com/HT208728  

Scraped locally under `.firecrawl/` (not committed).
