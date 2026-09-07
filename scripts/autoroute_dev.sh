#!/usr/bin/env bash
# Local dry-run for IoT-ASP autoroute (no GCP / ADK install required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export IOT_ASP_AUTOROUTE_DRY_RUN=1
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-bear-iot-asp-rec}"
export IOT_ASP_GEMINI_ENGINE_ID="${IOT_ASP_GEMINI_ENGINE_ID:-iot-asp-autoroute}"
export PYTHONPATH="${ROOT}/services/autoroute-adk${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"

# Prefer package dry_run if present
if python3 -c 'import iot_asp_autoroute.dry_run' 2>/dev/null; then
  python3 -m iot_asp_autoroute.dry_run
  exit 0
fi

python3 - <<'PY'
import json
from iot_asp_autoroute.tools import (
    colab_handoff_note,
    list_safety_clamps,
    read_telemetry,
    seismo_acoustic_priors,
    write_patch,
    ingest_telemetry,
)
from iot_asp_autoroute.clamps import validate_patch

print("clamps:", list_safety_clamps())
print("priors keys:", list(seismo_acoustic_priors().keys()))
print("ingest:", ingest_telemetry(json.dumps({
    "deviceId": "node1",
    "algo": "hop",
    "peakHz": 19500,
    "absA": 0.12,
    "micEnergy": 0.03,
    "vibClass": "physical",
    "vol": 0.08,
    "fMin": 17000,
    "fMax": 23000,
    "holdManual": False,
})))
print("telemetry:", read_telemetry("node1"))
print("colab:", colab_handoff_note("node1"))
r = write_patch("node1", json.dumps({
    "algo": "am_gate",
    "fMin": 17000,
    "fMax": 22000,
    "vol": 0.08,
    "pulseMs": 90,
    "shriekMs": 50,
    "vibThreshold": 0.2,
    "seedAction": "keep",
    "rationale": "dry-run physical→am_gate",
}))
print("patch:", r)
assert r.get("ok"), r
ok, msg, _ = validate_patch({"algo": "hop", "vol": 0.5, "fMin": 17000, "fMax": 23000})
assert not ok, msg
print("OK autoroute_dev dry-run")
PY
