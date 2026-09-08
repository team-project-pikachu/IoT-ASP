# Fleet audio sinks — Sonos Beam (Gen 2) + legacy Soundcore notes

Primary public sink for hop-ultrasonic: **Sonos Beam (Gen 2)** via **OS system audio**
(macOS Sound / AirPlay / Control Center). **Not** Web Bluetooth.

## Sonos Beam (Gen 2) — official claims (anti-warp / max clean level)

Sources (2026-09-08 Firecrawl scrape):

- User guide: <https://www.sonos.com/en-us/guides/beam>
- Product / tech: <https://www.sonos.com/en-us/shop/beam>
- Night Sound FAQ: <https://faq.sonos.com/nightsound>
- Speech Enhancement FAQ: <https://faq.sonos.com/tvspeech>
- EQ / loudness FAQ: <https://faq.sonos.com/eqsettings>

| Spec | Official claim | Implication for HOP |
|------|----------------|---------------------|
| Amplifiers | **Five Class-D** digital amplifiers | Plant can be loud; still software-limited by Sonos DSP |
| Drivers | **One tweeter** + **four elliptical midwoofers** (shop) | No published ultrasonic FR; 17–23 kHz experimental |
| EQ | Bass, treble, **loudness** adjustable in Sonos app | Loudness warps curve — **OFF** for scientific TX |
| Trueplay | Room EQ tuning (iOS) | Reshapes response — prefer **OFF** / flat for TX honesty |
| Speech Enhancement | Clarifies TV dialogue | Dynamic speech DSP — **OFF** for clean carriers |
| Night Sound | Enhances quiet sounds; **reduces intensity of loud sounds** | Compression / warping at “loud” — **OFF** for max clean TX |
| SPL / wattage / FR curve | **Not published** on guide/shop pages scraped | Do **not** invent numbers; raise OS + Sonos volume to max instead |

**Max practical level without warping (app policy):**

1. Web Audio out / `VOL_PATCH_MAX` = **100%** (C4) — no stacked digital boosts above 0 dBFS.
2. macOS / phone **system volume → max**; Sonos app volume → max.
3. Sonos app: **Night Sound OFF**, **Speech Enhancement OFF**, **Loudness OFF**, EQ flat; Trueplay optional but prefer off for repeatable science.
4. Expect AirPlay / Sonos DSP to still attenuate or erase **17–23 kHz** — treat as near-field experiment.

## Legacy Soundcore 2 (phone BT nodes)

Still valid for phone A2DP nodes. Anker A3105 manual FR **70 Hz – 20 kHz**; BassUp/DSP + AAC/SBC crush near-ultrasonic. Optional **10–20 Hz** public TX is **removed** (was C6).

## Fleet topology (app requirement)

- **Mac Studio / desktop + phones** open the same public URL.
- Pair **1:1** OS audio → **Sonos Beam (Gen 2)** (AirPlay / system output).
- Optional chair-mounted phone for structure-borne / accel sensing.
- Algorithms: `hop` / `pulse` / `shriek` (+ mirrors); incoherent per-tab RNG.
- TX band: **17–23 kHz only**.

## Capture method

- Firecrawl CLI scrape of Sonos Beam guide + shop (2026-09-08). Artifacts under `.firecrawl/sonos-beam-*.json`.
