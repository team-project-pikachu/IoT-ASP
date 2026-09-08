# ISSUE-22 — Structured fleet logs

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/22  
**Classification:** ship / stub iterate (Balanced)  
**Status:** implemented (stack PR2 deepen)

## Did

- `services/autoroute-adk/iot_asp_autoroute/fleet_log.py` (24 RECORD_KEYS)
- `tools.ingest_telemetry` / `process_sudden_freq` / `fleet_log_summary` hooks
- `tests/test_fleet_log.py`
- `scripts/fleet_log_demo.sh` dry-run CLI
- PWA: Copy fleet_log JSONL (fixed key order mirror)

## Didn't

- Live GCS writes without owner `LIVE_GCS` + bucket/SA
- Auto-close the GitHub issue (human verifies).

## Next

- Owner may point beacon → ingest worker; dry-run path is enough for local V&V
