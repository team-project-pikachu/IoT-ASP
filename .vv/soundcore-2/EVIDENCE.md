# Soundcore 2 manufacturer specs (evidence)

**Config item:** `SPEC.md` + `docs/specs/43-soundcore-2-a2dp.md`  
**Issue:** #43  
**Date:** 2026-09-08 (UTC)  
**Environment:** docs-only; no hardware on the bench this pass  
**Secrets:** none  
**Site PII:** none

## Procedure

1. Read existing `SPEC.md` official-claims table (Anker CA scrape 2026-09-07): FR and codecs marked Not listed.
2. Re-read official marketing pages: `https://www.anker.com/ca/products/soundcore-2`, `https://www.soundcore.com/products/soundcore-2`.
3. Read Anker A3105 owner's-manual spec tables (ManualsLib + Anker support PDFs).
4. Wire 70 Hz–20 kHz / 12 W / codec-unpublished / BT 5.0-vs-6.0 into `SPEC.md`, `docs/iphone-bluetooth.md`, `docs/native-xcode.md`.
5. Offline gate: `python3 -m pytest tests/test_soundcore_specs.py -q`.

## Observed (official sources only)

| Claim | Marketing pages | A3105 manual / support PDF |
|-------|-----------------|----------------------------|
| Output power | 12 W peak / "12W of pure audio power" | 12W+ |
| Drivers | dual neodymium + DSP | 1.5" × 2 full-range |
| Bass | BassUp + spiral bass port | (marketing feature; not a separate manual row) |
| FR | **Not listed** | **70 Hz – 20 kHz** |
| Codecs | **Not listed** | **Not listed** |
| Bluetooth | 5.0 on CA/US comparison table; some soundcore.com copy 6.0 | V5.0 older print; V6.0 newer PDFs / JP store |
| IP / battery | IPX7, 5,200 mAh, up to 24 h | IPX7, up to 24 h |

## Pass / fail

| ID | Result |
|----|--------|
| SC-01 FR cited from manual | pass (docs + test) |
| SC-02 marketing still "not listed" | pass |
| SC-03 17–23 kHz honesty | pass |
| SC-04 10–20 Hz na | pass |
| SC-05 12 W ≠ Web Audio 100% | pass |
| SC-10 codecs unpublished | pass |

## Honesty leftovers

- No official 1/3-octave FR curve.
- No official codec list (do not claim aptX).
- Fleet unit BT 5.0 vs 6.0 not confirmed on hardware this pass.
