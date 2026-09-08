# #64 — Software-only verify evidence (Balanced PR7)

**Date:** 2026-09-08  
**Honesty:** marks **CI-verifiable** procedures only. Does **not** claim matrix `pass` for field lab / HW rows.

## Commands (local / Actions `tests` job)

```bash
python -m pytest tests/test_api_contract.py tests/test_fleet_log.py tests/test_public_html.py tests/test_ruleset_json.py -q
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
```

## Mapped rows (status → `in_progress`, not `pass`)

| Req ID | Software verify | Evidence |
|--------|-----------------|----------|
| C1-BT | `navigator.bluetooth` absent in `public/index.html` | `tests/test_api_contract.py`, `test_public_html.py` |
| C4-VOL | `vol_hard_max==100` + HTML vol path | CI autoroute job + `ci_static_gates.sh` |
| C5-120V | telemetry `power: "ac120"` | `test_public_html` / e2e payload |
| SCH1 | `schemaVersion: 1` patch+telemetry | `test_api_contract`, `test_public_html` |
| HOLD1 | Hold/Manual freezes remote apply | e2e Hold test + static gates |
| I12-R2 | beacon fields + no keys in HTML | `test_api_contract`, static gates |

## Still owner / lab gated

- C6 LF systems honesty on device
- `#62` 3-phone field checklist
- Full matrix `pass` rows after evidence packs under `.vv/`
