# Colab sensor ETL — accel / gyro / mic-spectrum

**Date:** 2026-09-08 (America/New_York session; evidence UTC in `.vv/17/OBSERVED_AT.txt`)  
**Issue:** [#17](https://github.com/team-project-pikachu/IoT-ASP/issues/17) (+ Project 5 follow-up for live GCS)  
**Credential policy:** userdata / env **names** only (`GCP_SA_JSON`, `IOT_ASP_GCS_BUCKET`, …) — no secrets in tree.

## What changed

| Artifact | Change |
|----------|--------|
| `services/autoroute-adk/iot_asp_autoroute/colab_etl.py` | Accel axes, gyro ω, `micDiff`/`micNet`, LF/US band energy, `soundBurst`/`extremeActive`/`bandBurst`; synthetic fixture; shriek-biased patch stub |
| `sudden_freq.py` | Treat `soundBurst` / `extremeActive` / event `soundBurst` as sudden-freq path |
| `docs/api-contract.md` | Additive optional sensor/burst fields (`schemaVersion` still 1) |
| `docs/colab-gemini-pipeline.md` | Sensor ETL table + notebook cell 2b |
| `notebooks/iot_asp_colab_etl.ipynb` / `.md` | Offline vib+gyro+sound dry cell |
| `.vv/17/colab_etl_dry_run.json` | Offline evidence refresh |

## Schema alignment (frontend burst / micDiff)

Matches `docs/algorithms.md` + `public/index.html`:

- `micDiff = micEnergy − α·outLevel` with **α = 0.85**; alias `micNet`
- `bandBurst` ∈ `lf|us|both|none` (sensing &lt;20 Hz / &gt;17 kHz)
- `soundBurst`, `extremeActive` sustained while bursting
- Optional axes: `ax,ay,az`, `gx,gy,gz` / `absOmega` (Colab-ready; phone may omit gyro until wired)

## Offline evidence

```bash
python3 scripts/colab_etl_dry_run.py
# ok=true; sensorShriekBias=true; sensorBandBurst=both; sensorSuggestionAlgo in shriek family
```

See `.vv/17/colab_etl_dry_run.json`, `feature_columns_vs_contract.json`.

## Live GCS

**Incomplete** — gated notebook path (`LIVE_GCS=1` + Colab userdata) not executed in this lane.  
**Project 5:** [#26 Colab live GCS: ingest accel/gyro/micDiff telemetry → meta/features](https://github.com/team-project-pikachu/IoT-ASP/issues/26) (added to board). Do **not** block Vercel.
