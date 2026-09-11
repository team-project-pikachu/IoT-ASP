# #22 — Structured fleet logs closeout

Date: 2026-09-11T13:13Z
Worker: iot-asp-issue-queue-drain
Branch: `queue/#22-fleet-log-hooks`

## Status

**Implemented and integrated on main.** No further product code required for #22 acceptance.

## What landed (verified on main SHA dab7afb1)

| Surface | Location |
|---------|----------|
| Enrich + PII scrub + band/power/nightNY/lf* | `services/autoroute-adk/iot_asp_autoroute/fleet_log.py` |
| Fixed-shape JSONL records + aggregate + retention | same module |
| 37 offline tests | `tests/test_fleet_log.py` |
| Spec | `docs/specs/22-structured-fleet-logs.md` |
| Wire rows + enrichment paragraph | `docs/api-contract.md` |
| **Integrator hooks (were the residual open item)** | `services/autoroute-adk/iot_asp_autoroute/tools.py` |

### tools.py hooks (already on main)

1. `ingest_telemetry`: `tel = fleet_log.enrich_telemetry(tel)` before `gcs_io.write_json`; then `fleet_log.write_log_record(..., log_record("info", "ingest", ...))`.
2. `process_sudden_freq`: `_log` helper emits `hold_refuse` / `skipped` / `patch_authored` / `patch_refused` after Hold check; write failures never raise into the decision path.
3. `fleet_log_summary(node_id, date=None)` → `aggregate_records(read_log_records(...))`.

## Invariants preserved

- `schemaVersion` remains `1` (additive tags only).
- `vol_hard_max` / soft max unchanged at 100.
- Hold / Manual still freezes remote patch apply before any log write.
- No API keys or Gemini credentials in `public/`.
- No site PII: `scrub_pii` runs before write; dropped values never logged.
- C1 native A2DP only; no Web Bluetooth TX.

## Residual / out of scope

- Live GCS writes remain env-gated (`IOT_ASP_GCS_BUCKET` / ADC); dry-run path is the CI default.
- Phone beacon may still omit `band`/`power`/`nightNY`/`lf*` — server always derives them.
- Colab live features path is #26 (owner-gated credentials).
- Hosted Vercel webhook receiver is #122 (separate).

## Verification notes

- Spec status text still said “integration hooks pending” from the original branch note; this closeout records that the hooks are present on main.
- No fabricated HW or live GCS results.
- Evidence only; no clamp/schema/wire break.
