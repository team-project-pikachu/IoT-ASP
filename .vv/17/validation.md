# Issue #17 — Validation (right system)

| Check | Intent | Observed | Pass |
|-------|--------|----------|------|
| Val17-1 Contract alignment | Feature JSON carries the same heartbeat fields the phone beacons | Projected keys match api-contract sample (29 fields); aliases `a`/`ctxState` normalized | PASS |
| Val17-2 Shared detector | Colab must not fork a second anomaly algorithm | Notebook/docs import `iot_asp_autoroute.vib_anomaly` only | PASS |
| Val17-3 Seat / secret policy | 5-seat Gemini not called from public HTML; SA JSON never in git | Notebook gated `LIVE_GCS`; credential table lists **names**; frontend untouched this lane | PASS |
| Val17-4 Write authority | Colab must not become the patch writer | Docs + stub: suggestions only; `meta/patches/` ADK-only | PASS |
| Val17-5 Hold wins | Operator Hold/Manual blocks remote suggestion | Dry-run hold fixture refused | PASS |

**Not run this lane (deferred to integrate):** live Colab userdata GCS round-trip, Gemini Enterprise generateContent on seat, Vercel HTTP 200 (explicit non-goal for `exec-17-colab`).
