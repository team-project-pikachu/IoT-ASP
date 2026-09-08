# #141 — Near-ultrasonic mic evidence

**Date (UTC):** 2026-09-08
**Branch:** `feat/141-ultrasonic-mic`
**Honesty:** CLT `IoTASPSmoke` + pytest. No device mic claim. No SensorKit.

## Procedure

1. `bash scripts/native_compile_check.sh`
2. `python3 -m pytest tests/test_ultrasonic_mic.py tests/test_coremotion_suite.py -q`

## Observed results

### native_compile_check.sh

- **exit_code:** `0` → PASS (`IoTASPSmoke OK` includes UM Nyquist / micDiff 5.5)

### pytest

- **exit_code:** `0` after comment-grep fix (`tests/test_ultrasonic_mic.py`)
