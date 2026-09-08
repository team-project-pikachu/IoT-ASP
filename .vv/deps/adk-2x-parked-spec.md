# ADK 2.x parked-spec verification — 2026-09-08

**Issue:** [#24](https://github.com/team-project-pikachu/IoT-ASP/issues/24)  
**Scope:** Documentation honesty pass only; `google-adk` remains on major 1.

## Procedure

| Gate | Expected |
|------|----------|
| `python3 -m pytest tests/test_agent_import.py -q` | Source tool sequence and parked pins match the spec; live import runs when ADK is installed or skips otherwise |
| `python3 -m pytest tests -q` | Full repository suite remains green |
| `bash scripts/ci_static_gates.sh` | Hold / Manual, schema, clamp, and frontend secret gates pass |
| `bash scripts/autoroute_dev.sh` | Offline dry-run passes without requiring ADK |
| `python3 scripts/mdc_convert.py --check` | Cursor-derived outputs remain current |

## Observed results

Run from the PR worktree on 2026-09-08 UTC.

| Gate | Exit | Result |
|------|------|--------|
| Targeted pytest | 0 | PASS — 4 passed, 1 live-ADK test skipped because ADK was not installed locally |
| Full pytest | 0 | PASS — 273 passed, 1 live-ADK test skipped |
| Static gates | 0 | PASS — no frontend key patterns; patch schema and clamp constants valid |
| Autoroute dry-run | 0 | PASS — clamp and Hold / Manual negative controls passed; dry-run patch written |
| MDC conversion check | 0 | PASS — generated outputs are current |

## Non-claims

- No `google-adk` 2.x package was installed or tested.
- No preview or production deployment was performed.
- Migration evidence remains reserved for `.vv/deps/adk-2x.md` in the future unpark PR.
