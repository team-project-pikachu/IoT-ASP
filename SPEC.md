# Soundcore 2 — manufacturer specs (for HOP fleet)

Captured for the hop-ultrasonic public app. Primary source: Anker Canada product page.

## Official claims (Anker / soundcore)

| Spec | Value | Source |
|------|-------|--------|
| Model | Soundcore 2 (portable Bluetooth speaker) | [anker.com/ca/products/soundcore-2](https://www.anker.com/ca/products/soundcore-2) |
| Output power | **12 W** peak (stereo) | Same |
| Drivers | Dual neodymium drivers + digital signal processor (DSP) | Same |
| Bass | BassUp + patented spiral bass port (low-end emphasis) | Same |
| Water resistance | **IPX7** | Same |
| Battery | **5,200 mAh**, up to **24 hours** playtime | Same |
| Bluetooth | **5.0** (“ultra-stable”, extended range) | Same |
| Frequency response | **Not listed** on the product page | Same (2026-09-07 scrape) |
| Codecs | **Not listed** (typical BT speaker: SBC; AAC possible on iOS) | Not on page |

Comparison table on the same page repeats: Output Power 12W · Water IPX7 · Playtime 24 Hours · Bluetooth Version 5.0.

## Relevance to 17–23 kHz ultrasonic carriers

1. **Bluetooth A2DP** (SBC/AAC) is built for music (~20 Hz–20 kHz at best) and applies psychoacoustic coding that **throws away or heavily quantizes near-ultrasonic energy**. Expect severe attenuation or total loss of 17–23 kHz through the BT link.
2. **Speaker DSP + BassUp** prioritize bass and “clarity” for speech/music — typically high-shelf / anti-alias / EQ that **rolls off treble** well below the hop band.
3. **Physical drivers** in a compact waterproof enclosure rarely reproduce >15–18 kHz at useful SPL even over AUX; over BT the codec is the first hard limit.
4. **Implication for HOP:** treat Soundcore 2 as a **loud near-field blaster for whatever survives the BT path**, not as a calibrated ultrasonic transducer. Prefer AUX if available for experiments; otherwise expect carriers to collapse. Systems-check in the app surfaces this warning.

## Fleet topology (app requirement)

- **3 independent blasters:** 2× iPhone 16 + 1× iPhone 14, each paired **1:1** to its own Soundcore 2.
- All phones open the same public URL and transmit concurrently (incoherent hop schedules — no shared seed).

## Capture method

- Firecrawl CLI scrape of `https://www.anker.com/ca/products/soundcore-2` (2026-09-07).
- Artifact: `.firecrawl/scrape_-20260907T225729Z.json` (local cache).
- Manual/datasheet PDF search via Firecrawl returned no additional official FR curve; product page is the authoritative public listing used here.
