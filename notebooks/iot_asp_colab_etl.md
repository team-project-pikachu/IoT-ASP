# IoT-ASP Colab ETL (public — no site PII)

Open in Google Colab after cloning this repo. Secrets via **userdata names only**.  
See `docs/colab-gemini-pipeline.md`. Shared SciPy path: `iot_asp_autoroute.vib_anomaly` (1 Hz, 0.0005 g).

Accel / gyro / mic-spectrum (incl. `micDiff`, band energy &lt;20 Hz / &gt;17 kHz, `soundBurst` / `extremeActive`) are projected by `iot_asp_autoroute.colab_etl`.

```python
# @title Offline bootstrap + shared ADK imports
from __future__ import annotations
import json, os, sys
from pathlib import Path

CANDIDATES = [Path.cwd(), Path.cwd().parent, Path("/content/IoT-ASP"), Path("/content")]
ROOT = None
for base in CANDIDATES:
    adk = base / "services" / "autoroute-adk"
    if (adk / "iot_asp_autoroute" / "vib_anomaly.py").is_file():
        ROOT = base
        sys.path.insert(0, str(adk))
        break
assert ROOT, "clone IoT-ASP so services/autoroute-adk is importable"

from iot_asp_autoroute.colab_etl import (
    TELEMETRY_FEATURE_COLUMNS,
    extract_features,
    offline_dry_run,
    sample_telemetry_fixture,
    sample_vib_gyro_sound_fixture,
    suggest_patch_stub,
)
from iot_asp_autoroute.vib_anomaly import VIB_QUANTUM, synthetic_demo_series

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "bear-iot-asp-rec")
ENGINE_ID = os.environ.get("IOT_ASP_GEMINI_ENGINE_ID", "iot-asp-autoroute")
LIVE_GCS = os.environ.get("LIVE_GCS", "0") == "1"

# @title Feature extract + SciPy anomaly (shared with ADK)
tel = sample_telemetry_fixture("node1")
series = synthetic_demo_series(60)
features = extract_features(tel, vib_series=series, engine_id=ENGINE_ID)
print("cols", sorted(features["telemetry"].keys()), "quantum", VIB_QUANTUM)
print("anomaly", features["anomaly"]["disturbance"], features["anomaly"]["functions"])

# @title Synthetic vib + gyro + sound (offline)
sensor_tel = sample_vib_gyro_sound_fixture("node1")
sensor_feat = extract_features(sensor_tel, vib_series=series, engine_id=ENGINE_ID)
sensor_sug = suggest_patch_stub(sensor_tel, engine_id=ENGINE_ID)
print("sensors", sensor_feat["derived"]["sensors"])
print("shriekBias", sensor_sug.get("shriekBiasEligible"), (sensor_sug.get("suggestion") or {}).get("algo"))
assert sensor_sug["ok"] and sensor_sug["shriekBiasEligible"]
assert (sensor_sug.get("suggestion") or {}).get("algo") in (
    "shriek_chirp", "shriek_sweep", "burst", "infra_mod",
    "cry_mirror", "siren_mirror", "death_metal_mirror",
)

# @title Patch suggestion stub (ADK still clamps + writes patches)
sug = suggest_patch_stub(tel, engine_id=ENGINE_ID)
hold = suggest_patch_stub({**tel, "holdManual": True}, engine_id=ENGINE_ID)
assert sug["ok"] and hold["refused"]
assert offline_dry_run()["ok"]

# @title Live GCS (Colab userdata only — set LIVE_GCS=1)
# from google.colab import userdata
# sa_json = userdata.get("GCP_SA_JSON")  # never download to Studio
# bucket = userdata.get("IOT_ASP_GCS_BUCKET")
# → read meta/telemetry/ → write meta/features/ only (never meta/patches/)
print("LIVE_GCS", LIVE_GCS, "feature_col_count", len(TELEMETRY_FEATURE_COLUMNS))
```

Offline CI:

```bash
python3 scripts/colab_etl_dry_run.py
```
