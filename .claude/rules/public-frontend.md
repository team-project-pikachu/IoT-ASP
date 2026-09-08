---
paths:
  - "public/**"
  - "vercel.json"
---

# Public static blaster (`public/`)

- Single-file PWA: `public/index.html` (CSS + HTML + one IIFE script). Keep it dependency-free; no bundler, no npm at repo root (Vercel serves `public/` statically per `vercel.json`).
- **Never** add Web Bluetooth, BLE GATT, or device pickers for the carrier path (C1). Audio out is Web Audio → iOS system A2DP route.
- **Never** embed API keys, Gemini/Vertex clients, or ADK logic. `scripts/ci_static_gates.sh` fails on `AIza…`, `sk-…`, `PRIVATE KEY`, `*_API_KEY = "…"`, `apiKey: "…"` patterns.
- Keep these literals intact: `Hold / Manual` (label), `holdManual` (wire key), `holdPatchBtn` (element id), `SCHEMA_VERSION = 1`.
- Telemetry payload (`telemetryPayload()`) is device metrics only — no geolocation, addresses, names, speech. New fields must be additive and documented in `docs/api-contract.md` + the feature spec.
- Remote patches apply through `clampPatch()` → `applyPatch()`; Hold / Manual short-circuits both `pollPatch()` and `applyPatch()`. Preserve that order.
- Web Audio rules: unlock `AudioContext` only on a user gesture; request 48 kHz; mic capture with `echoCancellation/noiseSuppression/autoGainControl: false`; never route mic to output (feedback).
- Hops are incoherent per tab (per-device seed → `mulberry32`). Do not introduce a shared/global seed.
- Owner's Mac (Cursor) is usually ahead of `origin/main` on this file. Put new logic in clearly delimited `// ══ … ══` blocks near the telemetry section so merges stay mechanical.
- Static checks live in `tests/test_public_html.py`; browser smoke in `tests/e2e/`.
