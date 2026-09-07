# ADK autoroute agent

IoT-ASP’s continuous monitor + audio-engineering control plane is an **[Agent Development Kit (ADK)](https://docs.cloud.google.com/agent-builder/agent-development-kit/overview)** agent on Gemini Enterprise Agent Platform.

**Wire format:** [api-contract.md](api-contract.md) (`schemaVersion: 1`). Frontend only polls patches / beacons telemetry — never embeds Vertex keys or ADK logic.

## Independent deploy (backend ≠ frontend)

`services/autoroute-adk/` deploys to **GCP** (`bear-iot-asp-rec`). `public/` deploys to **Vercel**. They share only the JSON contract.

| Artifact | Host | When to redeploy |
|----------|------|------------------|
| `public/index.html`, `public/patch.json` | Vercel static | UI / offline mock / URL constant changes |
| ADK agent (`iot_asp_autoroute/`) | Agent Engine or Cloud Run | Prompt, tools, clamps, suddenFreq author |
| HTTP ingest (`ingest_main.py`) | Cloud Run / Cloud Functions | Telemetry POST handler |
| GCS objects | Private bucket | Runtime writes — no “deploy” |

**Rules**

1. Frontend change → Vercel only. Do **not** redeploy ADK unless the wire schema broke.
2. Backend change → `adk deploy …` / Cloud Run only. Do **not** redeploy Vercel unless you also changed HTML constants or the mock `patch.json`.
3. Point phones at live ingest/patch URLs via `?telemetry=` / `?patch=` (or env-like `BACKEND_*` at the top of `index.html`) without rebuilding the agent.
4. Local backend dry-run (no GCP, no Vercel): `bash scripts/autoroute_dev.sh`.

```text
  Vercel (public/)          GCS private              GCP ADK / ingest
  ┌─────────────────┐      ┌──────────────┐         ┌──────────────────┐
  │ GET /patch.json │◄─────│ meta/patches │◄────────│ write_patch tool │
  │ POST telemetry? │─────►│ meta/telemetry│────────►│ read + suddenFreq│
  └─────────────────┘      └──────────────┘         └──────────────────┘
        ▲ deploy vercel              │                    ▲ adk deploy
        │ independently              │                    │ independently
```

## Why ADK

ADK is Google’s open-source, code-first framework (Python/TS/Go/Java) to build, debug, and deploy agents to **Agent Runtime / Cloud Run / GKE**. Official pattern: package with `root_agent`, tools as Python callables, local `adk web` / `adk run`, deploy via `adk deploy agent_engine` or `adk deploy cloud_run`.

Context7: `/google/adk-python`. Firecrawl digests: `reference/knowledge/adk/`.

## Agent package

```
services/autoroute-adk/
  requirements.txt
  README.md
  ingest_main.py         # optional HTTP ingest (separate Cloud Run/CF)
  iot_asp_autoroute/
    __init__.py          # from . import agent
    agent.py             # root_agent = LlmAgent(...)
    tools.py             # GCS telemetry, patch write, clamps, Colab handoff
    clamps.py
    priors.py
    sudden_freq.py       # suddenFreq → autorotate
    gcs_io.py
    dry_run.py
```

## Tools

| Tool | Role |
|------|------|
| `read_telemetry` | Read latest GCS `meta/telemetry/<nodeId>/…` |
| `write_patch` | Validate clamps → write `meta/patches/<nodeId>.json` (`schemaVersion: 1`) |
| `ingest_telemetry` | Store heartbeat / suddenFreq beacon |
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
export IOT_ASP_AUTOROUTE_DRY_RUN=1   # mocked GCS under .autoroute-dry/
adk web   # or: adk run iot_asp_autoroute
```

Dry-run without ADK CLI / Vertex:

```bash
bash scripts/autoroute_dev.sh
```

## Deploy (Agent Runtime / Cloud Run) — backend only

From repo root (does **not** touch Vercel):

```bash
gcloud config set account betty@bearresearch.io
gcloud config set project bear-iot-asp-rec

# Agent Engine (Agent Runtime)
adk deploy agent_engine \
  --project=bear-iot-asp-rec \
  --region=us-central1 \
  --display_name=iot-asp-autoroute-adk \
  services/autoroute-adk/iot_asp_autoroute

# Or Cloud Run (ADK service)
adk deploy cloud_run \
  --project=bear-iot-asp-rec \
  --region=us-central1 \
  --service_name=iot-asp-autoroute-adk \
  services/autoroute-adk/iot_asp_autoroute
```

Optional **ingest** service (telemetry POST target for `?telemetry=`):

```bash
# Package ingest_main.py + iot_asp_autoroute for Cloud Run / CF Gen2.
# Set IOT_ASP_GCS_BUCKET + ADC/runtime SA. No keys in git.
# After deploy, give phones: ?telemetry=https://<ingest-host>/
```

Requires ADC (`gcloud auth application-default login`) with quota project `bear-iot-asp-rec`. No API keys in git.

## Frontend pointing at a new backend

Without redeploying Vercel HTML (if constants already ship empty defaults):

```text
https://<vercel-app>/?telemetry=https://<ingest.run.app>/&patch=https://<cdn-or-signed>/meta/patches/node1.json
```

Or set `BACKEND_BASE_URL` / `BACKEND_TELEMETRY_URL` / `BACKEND_PATCH_URL` near the top of `public/index.html` and redeploy **Vercel only**.

## Colab

Colab ETL notebook (`notebooks/iot_asp_colab_etl.ipynb`) computes spectra/vib features and can call / complement this ADK agent; Gemini Enterprise seats interpret and suggest patches. See [colab-gemini-pipeline.md](colab-gemini-pipeline.md).
