# Colab live GCS sensors evidence — #26 (`features_live`)

**Config item:** `services/autoroute-adk/iot_asp_autoroute/features_live.py` + `notebooks/iot_asp_colab_etl.{ipynb,md}`  
**Spec:** `docs/specs/26-colab-live-gcs-features.md` (FL-01 … FL-13)  
**Date:** 2026-09-08 (UTC)  
**Branch:** `claude/mdc-conversion-features-gu3yzk`  
**Secrets:** by name only — `GCP_SA_JSON`, `IOT_ASP_GCS_BUCKET`, `LIVE_GCS`, `GOOGLE_CLOUD_PROJECT`. No values in this file.

## Requirements

| ID | Requirement |
|----|-------------|
| CS-01 | Sensor columns (`ax..gz`, `accelAxes`, `gyroAxes`, `outLevel`, `micDiff`, `bandBurst`, `soundBurst`, `extremeActive`, `lfEnergy`, `usEnergy`, `lastHopAgeMs`, `ctxResumes`, `watchdogTrips`) projected into `meta/features/<node>/<ts>.json` |
| CS-02 | `micDiff = micEnergy − 0.85·outLevel` computed only when the phone did not send one |
| CS-03 | `*.json` objects and `*.jsonl` files under `meta/telemetry/<node>/` both read; sorted by `ts`; last `limit` kept |
| CS-04 | Never writes `meta/patches/` (guard raises `ValueError`) |
| CS-05 | Offline self-contained CLI (`--seed-demo`) exits 0 with a `file://` URI |
| CS-06 | Live write gated on `LIVE_GCS=1` **and** `IOT_ASP_GCS_BUCKET`; otherwise dry-run mirror |
| CS-07 | Notebook `.ipynb` / `.md` in sync; `userdata` names only; no `meta/patches` in code cells |

## Procedure (offline, no network)

```bash
export IOT_ASP_AUTOROUTE_DRY_ROOT=<tmp>        # scratch mirror; unset LIVE_GCS / IOT_ASP_GCS_BUCKET
PYTHONPATH=services/autoroute-adk python3 -m iot_asp_autoroute.features_live --node node1 --limit 50 --seed-demo
PYTHONPATH=services/autoroute-adk python3 -m iot_asp_autoroute.features_live --node ghost   # negative control
python3 -m pytest tests/test_features_live.py -q
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
```

## Observed (2026-09-08T01:20:57Z, Python 3.11.15, numpy + scipy installed)

`--seed-demo` run — **exit 0** (single JSON line, shown expanded; `<DRY_ROOT>` = the tmp mirror):

```json
{
  "ok": true,
  "live": false,
  "node": "node1",
  "object": "meta/features/node1/2026-09-08T00-00-11Z.json",
  "uri": "file://<DRY_ROOT>/meta/features/node1/2026-09-08T00-00-11Z.json",
  "seeded": 12,
  "seedUris": [
    "file://<DRY_ROOT>/meta/telemetry/node1/2026-09-08T00-00-00Z.json",
    "file://<DRY_ROOT>/meta/telemetry/node1/2026-09-08T00-00-11Z.json"
  ],
  "sourceCount": 12,
  "shriekBias": false,
  "written": true,
  "featureKeys": ["anomaly", "credentialPolicy", "derived", "deviceId", "engineId", "kind", "live",
                  "micDiffAlpha", "sampleHz", "schemaVersion", "sensorColumns", "sensors", "shriekBias",
                  "sourceCount", "sourceObjects", "telemetry", "ts", "writer"]
}
```

Mirror after the run (13 files; **no** `meta/patches/`):

```
<DRY_ROOT>/meta/features/node1/2026-09-08T00-00-11Z.json
<DRY_ROOT>/meta/telemetry/node1/2026-09-08T00-00-00Z.json … 2026-09-08T00-00-11Z.json   (12 seeded points)
```

Features object excerpt (`sensors` block of the latest point; `micDiff` computed = −40 − 0.85·(−30) = −14.5 dB; `bandBurst` = `us` because `usEnergy` −50 ≥ −55 and `lfEnergy` −70 < −60; `anomaly.n` = 12, SciPy engine):

```json
"sensors": {"accelAxes": [-0.0366, 0.0459, 0.9939], "ax": -0.0366, "ay": 0.0459, "az": 0.9939,
            "bandBurst": "us", "ctxResumes": 0, "gx": 0.4069, "gy": 0.2608, "gz": 0.2754,
            "gyroAxes": [0.4069, 0.2608, 0.2754], "lastHopAgeMs": 510, "lfEnergy": -70.0,
            "micDiff": -14.5, "outLevel": -30.0, "usEnergy": -50.0, "watchdogTrips": 0},
"shriekBias": false, "sourceCount": 12, "live": false, "ts": "2026-09-08T00:00:11Z"
```

Negative control `--node ghost` — **exit 2**, no write:

```json
{"error": "no telemetry under meta/telemetry/ghost/", "featureKeys": [], "live": false, "node": "ghost", "object": null, "ok": false, "seeded": 0, "sourceCount": 0, "uri": null}
```

| Check | Result |
|-------|--------|
| `python3 -m pytest tests/test_features_live.py -q` | exit 0 — 26 passed (FL-01 … FL-13 + ts / guard extras) |
| `bash scripts/ci_static_gates.sh` | exit 0 — `OK ci_static_gates` |
| `bash scripts/autoroute_dev.sh` | exit 0 — `DRY-RUN OK` (unchanged by this module) |
| `notebooks/iot_asp_colab_etl.ipynb` | parses as JSON, `nbformat: 4`, 6 cells (md, code, code, code, md, code) |
| FL-12 sync | `.md` python blocks == `.ipynb` code-cell sources (asserted in tests) |

## Live command (exact; not run here)

```bash
LIVE_GCS=1 IOT_ASP_GCS_BUCKET=<name> IOT_ASP_AUTOROUTE_DRY_RUN=0 GOOGLE_APPLICATION_CREDENTIALS=<path-to-SA-json> \
  PYTHONPATH=services/autoroute-adk python3 -m iot_asp_autoroute.features_live --node node1 --limit 200 --live
```

From Colab: open `notebooks/iot_asp_colab_etl.ipynb`, add `userdata` secrets **named** `GCP_SA_JSON`,
`IOT_ASP_GCS_BUCKET`, `LIVE_GCS` (= `1`), run all cells; the last cell prints the `gs://…/meta/features/node1/<ts>.json` URI.

**live: PENDING — requires Colab userdata GCP_SA_JSON + IOT_ASP_GCS_BUCKET + LIVE_GCS=1**

## Pass/fail

| Req | Status |
|-----|--------|
| CS-01 … CS-07 (offline path) | **PASS** (local, 2026-09-08) |
| Live GCS write | **PENDING** — owner runs the notebook with `LIVE_GCS=1`; record the `gs://` object name (bucket redacted) here |
