# Fleet audio — Sonos Beam (Gen 2) primary + Soundcore 2 phone BT

Primary public sink for hop-ultrasonic on Mac Studio / desktop: **Sonos Beam (Gen 2)** via
**OS system audio** (macOS Sound / AirPlay / Control Center). **Not** Web Bluetooth.

## Sonos Beam (Gen 2) — official claims + AirPlay clean level

Sources (2026-09-08 Firecrawl scrape):

- User guide: <https://www.sonos.com/en-us/guides/beam>
- Product / tech: <https://www.sonos.com/en-us/shop/beam>
- Night Sound FAQ: <https://faq.sonos.com/nightsound>
- Speech Enhancement FAQ: <https://faq.sonos.com/tvspeech>
- EQ / loudness FAQ: <https://faq.sonos.com/eqsettings>
- AirPlay volume constraints (fleet): [`docs/sonos-beam-gen2-airplay-volume-constraints.md`](docs/sonos-beam-gen2-airplay-volume-constraints.md)

| Spec | Official claim | Implication for HOP |
|------|----------------|---------------------|
| Amplifiers | **Five Class-D** digital amplifiers | Plant can be loud; still software-limited by Sonos DSP |
| Drivers | **One tweeter** + **four elliptical midwoofers** (shop) | No published ultrasonic FR; 17–23 kHz experimental |
| EQ | Bass, treble, **loudness** adjustable in Sonos app | Loudness warps curve — **OFF** for scientific TX |
| Trueplay | Room EQ tuning (iOS) | Reshapes response — prefer **OFF** / flat for TX honesty |
| Speech Enhancement | Clarifies TV dialogue | Dynamic speech DSP — **OFF** for clean carriers |
| Night Sound | Enhances quiet sounds; **reduces intensity of loud sounds** | Compression at “loud” — **OFF** for clean TX |
| Volume Limit | Per-room max on **0–100** scale (Sonos app) | Optional hardware guard beside software headroom |
| SPL / wattage / FR curve | **Not published** on guide/shop pages scraped | Do **not** invent numbers |

**Field symptom (AirPlay):** on **Mac Studio (M4 Max) → AirPlay → Beam Gen 2**, clicking + clipping + **staticky/crackle** above ~60% macOS/AirPlay system volume with near-FS digital content — **not** a Sonos-published 60% spec.

**Max clean AirPlay policy:** Web Audio / `VOL_PATCH_MAX` = **100%** UI (C4); Beam sink digital peak `AIRPLAY_BEAM_PEAK = 0.40` (−8.0 dBFS); prefer OS/AirPlay ≤~60% or Sonos Volume Limit; Night Sound / Speech / Loudness **OFF**; EQ flat; **do not** stack FS Web Audio with max OS + max Sonos volume.

Public TX band is **17–23 kHz only** (optional 10–20 Hz UI removed from the control surface).

---

# Soundcore 2 — manufacturer specs (for HOP fleet)

Captured for the hop-ultrasonic public app. Primary marketing source: Anker Canada product page.
Official frequency-response band comes from the Anker A3105 owner's-manual spec table (not the marketing page).
First-class A2DP sink for **nodes 1–2** (iPhone 16 fleet). Node 3 is a distinct AirPlay/Sonos path ([#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39)).

Issue spec: [`docs/specs/43-soundcore-2-a2dp.md`](docs/specs/43-soundcore-2-a2dp.md).

## Official claims (Anker / soundcore)

| Spec | Value | Source |
|------|-------|--------|
| Model | Soundcore 2 (portable Bluetooth speaker), A3105 | [anker.com/ca/products/soundcore-2](https://www.anker.com/ca/products/soundcore-2) |
| Output power | **12 W** peak (stereo); manual row **12W+** | Marketing page + A3105 spec table |
| Drivers | Dual neodymium + DSP (marketing); **1.5" × 2** full-range (manual) | Same |
| Bass | BassUp + patented spiral bass port (low-end emphasis) | Marketing page |
| Water resistance | **IPX7** | Marketing page + manual |
| Battery | **5,200 mAh**, up to **24 hours** playtime | Marketing page |
| Bluetooth | Marketing comparison table **5.0**; newer official manuals / JP store / 2026 support PDFs **V6.0** | Anker CA comparison table + A3105 manuals / support PDFs / JP store (confirm revision on the unit) |
| Frequency response | **Not listed** on the product page (2026-09-07 scrape) | Marketing page |
| Frequency response (manual) | **70 Hz – 20 kHz** | A3105 owner's-manual spec table |
| Codecs | **Not listed** (typical iOS A2DP path: AAC with SBC fallback — inference, not a manufacturer claim) | Not on page or manual |

Comparison table on the Anker CA page repeats: Output Power 12W · Water IPX7 · Playtime 24 Hours · Bluetooth Version 5.0.

## Relevance to 17–23 kHz ultrasonic carriers

1. **Manufacturer FR ceiling is 20 kHz.** The hop band **17–23 kHz** sits on/above that published top. Treat anything above 20 kHz as outside the official box.
2. **Bluetooth A2DP** (SBC/AAC) is built for music (~20 Hz–20 kHz at best) and applies psychoacoustic coding that **throws away or heavily quantizes near-ultrasonic energy**. Expect severe attenuation or total loss of 17–23 kHz through the BT link.
3. **Speaker DSP + BassUp** prioritize bass and “clarity” for speech/music — typically high-shelf / anti-alias / EQ that **rolls off treble** well below the hop band.
4. **Physical drivers** in a compact waterproof enclosure rarely reproduce >15–18 kHz at useful SPL even over AUX; over BT the codec is the first hard limit.
5. **Implication for HOP:** treat Soundcore 2 as a **loud near-field blaster for whatever survives the BT path**, not as a calibrated ultrasonic transducer. Prefer AUX if available for experiments; otherwise expect carriers to collapse. Systems-check in the app surfaces this warning.

## 10–20 Hz LF drive (C6) — public UI removed; Soundcore path na

The published FR floor is **70 Hz**. Optional LF drive **10–20 Hz** is below that floor and below typical BT-speaker HPFs / BassUp tuning. On the Soundcore 2 A2DP path LF TX is **na**. The public hop-ultrasonic UI no longer offers a 10–20 Hz arm control; telemetry stays `band=17-23k` with `lfArmed`/`lfDriveCapable` false. Do not claim infrasound playback from this sink ([#18](https://github.com/team-project-pikachu/IoT-ASP/issues/18), [#25](https://github.com/team-project-pikachu/IoT-ASP/issues/25)).

## Volume blast vs rated 12 W (C4)

Web Audio gain is **locked at 100%** (`VOL_PATCH_MAX`; no UI attenuator). That is **not** the same quantity as the speaker's rated **12 W** output. Bluetooth absolute volume, DSP limiter, and the 12 W electrical/acoustic rating still cap real SPL. Raise phone + Soundcore hardware volume separately if the plant must get louder. Hold / Manual still wins over remote / impulse blast apply.

## Fleet topology (app requirement)

- **Mac Studio / desktop:** OS system audio → **Sonos Beam (Gen 2)** (AirPlay / Sound settings).
- **Phone nodes:** may still pair **1:1** via native Bluetooth A2DP to Soundcore 2 (C1) or AirPlay to Beam.
- **Optional chair node:** structure-borne / accelerometer-biased sensing ([#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) / [#120](https://github.com/team-project-pikachu/IoT-ASP/issues/120)).
- All nodes open the same public URL and may transmit concurrently (incoherent schedules — no shared seed).
- Algorithms: `hop` / `pulse` / `shriek`, optionally switched by vib class (accel vs acoustic).
- TX band: **17–23 kHz only**.

## Capture method

- Firecrawl CLI scrape of `https://www.anker.com/ca/products/soundcore-2` (2026-09-07). Artifact: `.firecrawl/scrape_-20260907T225729Z.json` (local cache).
- 2026-09-08 follow-up (#43): official A3105 spec table supplies **70 Hz – 20 kHz**. Marketing pages still do **not** list FR or codecs. No official 1/3-octave FR curve found.

## Feature specs

One spec per Project 5 issue lives in [`docs/specs/`](docs/specs/) — index, status per issue, owner
surface, and the list of docs that exist only on the owner's Mac clone: [`docs/specs/README.md`](docs/specs/README.md).
Wire fields stay canonical in [`docs/api-contract.md`](docs/api-contract.md).

Open, non-parked items:

| Issue | Spec |
|-------|------|
| #1 — M0 public Vercel hop blaster (shipped) + telemetry fields + M0 polish | [docs/specs/01-m0-public-blaster.md](docs/specs/01-m0-public-blaster.md) |
| #2 — Max-entropy seeds + decoherent coverage | [docs/specs/02-max-entropy-seeds.md](docs/specs/02-max-entropy-seeds.md) |
| #3 — Continuous polling & monitoring watchdog | [docs/specs/03-continuous-monitoring-watchdog.md](docs/specs/03-continuous-monitoring-watchdog.md) |
| #22 — Structured fleet telemetry logs | [docs/specs/22-structured-fleet-logs.md](docs/specs/22-structured-fleet-logs.md) |
| #25 — HW-limited: LF mic/TX + AEC for `soundBurst` `micDiff` | [docs/specs/25-hw-limited-lf-aec-micdiff.md](docs/specs/25-hw-limited-lf-aec-micdiff.md) |
| #26 — Colab live GCS: accel / gyro / `micDiff` telemetry → `meta/features` | [docs/specs/26-colab-live-gcs-features.md](docs/specs/26-colab-live-gcs-features.md) |
| #27 — Continuous ship: GitHub Actions dev → test → prod into Vercel | [docs/specs/27-continuous-ship-dev-test-prod.md](docs/specs/27-continuous-ship-dev-test-prod.md) |
| #43 — Soundcore 2 manufacturer specs (A2DP fleet constraints) | [docs/specs/43-soundcore-2-a2dp.md](docs/specs/43-soundcore-2-a2dp.md) |

Parked items (#4–#8, #10, #11, #14, #15, #18–#21, #23, #24) have specs too; see the index.
