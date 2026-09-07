"""Offline dry-run: suddenFreq → clamped patch without Vertex/ADK credentials."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow `python -m iot_asp_autoroute.dry_run` from services/autoroute-adk
_PKG = Path(__file__).resolve().parent
_ROOT = _PKG.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from iot_asp_autoroute import gcs_io  # noqa: E402
from iot_asp_autoroute.sudden_freq import (  # noqa: E402
    author_sudden_freq_patch,
    is_sudden_freq_event,
)
from iot_asp_autoroute.tools import ingest_telemetry, process_sudden_freq  # noqa: E402


def sample_sudden_freq_telemetry(node_id: str = "node1") -> dict:
    return {
        "schemaVersion": 1,
        "deviceId": node_id,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": 42,
        "algo": "hop",
        "peakHz": 19500,
        "suddenFreq": True,
        "absA": 0.12,
        "micEnergy": 0.03,
        "audioContextState": "running",
        "fMin": 17000,
        "fMax": 23000,
        "vol": 8,
        "pulseMs": 80,
        "shriekMs": 50,
        "vibThreshold": 0.15,
        "vibClass": "physical",
        "holdManual": False,
        "suddenAuto": True,
        "suddenState": "rotate",
        "geminiAutorouteFlag": True,
        "event": "suddenFreq",
    }


def main() -> int:
    gcs_io.DRY_RUN = True  # type: ignore[attr-defined]
    # Force dry mirror for this process
    import os

    os.environ["IOT_ASP_AUTOROUTE_DRY_RUN"] = "1"
    # Reload flag via module state already set at import — rewrite through write path
    node = os.environ.get("IOT_ASP_DRY_NODE", "node1")
    tel = sample_sudden_freq_telemetry(node)
    print("== IoT-ASP autoroute dry-run ==")
    print(f"project={os.environ.get('GOOGLE_CLOUD_PROJECT', 'bear-iot-asp-rec')}")
    print(f"dry_root={gcs_io.DRY_ROOT}")
    print(f"suddenFreq={is_sudden_freq_event(tel)}")

    ing = ingest_telemetry(json.dumps(tel))
    print("ingest:", json.dumps(ing, indent=2))

    # Deterministic author (mocks Vertex/Gemini)
    ok, msg, patch = author_sudden_freq_patch(tel)
    print(f"author ok={ok} msg={msg}")
    print("patch draft:", json.dumps(patch, indent=2))

    proc = process_sudden_freq(node)
    print("process_sudden_freq:", json.dumps(proc, indent=2))

    patch_path = gcs_io.DRY_ROOT / f"meta/patches/{node}.json"
    if patch_path.is_file():
        print(f"wrote {patch_path}")
        print(patch_path.read_text(encoding="utf-8"))
        print("DRY-RUN OK")
        return 0
    print("DRY-RUN FAIL: patch file missing", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
