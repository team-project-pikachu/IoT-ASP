# Evidence — #25 HW-limited LF mic/TX + AEC `micDiff` → burst → `shriek_chirp` bias

**Config item:** `services/autoroute-adk/iot_asp_autoroute/mic_diff.py` + `tests/test_mic_diff.py`
**Spec:** `docs/specs/25-hw-limited-lf-aec-micdiff.md`
**Branch:** `claude/mdc-conversion-features-gu3yzk` (base `4e4f5db`)
**Date:** 2026-09-08 (UTC)
**Environment:** Python 3.11.15, numpy 2.4.6 (CI: 3.12 + `requirements-dev.txt`)
**SEBoK plan:** not modified · **Secrets:** none read or printed · **Site PII:** none

## Requirements

| ID | Requirement |
|----|-------------|
| BS-01 | `MIC_DIFF_ALPHA == 0.85`; `mic_diff(mic, out, alpha)` = `mic − alpha·out`, passthrough when `outLevel` missing |
| BS-02 | `calibrate_alpha` = least squares through origin (`numpy.linalg.lstsq`), clamp `[0, 2]`, refuse `< 3` pairs / no variance |
| BS-03 | `aec_capability` → `fullAEC False`, `path output-bus-subtraction`, for every user agent |
| BS-04 | `lf_capability` → `lfMic False` always; `lfTx == priors.lf_drive_capable(t)` |
| BS-05 | `burst_decision` monotone in `thr_db` (strict `>`); `hold_manual=True` refuses for every `micDiff` |
| BS-06 | `apply_burst_bias` → `shriek_chirp`, `shriekMs + 15` clamped to `[20, 120]`; `validate_patch` still passes |
| BS-07 | `hw_limits_report` → four limits `full_aec`, `lf_mic`, `lf_tx`, `alpha_calibration`, docs + `#9` pointers, no URLs |
| BS-08 | CLI `python3 -m iot_asp_autoroute.mic_diff --demo` exits 0, deterministic; no args → exit 2 |
| BS-09 | Module imports without scipy / google; source has no CFD / Navier / Web Bluetooth claims |

## Procedure

```bash
python3 -m pytest tests/test_mic_diff.py -q
cd services/autoroute-adk && python3 -m iot_asp_autoroute.mic_diff --demo
cd services/autoroute-adk && python3 -m iot_asp_autoroute.mic_diff        # usage, exit 2
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
python3 -m pytest tests -q
```

## Observed

| Command | Exit | Result |
|---------|------|--------|
| `python3 -m pytest tests/test_mic_diff.py -q` | 0 | `19 passed` (MD-01 … MD-17) |
| `python3 -m iot_asp_autoroute.mic_diff --demo` | 0 | JSON below; two consecutive runs byte-identical |
| `python3 -m iot_asp_autoroute.mic_diff` | 2 | `usage: python3 -m iot_asp_autoroute.mic_diff [-h] [--demo]` on stderr, empty stdout |
| `bash scripts/ci_static_gates.sh` | 0 | `OK ci_static_gates` |
| `bash scripts/autoroute_dev.sh` | 0 | `DRY-RUN OK` (module not on the dry-run path until the integrator hook lands) |
| `python3 -m pytest tests -q` | 0 | `51 passed` (whole suite) |

### Demo JSON (key fields)

```text
micDiff                 5.5          # mic_diff(-20.0, -30.0) = -20 - 0.85*(-30)
calibration.alpha       0.8575       # 12 TX-only pairs, seed 25, true alpha 0.85
calibration.ok          true         # n=12, residual_rms 0.4637, clamped false, reason "ok"
burst.extreme           true         # micEnergy -12 / outLevel -30 → micDiff 13.5 dB > thr 6.0
burst.algo              shriek_chirp # shriekMsBias 15
burst.quietMicDiffDb    5.5          # quietExtreme false (5.5 dB <= 6.0)
burstHold.reason        "holdManual — refuse"   # micDiff 20 dB, hold_manual=True → extreme false
aec.fullAEC             false        # userAgentClass ios-safari, path output-bus-subtraction
lf.lfMic / lf.lfTx      false / false   # micBinHz 23.44, txBinHz 2.93, lfBandHz [10, 20]
report.limits           4            # full_aec, lf_mic, lf_tx, alpha_calibration
```

## HW-limited leftovers (issue #25) — pass/fail

| Limit | Status | Evidence |
|-------|--------|----------|
| `full_aec` — full AEC on iOS Safari / Chrome Web Audio | **limited** (by design, honest) | `aec_capability()["fullAEC"] is False` for `None`, `""`, iOS Safari, iOS Chrome, desktop UAs (MD-12); shipped path = output-bus subtraction α = 0.85 |
| `lf_mic` — <20 Hz mic capture | **limited** (by design, honest) | `lf_capability()["lfMic"] is False` for all 7 fixtures (MD-13); 23.44 Hz/bin argument on the wire; `lfEnergy` documented as accelerometer felt proxy |
| `lf_tx` — LF 10–20 Hz TX over A2DP | **gated** | `lfTx == priors.lf_drive_capable(t)`; `True` only with `lfDriveCapable: True` or `lfArmed` + LF band; `False` under `holdManual` (MD-13, MD-17) |
| `alpha_calibration` — α per device / BT route | **calibrated in demo** | seed-25 fit recovers `0.8575` (|Δ| < 0.1); exact-fit pairs → `0.85 ± 1e-9`; slope 10 → clamped `2.0`; slope −3 → clamped `0.0`; `< 3` pairs / zero `outLevel` → `ok False`, default `0.85` (MD-04 … MD-06) |

## Safety invariants exercised

| Invariant | Test |
|-----------|------|
| Hold / Manual wins (refuse for `micDiff ∈ {None, −10, 0, 6.01, 40, 1e9}`; flags ignored under hold) | MD-09 |
| `shriekMs` clamp `[20, 120]` — `110 + 15 → 120.0`, never `125`; bogus bias 999 ignored | MD-11, MD-17 |
| `algo` whitelist — `BURST_ALGO in ALLOWED_ALGOS`; `validate_patch(out)[0] is True` | MD-01, MD-11 |
| `vol_hard_max == vol_soft_max == 100.0`; `apply_burst_bias` never touches `vol`/`fMin`/`fMax`/`band` | MD-01, MD-11 |
| No CFD / Navier / Web Bluetooth strings; no `os.environ`; fresh import adds no `scipy` / `google` modules | MD-15 |
| Deterministic CLI (seeded, no timestamps) | MD-16 |

## Integration still pending (integrator-owned files, requested not edited)

- `sudden_freq.py::author_sudden_freq_patch` — `burst_decision_from_telemetry` + `apply_burst_bias` after the duty bias, before `validate_patch`.
- `tools.py` — tool `hw_limits_report()`; `agent.py` `tools=[…]` registration.
- `docs/api-contract.md` — optional additive patch row `burstBias`.
