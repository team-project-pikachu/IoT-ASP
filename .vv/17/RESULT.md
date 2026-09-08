# Issue #17 — Evidence RESULT

| Field | Value |
|-------|--------|
| Issue | [#17 Colab + Gemini Enterprise pipeline](https://github.com/team-project-pikachu/IoT-ASP/issues/17) |
| Lane | `exec-17-colab` |
| Verdict | **PASS** (offline harden + V&V evidence) |
| Project Done | **Deferred** to integrate lane (do not flip board here) |
| Vercel e2e | **Not run** (scope lock) |

## Deliverables touched

- `notebooks/iot_asp_colab_etl.ipynb` / `.md` — hardened offline + gated GCS + vib/gyro/sound cell
- `docs/colab-gemini-pipeline.md` — shared SciPy path, sensor feature columns, credential refs
- `docs/api-contract.md` — additive accel/gyro/micDiff/burst fields
- `services/autoroute-adk/iot_asp_autoroute/colab_etl.py` — shared feature builder + shriek bias
- `scripts/colab_etl_dry_run.py` — deterministic offline verify
- `.vv/colab-sensors.md` — sensor ETL evidence note

## Evidence index

| File | Role |
|------|------|
| `requirements.md` | R17-* capture |
| `verification.md` | V17-* |
| `validation.md` | Val17-* |
| `colab_etl_dry_run.json` | Offline ETL summary |
| `vib_anomaly_dry_run.json` | Shared SciPy anomaly |
| `feature_columns_vs_contract.json` | Contract match |
| `REVISION.txt` / `OBSERVED_AT.txt` | Subject + time |

## Context7

`/scipy/scipy` — `medfilt` (odd kernel), `median_abs_deviation(scale="normal")`, `find_peaks` filtering order — cited in pipeline doc; implementation remains `vib_anomaly.py`.
