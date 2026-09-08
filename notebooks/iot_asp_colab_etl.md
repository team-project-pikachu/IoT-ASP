# IoT-ASP Colab live GCS — sensor features (#26)

Public notebook — **no site PII**. Secrets via Colab `userdata` **names** only
(`GCP_SA_JSON`, `IOT_ASP_GCS_BUCKET`, `LIVE_GCS`); values are never printed.

Pipeline: `meta/telemetry/<node>/` (objects + `.jsonl`) → `iot_asp_autoroute.features_live`
(shared `colab_etl` + SciPy `vib_anomaly`, accel / gyro / `micDiff` / `bandBurst` sensors) →
`meta/features/<node>/<ts>.json` → Gemini Enterprise (`iot-asp-autoroute`) / ADK agent.
See `docs/specs/26-colab-live-gcs-features.md` and `docs/colab-gemini-pipeline.md`.

```python
# @title Secrets by NAME only (Colab userdata) — never paste values into git/chat
import os, tempfile

try:
    from google.colab import userdata  # type: ignore
except ImportError:  # not on Colab → env only
    userdata = None


def _secret(getter):
    try:
        return getter() if userdata is not None else None
    except Exception:  # SecretNotFoundError / NotebookAccessError → treat as unset
        return None


NODE = os.environ.get("IOT_ASP_NODE", "node1")
LIMIT = int(os.environ.get("IOT_ASP_LIMIT", "200"))

bucket = _secret(lambda: userdata.get("IOT_ASP_GCS_BUCKET"))
live_flag = _secret(lambda: userdata.get("LIVE_GCS"))
sa_json = _secret(lambda: userdata.get("GCP_SA_JSON"))

if bucket:
    os.environ["IOT_ASP_GCS_BUCKET"] = bucket
os.environ["LIVE_GCS"] = "1" if (str(live_flag or os.environ.get("LIVE_GCS", "0")) == "1" and bucket) else "0"
LIVE = os.environ["LIVE_GCS"] == "1"
# gcs_io reads these at import: dry-run mirror unless LIVE
os.environ["IOT_ASP_AUTOROUTE_DRY_RUN"] = "0" if LIVE else "1"
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "bear-iot-asp-rec")

if sa_json and LIVE:
    _fd, _path = tempfile.mkstemp(prefix="iot-asp-sa-", suffix=".json")
    with os.fdopen(_fd, "w") as fh:
        fh.write(sa_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _path  # path only, value never printed
del sa_json

print("bucket set:", bool(bucket), "| live:", int(LIVE), "| node:", NODE, "| limit:", LIMIT)
```

```python
# @title Install the shared module from the repo (or point sys.path at a checkout)
import os, subprocess, sys

REPO_DIR = os.environ.get("IOT_ASP_REPO_DIR", "/content/IoT-ASP")
if not os.path.isdir(REPO_DIR):
    subprocess.run(["git", "clone", "--depth", "1", "https://github.com/team-project-pikachu/IoT-ASP.git", REPO_DIR], check=True)

PKG_ROOT = os.path.join(REPO_DIR, "services/autoroute-adk")
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)
# Runtime deps only (numpy/scipy ship with Colab; google-cloud-storage for LIVE writes)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "numpy>=1.26,<3", "scipy>=1.14,<1.18", "google-cloud-storage>=2.14,<4"], check=False)
print("pkg root on sys.path:", PKG_ROOT in sys.path)
```

```python
# @title Telemetry → sensor features (shared module; SciPy vib anomaly is authoritative)
from iot_asp_autoroute import features_live

if not LIVE:
    # Offline / dry-run: seed 12 synthetic heartbeats into the local mirror so the run is self-contained
    features_live._seed_demo(NODE)

res = features_live.run_live(NODE, LIMIT, live=os.environ.get("LIVE_GCS") == "1")
```

This notebook writes **only** `meta/features/<node>/<ts>.json` and never writes `meta/patches/`
(`features_live.assert_not_patch_path` raises before every write). The ADK worker
(`tools.write_patch`) clamps and writes patches; Hold / Manual still wins there. `shriekBias` is a
feature hint, not a patch. Features are never authoritative.

```python
# @title Result URIs (file:// in dry-run, gs:// when LIVE)
print("uri:", res.get("uri"))
print("object:", res.get("object"), "| sourceCount:", res.get("sourceCount"), "| live:", res.get("live"), "| ok:", res.get("ok"))
print("featureKeys:", res.get("featureKeys"))
```

Generated in lockstep with `iot_asp_colab_etl.ipynb` (tests/test_features_live.py FL-12 checks the two stay in sync).
