# IoT-ASP ADK autoroute agent

Package: `iot_asp_autoroute`  
GCP project: `bear-iot-asp-rec`  
Engine: `iot-asp-autoroute`

## Layout

```
services/autoroute-adk/
  requirements.txt
  README.md
  .env.example
  iot_asp_autoroute/
    __init__.py
    agent.py          # root_agent
    tools.py
    clamps.py
    priors.py
    sudden_freq.py    # suddenFreq → autorotate
    gcs_io.py
    dry_run.py
```

## Dry-run (no keys / no Vertex)

From repo root:

```bash
bash scripts/autoroute_dev.sh
```

Writes mocked telemetry + `meta/patches/<nodeId>.json` under `.autoroute-dry/`.

## Live ADK (ADC)

```bash
cd services/autoroute-adk
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT=bear-iot-asp-rec
export GOOGLE_CLOUD_LOCATION=us-central1
export IOT_ASP_GCS_BUCKET=<private-bucket>   # never commit
export IOT_ASP_AUTOROUTE_DRY_RUN=0
gcloud auth application-default login
adk web   # or: adk run iot_asp_autoroute
```

## Deploy (independent of Vercel)

See `docs/adk-autoroute.md` and wire format `docs/api-contract.md`.  
`adk deploy …` / Cloud Run updates the backend only — do not redeploy Vercel unless `public/` changed. Service account + Vertex; no API keys in git.

## WAF notes

- Secrets: env / Secret Manager / Colab userdata only  
- Private GCS for telemetry + patches  
- Clamp Gemini outputs before apply (`vol` UI percent soft==hard ≤100; Hold/Manual refuses writes)
