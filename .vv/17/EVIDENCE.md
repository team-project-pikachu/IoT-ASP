# Evidence package — Issue #17 (Colab + Gemini pipeline)

**Status:** Phase 1 matrix scaffold + exec-17 draft package (see siblings).  
**Issue:** [#17](https://github.com/team-project-pikachu/IoT-ASP/issues/17)

## Index

| Artifact | Path |
|----------|------|
| Result summary | [RESULT.md](RESULT.md) |
| Requirements | [requirements.md](requirements.md) |
| Verification | [verification.md](verification.md) |
| Validation | [validation.md](validation.md) |
| Offline ETL | [colab_etl_dry_run.json](colab_etl_dry_run.json) |
| SciPy anomaly | [vib_anomaly_dry_run.json](vib_anomaly_dry_run.json) |
| Contract columns | [feature_columns_vs_contract.json](feature_columns_vs_contract.json) |
| Sensor ETL (accel/gyro/mic) | [../colab-sensors.md](../colab-sensors.md) |
| Revision / time | [REVISION.txt](REVISION.txt) · [OBSERVED_AT.txt](OBSERVED_AT.txt) |
| Matrix rows | [../matrix.md](../matrix.md) (`I17-*`, SCH1, C5) |

## Known drift

- Missing `docs/gcp-recordings.md` (ops narrative for `bear-iot-asp-rec`).
- Live GCS Colab path not executed this pass — Project 5 follow-up (see `.vv/colab-sensors.md`).

## Promotion

Project Status → Done deferred to integrate lane (no Vercel e2e in this package alone).
