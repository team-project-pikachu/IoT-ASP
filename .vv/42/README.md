# V&V — impulse→blast / alarm (#42 / #44 / #45)

**Config item:** `public/index.html`, `native/IoTASP/Shared/Alarm/AlarmStateMachine.swift`
**Date:** 2026-09-08 (UTC)
**Revision:** PR #57 revision containing this evidence

## Procedure

```bash
python3 -m pytest tests -q
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
cd native/IoTASP && swift Scripts/alarm_smoke.swift
```

## Observed results

| Check | Exit | Result |
|-------|-----:|--------|
| Full Python suite | 0 | **261 passed** (9.04 s) |
| Static policy gates | 0 | no frontend key patterns; schema/clamps/Hold checks passed |
| Autoroute dry-run | 0 | clamped patch, fleet log, and Hold refusal checks passed |
| Native alarm smoke | 0 | trigger, sustain, observable clear, retrigger, and Hold checks passed |
| Impulse heartbeat latch | 0 | static regression asserts snapshot-before-clear behavior |
| Same-origin peer tabs | 0 | static regression asserts per-tab `instanceId` filtering/keying |

## Pass/fail

| Requirement | Status |
|-------------|--------|
| `impulse` survives until a heartbeat snapshots it | **PASS** |
| Quiet hysteresis exposes `cleared` | **PASS** |
| A later impulse retriggers from `cleared` | **PASS** |
| Hold / Manual suppresses blast | **PASS** |
| Peer tabs sharing one `deviceId` remain discoverable | **PASS** |

Telemetry fields remain additive under `schemaVersion: 1`.
