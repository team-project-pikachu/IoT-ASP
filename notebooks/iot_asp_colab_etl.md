# IoT-ASP Colab ETL stub (public — no site PII)
# Open in Google Colab. Secrets via userdata only.

```python
# @title Auth (Colab userdata only — never paste SA JSON into git/chat)
from google.colab import userdata
import json, os, tempfile
from google.oauth2 import service_account
from google.cloud import storage

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "bear-iot-asp-rec")
ENGINE_ID = os.environ.get("IOT_ASP_GEMINI_ENGINE_ID", "iot-asp-autoroute")
BUCKET = userdata.get("IOT_ASP_GCS_BUCKET")  # private bucket name
sa_json = userdata.get("GCP_SA_JSON")

creds = service_account.Credentials.from_service_account_info(json.loads(sa_json))
client = storage.Client(project=PROJECT, credentials=creds)
print("project", PROJECT, "engine", ENGINE_ID, "bucket", BUCKET)

# @title Feature extract from latest telemetry (sketch)
def latest_telemetry(node_id: str):
    blobs = list(client.list_blobs(BUCKET, prefix=f"meta/telemetry/{node_id}/"))
    blobs = sorted(blobs, key=lambda b: b.name, reverse=True)
    if not blobs:
        return None
    return json.loads(blobs[0].download_as_text())

# Heuristics only — NS/seismo priors as labels, not CFD
def vib_features(t):
    if not t:
        return {}
    abs_a = float(t.get("absA") or 0)
    mic = float(t.get("micEnergy") or 0)
    vib = t.get("vibClass") or "none"
    return {
        "peakHz": t.get("peakHz"),
        "absA": abs_a,
        "micEnergy": mic,
        "vibClass": vib,
        "priorHint": "structure_borne" if abs_a > mic else "air_borne",
        "engineId": ENGINE_ID,
    }

# Write features → Gemini Enterprise / ADK agent consumes
# client.bucket(BUCKET).blob(f"meta/features/node1/latest.json").upload_from_string(...)
print("stub ready — wire generateContent / ADK invoke next")
```

See `docs/colab-gemini-pipeline.md`.
