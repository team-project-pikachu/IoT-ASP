# Accounts, seats and which service lives where

IoT-ASP runs across **two Google identities**, and the split is **forced by a vendor
constraint**, not a stylistic preference. Getting it wrong produces confusing
`PERMISSION_DENIED` errors or an events subscription that stays silent forever.

Addresses are **not** written into this repo (CLAUDE.md invariant 7). They are referenced
by secret name from 1Password Environment `dev`, resolved **headlessly** via
`OP_SERVICE_ACCOUNT_TOKEN` — see [`scripts/nest_secrets_headless.sh`](../scripts/nest_secrets_headless.sh).

| Name used here | Kind | Secret name |
|---|---|---|
| **owner-consumer** | consumer Google Account (`gmail.com`) | `NEST_DA_OWNER_ACCOUNT` |
| **owner-org** | Google Workspace account on the research domain | `IOT_ASP_ORG_ACCOUNT` |

---

## Why the split is forced

> Device Access requires a **consumer** Google Account. Google Workspace accounts are
> **not supported**.
> — <https://developers.google.com/nest/device-access/get-started>

Nest devices are owned in the Google Home app by **owner-consumer**, so the Device Access
project, the US$5 fee, and the PCM OAuth consent must all be that account. Everything
billed, licensed or seat-metered — the GCP project, Gemini Enterprise, Vertex/Agent
Platform — sits on **owner-org**. The two are joined by exactly one IAM grant.

---

## Service → account map

| Service | Account | Notes |
|---|---|---|
| Nest devices in the Google Home app | **owner-consumer** | must match the consent account |
| Device Access Console project (UUID) + US$5 fee | **owner-consumer** | <https://console.nest.google.com/device-access> |
| SDM PCM consent → `NEST_REFRESH_TOKEN` | **owner-consumer** | 3LO; a service account **cannot** call SDM on a user's behalf |
| GCP project `bear-iot-asp-rec` (number `1062135198697`) | **owner-org** | billing, IAM, quota |
| OAuth 2.0 client for SDM | **owner-org** project | redirect URI `https://www.google.com`; unique per Device Access project |
| Pub/Sub topic + pull subscription | **owner-org** project | self-hosted topic (post-Jan-2025 rule) |
| Secret Manager (`NEST_*`) | **owner-org** project | values from 1Password `dev` |
| Gemini Enterprise engine `iot-asp-autoroute` | **owner-org** | Discovery Engine; **5 standard seats** on the domain |
| Vertex / Agent Platform / Colab Enterprise | **owner-org** project | owner-consumer is *granted* access, see below |
| Poller service account `iot-asp-nest-poller` | **owner-org** project | `roles/pubsub.subscriber` on the subscription only |
| Vercel (`hop-ultrasonic`) | `1digital-design` | unchanged by this work |

**The one joining grant** — so owner-consumer can open and run notebooks in the org
project (`scripts/nest_gcp_bootstrap.sh` step 7):

```bash
gcloud projects add-iam-policy-binding bear-iot-asp-rec \
  --member="user:${NEST_DA_OWNER_ACCOUNT}" \
  --role="roles/aiplatform.colabEnterpriseUser"   # minimum to create + run a Colab Enterprise notebook
gcloud projects add-iam-policy-binding bear-iot-asp-rec \
  --member="user:${NEST_DA_OWNER_ACCOUNT}" \
  --role="roles/viewer"
```

Role source: <https://docs.cloud.google.com/colab/docs/access-control>

---

## Seat arithmetic (5 standard seats)

Gemini Enterprise seats are **licensed to the Workspace domain**. A consumer
`gmail.com` account **cannot hold one**. Two consequences that shape the code:

1. **The burst detector runs as owner-org / the service account, never as
   owner-consumer.** `nest/detector.py` authenticates with Application Default
   Credentials in the org project, not with the SDM user token.
2. **Nest costs zero additional seats.** The detector calls the *same* engine
   (`iot-asp-autoroute`) the autoroute agent already uses — `docs/gemini-enterprise.md`
   already allocates one seat to "continuous monitor + audio-engineering control". Adding
   the Nest acoustic witness reuses that seat rather than claiming a second.

| Seat | Role | Consumed by |
|---|---|---|
| 1 | PI / admin | owner-org |
| 2 | Continuous monitor + autoroute + **Nest burst detector** | the ADK agent / service account |
| 3–4 | Analyst / engineer | TBD |
| 5 | Reserve | TBD |

Roster detail stays in gitignored `study/GEMINI_ENTERPRISE_ROSTER.md`
(`docs/gemini-enterprise.md`).

---

## `gcloud alpha` / `gcloud beta` surfaces

The Agent Platform pieces are not in the GA `gcloud` surface. These command groups were
confirmed to exist in the live reference on 2026-09-08:

| Need | Surface | Subcommands |
|---|---|---|
| Colab Enterprise notebooks (Agent Platform → Colab) | **`gcloud beta colab`** | `runtime-templates`, `runtimes`, `executions`, `schedules` |
| Agent Platform agent registry (register/deploy an ADK agent) | **`gcloud alpha agent-registry`** | `agents`, `skills`, `endpoints`, `mcp-servers`, `bindings`, `publishers`, `services`, `operations` |
| Vertex AI | `gcloud beta ai` / `gcloud alpha ai` | — |
| Gemini Cloud Assist (**not** Gemini Enterprise engines) | `gcloud beta gemini` | `cloud-assist` only |

Sources: <https://docs.cloud.google.com/sdk/gcloud/reference/beta/colab/> ·
<https://docs.cloud.google.com/sdk/gcloud/reference/alpha/agent-registry/> ·
<https://docs.cloud.google.com/sdk/gcloud/reference/beta/gemini/>

> **Gemini Enterprise engines are not a `gcloud` surface.** `gcloud beta gemini` is Cloud
> Assist only. The engine `iot-asp-autoroute` is Discovery Engine, reached over REST at
> `discoveryengine.googleapis.com` — which is exactly what `nest/detector.py` calls, and
> why it uses `urllib` rather than shelling out to `gcloud`.

Run a Colab Enterprise notebook headlessly on the org project:

```bash
gcloud beta colab runtime-templates list --region=us-central1 --project=bear-iot-asp-rec
gcloud beta colab executions create \
  --region=us-central1 --project=bear-iot-asp-rec \
  --notebook-runtime-template=<template> \
  --gcs-notebook-uri=gs://<bucket>/notebooks/iot_asp_nest_adk.ipynb
```

---

## Preflight checklist

```bash
# 1Password headlessly — no signin, no biometrics, no desktop app
export OP_SERVICE_ACCOUNT_TOKEN=...
bash scripts/nest_secrets_headless.sh check          # names + presence only

# GCP plan, mutating nothing
bash scripts/nest_gcp_bootstrap.sh                   # dry run
NEST_DA_OWNER_ACCOUNT=$(op read "op://dev/IoT-ASP Nest Device Access/NEST_DA_OWNER_ACCOUNT") \
  bash scripts/nest_gcp_bootstrap.sh --apply         # owner, once
```

Related: [`nest-device-access.md`](nest-device-access.md) ·
[`gemini-enterprise.md`](gemini-enterprise.md) ·
[`specs/85-nest-google-home-integration.md`](specs/85-nest-google-home-integration.md)
