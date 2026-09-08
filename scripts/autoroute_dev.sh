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
    "schemaVersion": 1,
    "deviceId": "node1",
    "algo": "hop",
    "peakHz": 19500,
    "suddenFreq": True,
    "absA": 0.12,
    "micEnergy": 0.03,
    "vibClass": "physical",
    "vol": 8,
    "fMin": 17000,
    "fMax": 23000,
    "holdManual": False,
})))
print("telemetry:", read_telemetry("node1"))
print("colab:", colab_handoff_note("node1"))
r = write_patch("node1", json.dumps({
    "schemaVersion": 1,
    "algo": "am_gate",
    "fMin": 17000,
    "fMax": 22000,
    "vol": 8,
    "pulseMs": 90,
    "shriekMs": 50,
    "vibThreshold": 0.2,
    "seedAction": "keep",
    "rationale": "dry-run physical→am_gate",
}))
print("patch:", r)
assert r.get("ok"), r
# vol_hard_max == 100 (UI percent). Mid-range OK; >100 must refuse.
# Legacy linear 0.5 → 50% is accepted (normalize_vol_ui_percent).
ok50, msg50, clamped50 = validate_patch({"algo": "hop", "vol": 50, "fMin": 17000, "fMax": 23000})
assert ok50 and clamped50.get("vol") == 50.0, (msg50, clamped50)
ok_lin, msg_lin, clamped_lin = validate_patch({"algo": "hop", "vol": 0.5, "fMin": 17000, "fMax": 23000})
assert ok_lin and clamped_lin.get("vol") == 50.0, (msg_lin, clamped_lin)
ok_hi, msg_hi, _ = validate_patch({"algo": "hop", "vol": 101, "fMin": 17000, "fMax": 23000})
assert not ok_hi, msg_hi
print("OK autoroute_dev dry-run")
PY
