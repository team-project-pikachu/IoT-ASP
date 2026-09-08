# GCP recordings + autoroute objects

**Public ops note** for project `bear-iot-asp-rec`. Use an **org Google account** for Gemini Enterprise / GCP (`gcloud`, Colab userdata, Discovery Engine). Do not put API keys or personal Gmail addresses in this repo.

Private bucket names, IAM grants, and site-specific upload checklists live in the private study repo (`IoT-ASP-study`).

## Project

| Field | Value |
|-------|--------|
| Project ID | `bear-iot-asp-rec` |
| Gemini Enterprise engine | `iot-asp-autoroute` |
| Preferred org account (CLI / Chrome) | `betty@bearresearch.io` |

## Object layout (convention)

Private Cloud Storage holds both **session recordings** and the **autoroute control plane**:

```text
gs://<private-bucket>/
  node1/<YYYYMMDD>/…          # MediaRecorder exports + JSON sidecars
  node2/…
  meta/telemetry/<deviceId>/  # compact heartbeats (schemaVersion 1)
  meta/patches/<deviceId>.json
  meta/colab-jobs/…
  meta/features/…
```

Bucket name and public-access-prevention settings are private; never make the recordings bucket world-readable.

## Autoroute ↔ recordings

| Path | Writer | Consumer |
|------|--------|----------|
| `meta/telemetry/…` | Phone beacon / ingest | ADK tools, Colab ETL |
| `meta/patches/<id>.json` | ADK `write_patch` (clamped) | Phone `GET` poll / apply |
| `node*/…/*.webm` | Lab upload script | Gemini Enterprise seat analysis |

Wire schemas: [api-contract.md](api-contract.md). Agent package: [adk-autoroute.md](adk-autoroute.md).

## Chrome iOS (dedicated nodes)

On Chrome for iOS, set the **active Google account** to the org account `betty@bearresearch.io` before opening Gemini Enterprise / GCP-tied surfaces (Colab, Console). Fleet checklist: [iphone-dedicated-mode.md](iphone-dedicated-mode.md).

## Local dry-run (no GCS)

```bash
bash scripts/autoroute_dev.sh
```

Writes under `.autoroute-dry/` (gitignored). No Vertex keys required.

## Related

- [gemini-enterprise.md](gemini-enterprise.md) — seats / engine id (credential **names** only)
- [autoroute.md](autoroute.md) — suddenFreq control loop
- [colab-gemini-pipeline.md](colab-gemini-pipeline.md) — features → patch stubs
