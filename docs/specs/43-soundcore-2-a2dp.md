# Spec: Soundcore 2 manufacturer specs (A2DP fleet constraints)

Issue: [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43)  
Board: [Project 5](https://github.com/orgs/team-project-pikachu/projects/5)

## Status

Docs research **landed on this branch**. Prefer official Anker/Soundcore pages and Anker support PDFs; ManualsLib is cited only as a **third-party HTML mirror** of the A3105 owner's manual when the PDF is awkward to deep-link.
No hardware re-measure. No wire-field changes. Does not block public hop redeploy.

## Goal

Treat Anker/Soundcore 2 as the first-class **A2DP fleet sink for nodes 1–2** (iPhone 16 ↔ speaker, constraint **C1**) and write manufacturer limits into native + Bluetooth docs:

- Official frequency-response / power / codec notes
- 17–23 kHz hop-band honesty
- 10–20 Hz LF drive gated **na** on this sink
- Volume-blast (C4 100% Web Audio) versus rated **12 W** speaker power

## Prior art

Searched in order: this repo → official Anker/Soundcore pages + A3105 manuals → org repos → no third-party FR curves as manufacturer claims.

Already here:

- Root [`SPEC.md`](../../SPEC.md) — marketing-page scrape (2026-09-07) marked FR/codecs **Not listed**
- [`docs/DESIGN_CONSTRAINTS.md`](../DESIGN_CONSTRAINTS.md) **C1 / C4 / C6**
- [`docs/iphone-bluetooth.md`](../iphone-bluetooth.md) — AAC/SBC typical; BT volume vs Web Audio 100%
- [`docs/native-xcode.md`](../native-xcode.md) — #9 parked shell; links this Soundcore FR honesty note
- [`reference/knowledge/acoustics-materials/soundcore-2-portable-bluetooth-speaker.md`](../../reference/knowledge/acoustics-materials/soundcore-2-portable-bluetooth-speaker.md)
- Node 3 is a **different path** (Sonos Beam / AirPlay, [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39))

Reuse `SPEC.md` as the manufacturer table. Do not invent codec support or an unpublished FR curve.

## Shipped on `main`

- `SPEC.md` official-claims table (model, 12 W peak, dual neodymium + DSP, BassUp, IPX7, 5,200 mAh / 24 h, Bluetooth 5.0 from the CA/US comparison table)
- C4: `VOL_PATCH_MAX` / UI 100% — Web Audio gain only
- C6: `lfDriveCapable` gate; Soundcore/A2DP typically **na** for 10–20 Hz
- Systems-check warning that 17–23 kHz collapses over BT

## Remaining scope (this spec)

1. Cite the **A3105 owner's-manual spec table**: frequency response **70 Hz – 20 kHz**, drivers **1.5" × 2** full-range, audio output **12W+**.
2. Record Bluetooth-version split: marketing comparison tables say **5.0**; newer official manuals / JP store / 2026 support PDFs say **V6.0**. Do not pick a fleet revision without the unit in hand.
3. Codecs remain **not listed** by Anker/Soundcore. iOS A2DP is typically AAC with SBC fallback — inference, not a manufacturer claim.
4. Wire honesty into `docs/iphone-bluetooth.md` and `docs/native-xcode.md` (replace the pre-landing TODO with this spec link).
5. Keep Node 3 / Sonos out of this table.

## Wire fields

None. Canonical telemetry stays [`docs/api-contract.md`](../api-contract.md). Optional existing tags `band=17-23k` / `band=10-20` are unchanged. `schemaVersion` stays **1**.

## Clamps / safety

- **C1** — iOS system A2DP only. No Web Bluetooth for carrier TX.
- **C4** — in-app vol ceiling stays 100 UI percent. Rated **12 W** is speaker electrical/acoustic marketing power, not a promise that Web Audio 100% delivers 12 W SPL.
- **C5** — Hold / Manual still freezes remote patches and blast apply.
- **C6** — 10–20 Hz stays gated; Soundcore published FR floor is **70 Hz** → LF TX on this sink is **na**.
- No site PII. No purchase/pricing claims.

## Acceptance tests

| ID | Check |
|----|--------|
| SC-01 | `SPEC.md` official-claims table lists FR **70 Hz – 20 kHz** with an Anker/Soundcore manual citation |
| SC-02 | `SPEC.md` still records marketing pages as **not listing** FR/codecs |
| SC-03 | `SPEC.md` states 17–23 kHz is on/above the published 20 kHz ceiling + A2DP/DSP roll-off |
| SC-04 | `SPEC.md` states 10–20 Hz is below the published 70 Hz floor → gated **na** |
| SC-05 | `SPEC.md` states C4 100% Web Audio ≠ rated 12 W SPL |
| SC-06 | `docs/iphone-bluetooth.md` links this spec and repeats 17–23 kHz / 10–20 Hz / 12 W honesty |
| SC-07 | `docs/native-xcode.md` links this spec for nodes 1–2 A2DP (no SensorKit entitlement invented) |
| SC-08 | This file has the eleven mandatory sections in order |
| SC-09 | `tests/test_soundcore_specs.py` covers SC-01…SC-08 (stdlib, offline) |
| SC-10 | Codecs row remains **Not listed** as a manufacturer claim |

## CI gate

- `python3 -m pytest tests/test_soundcore_specs.py -q`
- `python3 scripts/mdc_convert.py --check`
- PR must use `Fixes #43` (or Closes/Resolves). No `schemaVersion` bump. No secrets.

## Risks / HW limits

| Limit | Why | Mitigation |
|-------|-----|------------|
| No published FR *curve* | Manual gives a band, not 1/3-octave data | Treat 70 Hz–20 kHz as a box, not a calibrated response |
| 17–23 kHz hop band | Published ceiling 20 kHz; A2DP AAC/SBC + BassUp/DSP roll off earlier | Loud near-field blaster for whatever survives; not a US transducer |
| 10–20 Hz LF TX | Published floor 70 Hz + BT HPF | `lfDriveCapable` **na** on Soundcore A2DP |
| Codecs unpublished | Anker does not list SBC/AAC/aptX on product pages or A3105 tables | Infer iOS AAC/SBC only; never claim aptX |
| BT 5.0 vs 6.0 | Hardware revisions differ across official sources | Document both; confirm on the unit |
| Vol blast vs 12 W | C4 is Web Audio gain | Raise phone + speaker absolute volume separately |
| Node 3 | Sonos Beam is AirPlay, not this sink | [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) |

## Sources

- [Anker Canada — Soundcore 2](https://www.anker.com/ca/products/soundcore-2) (marketing; 12 W, BassUp, IPX7, 5,200 mAh, comparison table BT 5.0; no FR/codecs)
- [soundcore.com — Soundcore 2](https://www.soundcore.com/products/soundcore-2) (12 W peak, dual neodymium + DSP, BassUp, IPX7; some copy BT 6.0; no FR/codecs)
- A3105 owner's manual spec table (Anker): frequency response **70 Hz – 20 kHz**, audio output **12W+**, driver 1.5" × 2 full-range, BT V5.0 (older print) — primary: [Anker support PDF 000021515](https://salesforce-knowledge-download.s3.us-west-2.amazonaws.com/000021515/en_US/000021515.pdf) (same FR band); tertiary HTML mirror: [ManualsLib p.7](https://www.manualslib.com/manual/2149752/Anker-Soundcore-2.html?page=7)
- Newer Anker support PDF spec tables: same FR **70 Hz – 20 kHz**, BT **V6.0**, 12W+, IPX7 — e.g. [support PDF 000021515](https://salesforce-knowledge-download.s3.us-west-2.amazonaws.com/000021515/en_US/000021515.pdf)
- [Anker Japan A3105](https://www.ankerjapan.com/products/a3105) — 12 W, IPX7, Bluetooth 6.0 listing
- Constraints: [`docs/DESIGN_CONSTRAINTS.md`](../DESIGN_CONSTRAINTS.md) C1/C4/C6
- Related issues: #43, #9, #39, #25, #1
