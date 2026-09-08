"""Offline dry-run: suddenFreq → clamped patch without Vertex/ADK credentials."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow `python -m iot_asp_autoroute.dry_run` from services/autoroute-adk
_PKG = Path(__file__).resolve().parent
_ROOT = _PKG.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from iot_asp_autoroute import gcs_io  # noqa: E402
from iot_asp_autoroute.clamps import CLAMPS, validate_patch  # noqa: E402
from iot_asp_autoroute.sudden_freq import (  # noqa: E402
    author_sudden_freq_patch,
    is_sudden_freq_event,
)
from iot_asp_autoroute.tools import (  # noqa: E402
    ingest_telemetry,
    process_sudden_freq,
    write_patch,
)


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
        "vol": 100,
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


def _assert_clamp_negatives() -> None:
    """Negative controls aligned with vol_hard_max=100 and Hold/Manual."""
    assert CLAMPS["vol_hard_max"] == 100.0, CLAMPS
    assert CLAMPS["vol_soft_max"] == 100.0, CLAMPS

    ok50, msg50, c50 = validate_patch(
        {"algo": "hop", "vol": 50, "fMin": 17000, "fMax": 23000}
    )
    assert ok50 and c50.get("vol") == 50.0, (msg50, c50)

    ok_lin, msg_lin, c_lin = validate_patch(
        {"algo": "hop", "vol": 0.5, "fMin": 17000, "fMax": 23000}
    )
    assert ok_lin and c_lin.get("vol") == 50.0, (msg_lin, c_lin)

    ok_hi, msg_hi, _ = validate_patch(
        {"algo": "hop", "vol": 101, "fMin": 17000, "fMax": 23000}
    )
    assert not ok_hi and "hard max" in msg_hi, msg_hi

    ok_band, msg_band, _ = validate_patch(
        {"algo": "hop", "vol": 100, "fMin": 1000, "fMax": 23000}
    )
    assert not ok_band, msg_band


def _assert_hold_manual_wins(node: str) -> None:
    held = sample_sudden_freq_telemetry(node)
    held["holdManual"] = True
    held["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ing = ingest_telemetry(json.dumps(held))
    assert ing.get("ok"), ing
    assert not is_sudden_freq_event(held)
    authored = author_sudden_freq_patch(held)
    assert not authored[0] and "holdManual" in authored[1], authored
    proc = process_sudden_freq(node)
    assert proc.get("ok") is False and "holdManual" in str(proc.get("error")), proc
    refused = write_patch(
        node,
        json.dumps(
            {
                "schemaVersion": 1,
                "algo": "hop",
                "fMin": 17000,
                "fMax": 23000,
                "vol": 80,
            }
        ),
    )
    assert refused.get("ok") is False and "holdManual" in str(refused.get("error")), refused


def main() -> int:
    gcs_io.DRY_RUN = True  # type: ignore[attr-defined]
    os.environ["IOT_ASP_AUTOROUTE_DRY_RUN"] = "1"
    node = os.environ.get("IOT_ASP_DRY_NODE", "node1")
    tel = sample_sudden_freq_telemetry(node)
    print("== IoT-ASP autoroute dry-run ==")
    print(f"project={os.environ.get('GOOGLE_CLOUD_PROJECT', 'bear-iot-asp-rec')}")
    print(f"dry_root={gcs_io.DRY_ROOT}")
    print(f"vol_hard_max={CLAMPS['vol_hard_max']}")
    print(f"suddenFreq={is_sudden_freq_event(tel)}")

    _assert_clamp_negatives()
    print("clamp negatives: OK (vol 50/legacy 0.5 accept; vol 101 + OOB fMin refuse)")

    ing = ingest_telemetry(json.dumps(tel))
    print("ingest:", json.dumps(ing, indent=2))

    ok, msg, patch = author_sudden_freq_patch(tel)
    print(f"author ok={ok} msg={msg}")
    print("patch draft:", json.dumps(patch, indent=2))
    assert ok and patch.get("vol") == 100.0, (msg, patch)

    proc = process_sudden_freq(node)
    print("process_sudden_freq:", json.dumps(proc, indent=2))
    assert proc.get("ok"), proc

    _assert_hold_manual_wins(node)
    print("holdManual negatives: OK (author/process/write_patch refuse)")

    # Restore a non-hold patch so artifact remains usable for inspect
    clear = sample_sudden_freq_telemetry(node)
    clear["holdManual"] = False
    clear["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ingest_telemetry(json.dumps(clear))
    process_sudden_freq(node)

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
