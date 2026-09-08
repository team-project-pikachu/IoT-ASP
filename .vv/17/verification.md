# Issue #17 — Verification (built right)

**Procedure date (UTC):** see `OBSERVED_AT.txt`  
**Subject revision:** see `REVISION.txt`

| Check | Procedure | Observed | Pass |
|-------|-----------|----------|------|
| V17-1 Offline Colab ETL dry-run | `python3 scripts/colab_etl_dry_run.py` | `colab_etl_dry_run.json` `ok: true`; stderr `holdRefused=True` `quantum=0.0005` | PASS |
| V17-2 Shared SciPy anomaly dry-run | `python3 -m iot_asp_autoroute.dry_run_anomaly` (cwd `services/autoroute-adk`) | `vib_anomaly_dry_run.json` functions medfilt/MAD/find_peaks | PASS |
| V17-3 Feature columns ⊆ contract | Compare `TELEMETRY_FEATURE_COLUMNS` + projected fixture vs api-contract sample JSON | `feature_columns_vs_contract.json` `pass: true` | PASS |
| V17-4 No secrets in artifacts | Grep notebook/docs/module for private key / SA JSON body | secret-scan pass (userdata **name** refs only) | PASS |
| V17-5 Notebook structure | nbformat cells ≥ offline + feature + suggestion + gated GCS | 9 cells; imports `vib_anomaly` / `colab_etl` | PASS |
| V17-6 Handoff note enrichment | `colab_handoff_note` includes shared module + columns | `tools.py` note fields present | PASS |

**Negative control (verification):** `holdManual: true` → suggestion `refused: true` (no patch body).

Artifacts: `colab_etl_dry_run.json`, `colab_etl_dry_run.stderr.txt`, `vib_anomaly_dry_run.json`, `vib_anomaly_dry_run.stderr.txt`, `feature_columns_vs_contract.json`.
