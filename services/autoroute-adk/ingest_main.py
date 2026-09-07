"""Optional HTTP ingest stub for Cloud Functions / Cloud Run (telemetry → GCS).

Deploy separately; local dry-run uses scripts/autoroute_dev.sh instead.
Expects ADC / runtime SA — no keys in source.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Lightweight entry so CF can `from main import ingest` after packaging tools.


def ingest(request: Any) -> tuple[str, int, dict[str, str]]:
    """Cloud Functions HTTP (Gen2) style handler."""
    # Deferred import so dry-run does not need this module
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from iot_asp_autoroute.tools import ingest_telemetry, process_sudden_freq

    if request.method == "OPTIONS":
        return ("", 204, {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST,OPTIONS", "Access-Control-Allow-Headers": "Content-Type"})

    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        body = {}
    if not body and request.data:
        try:
            body = json.loads(request.data.decode("utf-8"))
        except Exception:
            return (json.dumps({"ok": False, "error": "invalid JSON"}), 400, {"Content-Type": "application/json"})

    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "bear-iot-asp-rec")
    result = ingest_telemetry(json.dumps(body))
    node = str(body.get("deviceId") or body.get("nodeId") or "node1")
    if result.get("suddenFreq") and os.environ.get("IOT_ASP_AUTOROUTE_ON_INGEST", "1") not in ("0", "false"):
        result["patch"] = process_sudden_freq(node)
    return (
        json.dumps(result),
        200 if result.get("ok") else 400,
        {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
    )
