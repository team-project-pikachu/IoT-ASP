# Gemini Enterprise — IoT-ASP (5 seats, hybrid autoroute)

**Pull date:** 2026-09-07  
**GCP project:** `bear-iot-asp-rec` (project number `1062135198697`)  
**Account:** `betty@bearresearch.io` (via `gcloud`; Chrome iOS → active Google account = this org account)

## Gemini / Discovery Engine app (created)

| Field | Value |
|-------|--------|
| Engine id | **`iot-asp-autoroute`** |
| Display name | IoT-ASP Autoroute |
| Resource name | `projects/1062135198697/locations/global/collections/default_collection/engines/iot-asp-autoroute` |
| Data store | `iot-asp-autoroute-kb` |
| Solution | `SOLUTION_TYPE_SEARCH` + `SEARCH_ADD_ON_LLM` |
| Console | [Discovery Engine engines](https://console.cloud.google.com/gen-app-builder/engines?project=bear-iot-asp-rec) |

Verify:

```bash
gcloud config set account betty@bearresearch.io
gcloud config set project bear-iot-asp-rec
TOKEN=$(gcloud auth print-access-token)
curl -sS -H "Authorization: Bearer $TOKEN" -H "x-goog-user-project: bear-iot-asp-rec" \
  "https://discoveryengine.googleapis.com/v1/projects/bear-iot-asp-rec/locations/global/collections/default_collection/engines/iot-asp-autoroute"
```

## Hybrid autoroute (v0)

**Primary loop:** sudden-frequency detection on-device → local rotate + telemetry → private GCS → **ADK agent** (Vertex Gemini) authors JSON param patches → nodes poll/apply (**autorotate the noises**).  
**One Gemini Enterprise seat** drives continuous monitor + audio-engineering control. Safari tabs do **not** call Gemini directly (respects **5 seats**).  
Carrier audio out remains **iOS native A2DP** ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md)).

See [adk-autoroute.md](adk-autoroute.md), [autoroute.md](autoroute.md), [colab-gemini-pipeline.md](colab-gemini-pipeline.md).

Primary agent path: **[Google Agent Development Kit (ADK)](https://docs.cloud.google.com/agent-builder/agent-development-kit/overview)** on Gemini Enterprise Agent Platform — not ad-hoc curl-only Vertex.

## 5-seat roster (template)

Seat emails and processing notes live in private `study/GEMINI_ENTERPRISE_ROSTER.md` (gitignored). Public template:

| Seat # | Role | Status |
|--------|------|--------|
| 1 | PI / admin | Active |
| 2–4 | Analyst / engineer | TBD |
| 5 | Reserve / contractor | TBD |

Credential **names only** in public config: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `IOT_ASP_GEMINI_ENGINE_ID=iot-asp-autoroute`. Keys via ADC / Colab `userdata` — never git.

## APIs enabled on `bear-iot-asp-rec`

- `aiplatform.googleapis.com` (Vertex / Agent Platform)
- `discoveryengine.googleapis.com` (Gemini Enterprise engines)
- `run.googleapis.com`, `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com` (Cloud Run deploy path)
- Cloud Storage (recordings + `meta/telemetry` + `meta/patches`)

## Docs / knowledge

- ADK overview: https://docs.cloud.google.com/agent-builder/agent-development-kit/overview  
- Context7 library: `/google/adk-python`  
- Firecrawl ingest: `reference/knowledge/adk/`  
- Living KB: `reference/knowledge-base/` + `scripts/kb_refresh.sh`

## Notion

See **[notion-links.md](notion-links.md)** for the hub URL and the 2026-09-07 workspace search log (kept as history). Hub: [IoT-ASP — Adaptive Signal Processing hub](https://www.notion.so/IoT-ASP-Adaptive-Signal-Processing-hub-3d5bf46958418109a303eb31342ff50d) (created 2026-09-08 for [Issue #19](https://github.com/team-project-pikachu/IoT-ASP/issues/19)). Do not put street addresses in public Notion-linked docs. Do not create a second hub page.

## Related

- [docs/autoroute.md](autoroute.md) — telemetry + patch schema + clamps  
- [docs/gcp-recordings.md](gcp-recordings.md) — private GCS layout (public ops; no keys)  
- [docs/iphone-dedicated-mode.md](iphone-dedicated-mode.md) — Chrome iOS org account + Hold checklist  
- [docs/notion-links.md](notion-links.md) — Notion search hits / hub follow-up  
- [docs/physics.md](physics.md) — NS / seismo-acoustic priors  
- [docs/awesome-iot-asp.md](awesome-iot-asp.md)
