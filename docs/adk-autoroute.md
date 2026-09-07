# ADK autoroute agent

IoT-ASP’s continuous monitor + audio-engineering control plane is an **[Agent Development Kit (ADK)](https://docs.cloud.google.com/agent-builder/agent-development-kit/overview)** agent on Gemini Enterprise Agent Platform.

## Why ADK

ADK is Google’s open-source, code-first framework (Python/TS/Go/Java) to build, debug, and deploy agents to **Agent Runtime / Cloud Run / GKE**. Official pattern: package with `root_agent`, tools as Python callables, local `adk web` / `adk run`, deploy via `adk deploy agent_engine` or `adk deploy cloud_run`.

Context7: `/google/adk-python`. Firecrawl digests: `reference/knowledge/adk/`.

## Agent package

```
services/autoroute-adk/
  requirements.txt
  README.md
  iot_asp_autoroute/
    __init__.py          # from . import agent
    agent.py             # root_agent = LlmAgent(...)
    tools.py             # GCS telemetry, patch write, clamps, Colab handoff, NS priors
    clamps.py
    priors.py
```

## Tools

| Tool | Role |
|------|------|
| `read_telemetry` | Read latest GCS `meta/telemetry/<nodeId>/…` |
| `write_patch` | Validate clamps → write `meta/patches/<nodeId>.json` |
| `list_safety_clamps` | Expose band/gain/duty limits to the model |
| `seismo_acoustic_priors` | Short NS / linearized-acoustic / earthquake-coupling priors |
| `colab_handoff_note` | Emit a Colab ETL job note (spectra/vib features) for Gemini seat analysis |

## Gemini Enterprise pairing

- Engine id: **`iot-asp-autoroute`** (Discovery Engine on `bear-iot-asp-rec`)  
- Vertex model for ADK: `gemini-2.5-flash` (configurable via env)  
- Env: `GOOGLE_CLOUD_PROJECT=bear-iot-asp-rec`, `GOOGLE_CLOUD_LOCATION=us-central1`, `IOT_ASP_GEMINI_ENGINE_ID=iot-asp-autoroute`, `IOT_ASP_GCS_BUCKET` (private; set locally / Secret Manager)

## Run locally

```bash
cd services/autoroute-adk
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT=bear-iot-asp-rec
export GOOGLE_CLOUD_LOCATION=us-central1
export IOT_ASP_AUTOROUTE_DRY_RUN=1   # mocked GCS
adk web   # or: adk run iot_asp_autoroute
```

Dry-run without ADK CLI:

```bash
bash scripts/autoroute_dev.sh
```

## Deploy (Agent Runtime / Cloud Run)

```bash
gcloud config set account betty@bearresearch.io
gcloud config set project bear-iot-asp-rec

# Agent Engine (Agent Runtime)
adk deploy agent_engine \
  --project=bear-iot-asp-rec \
  --region=us-central1 \
  --display_name=iot-asp-autoroute-adk \
  services/autoroute-adk/iot_asp_autoroute

# Or Cloud Run
adk deploy cloud_run \
  --project=bear-iot-asp-rec \
  --region=us-central1 \
  --service_name=iot-asp-autoroute-adk \
  services/autoroute-adk/iot_asp_autoroute
```

Requires ADC (`gcloud auth application-default login`) with quota project `bear-iot-asp-rec`. No API keys in git.

## Colab

Colab ETL notebook (`notebooks/iot_asp_colab_etl.ipynb`) computes spectra/vib features and can call / complement this ADK agent; Gemini Enterprise seats interpret and suggest patches. See [colab-gemini-pipeline.md](colab-gemini-pipeline.md).
