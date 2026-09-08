# Soundcore / Anker — manufacturer specs (A2DP fleet)

**Status:** research complete for published claims; **FR / max SPL / codec list remain unpublished** by Anker for Soundcore 2.  
**Board:** [Project 5](https://github.com/orgs/team-project-pikachu/projects/5) · issue [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43).  
**Formal constraints:** [DESIGN_CONSTRAINTS.md](../DESIGN_CONSTRAINTS.md) **C1** (OS A2DP route), **C4** (volume), **C6** (LF gate).  
**Sibling sink:** [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) Sonos Beam Gen 2 is **AirPlay**, not this A2DP peer.  
**Root summary:** [`SPEC.md`](../../SPEC.md) (short table); this file is the expanded manufacturer dossier.  
**Evidence:** Firecrawl CLI scrapes 2026-09-07 / 2026-09-08 (local `.firecrawl/`, gitignored).

## Fleet model in use

Repo docs, `public/README.txt`, and the live hop UI all pin the A2DP nodes to **Soundcore 2** (SKU / model family **A3105**; product imagery uses `A3105015` / `A3105011` variants).

| Node | Phone | Sink | Path |
|------|-------|------|------|
| 1–2 | iPhone 16 | **Soundcore 2 (A3105)** | iOS **native Bluetooth A2DP** (Settings pair → Control Center route) |
| 3 (optional) | iPhone 14 / 16 | Soundcore 2 **or** Sonos Beam (#39) | A2DP vs AirPlay — do not conflate |

No other Soundcore SKU is named as fleet hardware in IoT-ASP issues/docs. Treat substitutions as **ask-ready** only (table below).

## Soundcore 2 (A3105) — official published specs

| Spec | Official value | Source |
|------|----------------|--------|
| Model / SKU | Soundcore 2 · **A3105** | [Anker CA product page](https://www.anker.com/ca/products/soundcore-2) (CDN assets `A3105015…`); support articles tag 【A3105】 |
| Output power | **12 W** peak stereo (**6 W × 2**) | Product pages (12 W); [Soundcore 2 vs 3 support](https://service.soundcore.com/article-description/The-Main-Differences-Between-Soundcore-2-and-Soundcore-3-Speaker) (6 W×2) |
| Drivers | Dual neodymium drivers + **DSP**; one passive radiator | Same product + support pages |
| Bass | **BassUp** + patented spiral bass port (LF emphasis) | [Anker CA](https://www.anker.com/ca/products/soundcore-2), [soundcore.com](https://www.soundcore.com/products/soundcore-2) |
| Water resistance | **IPX7** | Same |
| Battery | **5,200 mAh**, up to **24 h** playtime | Same |
| Bluetooth | **5.0** on Anker CA listing; **6.0** on current [soundcore.com](https://www.soundcore.com/products/soundcore-2) for “latest version” | **Model-revision dependent** — see note |
| A2DP sink | Yes (portable Bluetooth speaker; iOS pairs as stereo sink) | Product positioning; fleet uses OS A2DP ([iphone-bluetooth.md](../iphone-bluetooth.md)) |
| TWS / multi-speaker | **TWS** pair of **two** Soundcore 2 units (stereo / louder) | Product + [How to Pair Two Soundcore 2](https://service.soundcore.com/article-description/How-to-Pair-Two-Soundcore-2-Speakers-Together) |
| Multi-point (two phones) | **Not claimed** for Soundcore 2 | — |
| App EQ | **No** Soundcore app / EQ on Soundcore 2 | [2 vs 3 support](https://service.soundcore.com/article-description/The-Main-Differences-Between-Soundcore-2-and-Soundcore-3-Speaker) |
| AUX-in | **Yes** (classic Soundcore 2) | Same support article |
| Charge port | Classic: **Micro-USB**; newer store copy / reviews mention **USB-C** on BT 6.0 revision | Support (Micro-USB) vs current US PDP / user notes — **revision-dependent** |
| Frequency response | **Not published** by Anker/soundcore | Product pages (2026-09-08 scrapes) |
| Max SPL / sensitivity | **Not published** | Same |
| Codecs (SBC / AAC / LDAC / aptX) | **Not published** for Soundcore 2 | Same — expect consumer A2DP **SBC**; **AAC** possible when iOS negotiates it; **LDAC** is marketed on other Soundcore lines (e.g. comparison-table Hi-Res column), **not** claimed for Soundcore 2 |
| Latency (ms) | **Not published** as a number; US PDP markets BT 6.0 “improved stability and lower latency” | [soundcore.com Soundcore 2](https://www.soundcore.com/products/soundcore-2) |

### Bluetooth revision note (important)

- [Anker Canada Soundcore 2](https://www.anker.com/ca/products/soundcore-2) still lists **Bluetooth 5.0** in the comparison grid.
- [soundcore.com Soundcore 2](https://www.soundcore.com/products/soundcore-2) states the latest version uses **Bluetooth 6.0**, and **cannot TWS-pair with older (BT 5.0) units**; identify by serial number.
- For ASP agents: treat BT major version as **unit-dependent**. Codec/path behavior for hop carriers is dominated by **A2DP + BassUp/DSP**, not the 5.0 vs 6.0 marketing label.

### Soundcore 2 vs Soundcore 3 (official deltas)

From [soundcore support](https://service.soundcore.com/article-description/The-Main-Differences-Between-Soundcore-2-and-Soundcore-3-Speaker):

| | Soundcore 2 (fleet) | Soundcore 3 |
|--|---------------------|-------------|
| Drivers | Dual neodymium + 1 passive radiator | 2× 1.5″ titanium + 2 passive; HF unit marketed **up to 40 kHz** |
| Power | **6 W × 2** | **8 W × 2** |
| Multi-speaker | TWS (2 units) | PartyCast (100+) |
| App EQ | **None** | Soundcore app EQ |
| Charge | Micro-USB (classic) | USB-C |
| AUX | **Yes** | No |

Soundcore 3’s “up to 40 kHz” claim is **not** a Soundcore 2 FR curve and does **not** imply usable ultrasonic SPL over A2DP for the fleet units.

## ASP relevance (17–23 kHz and 10–20 Hz)

1. **A2DP codecs** (SBC/AAC) target music bandwidth (~20 Hz–20 kHz at best) and psychoacoustic coding that **discards or heavily quantizes near-ultrasonic energy**. Expect severe attenuation or loss of **17–23 kHz** hop carriers through the BT link.
2. **BassUp + DSP** emphasize low-end “clarity” for speech/music — typically high-shelf / anti-alias behavior that **rolls off treble** below the hop band.
3. **Physical drivers** in a compact IPX7 enclosure rarely reproduce >15–18 kHz at useful SPL even over AUX; over BT the codec is the first hard limit.
4. **10–20 Hz LF TX:** not in the music passband the product is designed for; treat as **`na`** on Soundcore/A2DP (`lfDriveCapable` false by default). Phone-speaker experimental path only when Systems check arms LF (#25 / #18).
5. **Volume ceiling:** utilize rated **~12 W** via max OS + speaker volume and app Web Audio gain **100%** (C4); BT absolute volume + DSP still cap real SPL — there is **no published max-SPL dB** figure.
6. **AUX experiment path:** Soundcore 2 has AUX-in per support — prefer AUX for FR experiments when a wired source is available; MVP fleet remains wireless A2DP.

## Agent bullets (iOS / Watch / web)

- **Playback path:** Web Audio → **iOS system A2DP** (Settings 1:1 pair + Control Center). No Web Bluetooth. Watch companion cannot substitute the phone’s A2DP route for hop TX.
- **Volume:** App clamp **100%** Web Audio; raise **phone BT absolute volume** and **Soundcore hardware volume** separately. Hardware ceiling ≈ **12 W** dual drivers — not calibrated SPL.
- **Band limits (implied, not measured FR):**
  - Default hop **17–23 kHz:** expect **roll-off / collapse** over A2DP + BassUp/DSP; systems-check must warn (see UI + `SPEC.md`).
  - Optional **10–20 Hz:** usually **`na`** on Soundcore/A2DP; do not claim infrasound TX.
- **EQ:** Soundcore 2 has **no app EQ** — no remote tone shaping via Soundcore app; any EQ is OS/DSP only.
- **Pairing:** 1 phone ↔ 1 speaker for fleet nodes; TWS dual-speaker mode is optional louder stereo, not multi-phone multi-point.
- **Sonos (#39):** Beam Gen 2 is a **different** Node-3 research path (AirPlay). Do not apply Soundcore A2DP assumptions to Sonos.

## Ask-ready Soundcore lines (not fleet-pinned)

From the Anker CA comparison grid on the [Soundcore 2 page](https://www.anker.com/ca/products/soundcore-2) (marketing columns; verify SKU before purchasing):

| Line (marketing) | Output (table) | BT (table) | Notes for ASP ask |
|------------------|----------------|------------|-------------------|
| Soundcore 2 | 12 W | 5.0 | **Fleet pin** |
| Motion / Boom-class portable | 20–80 W+ | 5.0–5.3 | Louder; still A2DP music path unless AUX/LDAC proven |
| Hi-Res / LDAC column | ~40 W | 5.3 | LDAC only if Android/source supports; **iPhone stays AAC/SBC** |
| Soundcore 3 | 16 W (8×2) | — | App EQ; HF marketing to 40 kHz; **no AUX** |

Earbud lines (Liberty / Sport / Sleep A40, etc.) are **not** ASP blast sinks for room hop; ignore unless a future issue explicitly adds them.

## Unknown / model-dependent (do not invent)

| Item | Status |
|------|--------|
| Official FR curve (Hz / dB) | **Unknown** — Anker does not publish for Soundcore 2 |
| Max SPL (dB @ 1 m) | **Unknown** |
| Negotiated codec on iPhone 16 | **Unit/OS-dependent** (typically AAC or SBC); not listed on product page |
| Exact BT 5.0 vs 6.0 on a given SN | **Revision-dependent** |
| Latency ms | **Unknown** (marketing only) |
| Useful ultrasonic SPL >17 kHz | **Unproven**; treat as collapsed unless measured |

## Capture method

- Firecrawl CLI scrape: `https://www.anker.com/ca/products/soundcore-2` (2026-09-07, 2026-09-08).
- Firecrawl CLI scrape: `https://www.soundcore.com/products/soundcore-2` (2026-09-08).
- Firecrawl CLI scrape: Soundcore support “Main Differences Between Soundcore 2 and Soundcore 3” (2026-09-08).
- Secondary lab reviews (e.g. RTINGS) exist but are **not** treated as manufacturer specs here; prefer official pages above.

## Related issues / docs

- [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43) — this dossier
- [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) — Sonos Beam Gen 2 (AirPlay Node 3)
- [#25](https://github.com/team-project-pikachu/IoT-ASP/issues/25) — HW-limited LF / AEC / `micDiff`
- [#1](https://github.com/team-project-pikachu/IoT-ASP/issues/1) — M0 public hop blaster
- [#18](https://github.com/team-project-pikachu/IoT-ASP/issues/18) — Node-3 chair / infrasound proxy
- [`docs/iphone-bluetooth.md`](../iphone-bluetooth.md) · [`docs/physics.md`](../physics.md) · [`docs/algorithms.md`](../algorithms.md)
