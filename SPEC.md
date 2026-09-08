# Soundcore 2 — manufacturer specs (for HOP fleet)

Captured for the hop-ultrasonic public app. Primary source: Anker / soundcore product + support pages.

**Expanded dossier (issue [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43)):** [`docs/hardware/soundcore-specs.md`](docs/hardware/soundcore-specs.md) — A3105 details, BT 5.0/6.0 revision note, 2 vs 3 deltas, agent bullets, unknowns.

## Official claims (Anker / soundcore)

| Spec | Value | Source |
|------|-------|--------|
| Model | Soundcore 2 (**A3105**) portable Bluetooth speaker | [anker.com/ca/products/soundcore-2](https://www.anker.com/ca/products/soundcore-2), [soundcore.com](https://www.soundcore.com/products/soundcore-2) |
| Output power | **12 W** peak stereo (**6 W × 2**) | Product pages; [2 vs 3 support](https://service.soundcore.com/article-description/The-Main-Differences-Between-Soundcore-2-and-Soundcore-3-Speaker) |
| Drivers | Dual neodymium drivers + DSP (+ 1 passive radiator) | Same |
| Bass | BassUp + patented spiral bass port (low-end emphasis) | Same |
| Water resistance | **IPX7** | Same |
| Battery | **5,200 mAh**, up to **24 hours** playtime | Same |
| Bluetooth | **5.0** (Anker CA) / **6.0** on latest US revision (SN-dependent; no cross-TWS) | CA vs [soundcore.com](https://www.soundcore.com/products/soundcore-2) |
| App EQ | **None** (Soundcore 2) | Support 2 vs 3 |
| AUX-in | **Yes** (classic Soundcore 2) | Support 2 vs 3 |
| Frequency response | **Not listed** on product pages | Scrapes 2026-09-07 / 2026-09-08 |
| Codecs / max SPL / latency ms | **Not listed** (expect SBC; AAC possible on iOS) | Not on page |

Comparison table on the Anker CA page repeats: Output Power 12W · Water IPX7 · Playtime 24 Hours · Bluetooth Version 5.0.

## Relevance to 17–23 kHz ultrasonic carriers

1. **Bluetooth A2DP** (SBC/AAC) is built for music (~20 Hz–20 kHz at best) and applies psychoacoustic coding that **throws away or heavily quantizes near-ultrasonic energy**. Expect severe attenuation or total loss of 17–23 kHz through the BT link.
2. **Speaker DSP + BassUp** prioritize bass and “clarity” for speech/music — typically high-shelf / anti-alias / EQ that **rolls off treble** well below the hop band.
3. **Physical drivers** in a compact waterproof enclosure rarely reproduce >15–18 kHz at useful SPL even over AUX; over BT the codec is the first hard limit.
4. **Implication for HOP:** treat Soundcore 2 as a **loud near-field blaster for whatever survives the BT path**, not as a calibrated ultrasonic transducer. Prefer AUX if available for experiments; otherwise expect carriers to collapse. Systems-check in the app surfaces this warning.

## Fleet topology (app requirement)

- **2 nodes** paired **1:1** phone ↔ Bluetooth speaker (e.g. Soundcore 2).
- **Optional 3rd node:** phone chair-mounted for structure-borne / accelerometer-biased sensing.
- All nodes open the same public URL and may transmit concurrently (incoherent schedules — no shared seed).
- Algorithms: `hop` / `pulse` / `shriek`, optionally switched by vib class (accel vs acoustic).

## Capture method

- Firecrawl CLI scrapes of Anker CA + soundcore.com Soundcore 2 + support 2 vs 3 (2026-09-07 / 2026-09-08).
- Artifacts under local `.firecrawl/` (gitignored). Full citations: [`docs/hardware/soundcore-specs.md`](docs/hardware/soundcore-specs.md).
- No official FR curve / max-SPL / codec list published; product + support pages are the authoritative public listings used here.

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

Parked items (#4–#8, #10, #11, #14, #15, #18–#21, #23, #24) have specs too; see the index.
