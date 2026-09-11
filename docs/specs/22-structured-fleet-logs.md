# #22 — Structured fleet telemetry logs (awesome-inspired)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/22 · Milestone: M6

## Status

**Done on main (2026-09-11 closeout).** Module `services/autoroute-adk/iot_asp_autoroute/fleet_log.py` and `tests/test_fleet_log.py` (37 tests) ship on main. Integrator hooks in `tools.py` (`ingest_telemetry` enrich + log, `process_sudden_freq` decision records, `fleet_log_summary` tool) are present on main. `docs/api-contract.md` carries the five telemetry rows and the enrichment paragraph. Evidence: `.vv/22/fleet-log-hooks-closeout.md`.

The beacon in `public/index.html` may or may not emit `band`/`power`/`nightNY`/`lfArmed`/`lfDriveCapable` depending on checkout; this module treats those keys as **optional inputs** and always derives them server-side, so it is correct either way.

## Goal

Every telemetry heartbeat and every autoroute decision produces one **structured, PII-scrubbed, fixed-shape JSON Lines record** under `meta/logs/<node>/<YYYY-MM-DD>.jsonl`, enriched with the tags the fleet cares about (`band`, `power`, `nightNY`, `lfArmed`, `lfDriveCapable`, `lfGate`), plus a deterministic aggregator (`aggregate_records`) and a documented retention/aggregation plan that hands raw logs and aggregates to the Colab ETL (#17, #26) without ever touching `meta/patches/`.

"Awesome-inspired" = the observability conventions from the curated index (`docs/awesome-iot-asp.md`): one record per event, fixed key order, `kind` + `schemaVersion` discriminators, level enum, no free-form PII, date-partitioned JSONL, and a separate aggregate layer with explicit retention.

## Shipped on `main`

| What | Where |
|------|-------|
| `parse_ts` / `to_wire_ts` / `night_ny` (zoneinfo `America/New_York`) | `fleet_log.py` |
| `infer_band`, `is_pii_key`, `scrub_pii`, `enrich_telemetry` | same |
| `RECORD_KEYS`, `log_record`, `write_log_record`, `read_log_records`, `aggregate_records`, `retention_plan`, CLI `--demo` | same |
| Acceptance tests (37 cases) | `tests/test_fleet_log.py` |
| `ingest_telemetry` enrich + log write | `tools.py` |
| `process_sudden_freq` decision records | `tools.py` |
| `fleet_log_summary` ADK tool | `tools.py` |
| Wire rows + enrichment paragraph | `docs/api-contract.md` |

## Wire fields

All **additive** under `schemaVersion: 1`; no bump. Telemetry keys are optional on the wire and always normalised server-side by `enrich_telemetry`.

| Field | Type | Notes |
|-------|------|--------|
| `band` | string | `17-23k` (default) \| `10-20` |
| `power` | string | Default `ac120` (C5) |
| `nightNY` | bool | Server recomputes from `ts` in America/New_York |
| `lfArmed` | bool | Default false |
| `lfDriveCapable` | bool | Default false |

Log record path: `meta/logs/<node>/<YYYY-MM-DD>.jsonl`.

## Clamps / safety

- No clamp changes. Hold / Manual still wins before any log write.
- `vol_hard_max == 100` untouched.
- PII scrubbed before write; secrets by name only.
- C1 native A2DP only.

## Acceptance

- [x] `fleet_log.py` + tests on main
- [x] tools.py integrator hooks on main
- [x] api-contract enrichment rows
- [x] Closeout evidence under `.vv/22/`
- [x] No schemaVersion bump; no secrets; Hold preserved

## Related

- Colab live features: #26 (owner-gated)
- Hosted webhook: #122
- Continuous ship secrets: #27
