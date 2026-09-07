"""ADK tools: telemetry read, patch write, clamps, priors, Colab handoff."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from . import gcs_io
from .clamps import CLAMPS, validate_patch
from .priors import prior_text
from .sudden_freq import author_sudden_freq_patch, is_sudden_freq_event

ENGINE_ID = os.environ.get("IOT_ASP_GEMINI_ENGINE_ID", "iot-asp-autoroute")


def read_telemetry(node_id: str) -> dict[str, Any]:
    """Read the latest telemetry JSON for a node from GCS (or dry-run mirror).

    Args:
        node_id: Field node id (e.g. node1).

    Returns:
        Dict with ok, path, and payload (or error).
    """
    prefix = f"meta/telemetry/{node_id}/"
    names = gcs_io.list_prefix(prefix)
    if not names:
        return {"ok": False, "error": f"no telemetry under {prefix}", "payload": None}
    latest = names[-1]
    payload = gcs_io.read_json(latest)
    return {"ok": True, "path": latest, "payload": payload}


def write_patch(node_id: str, patch_json: str) -> dict[str, Any]:
    """Validate clamps and write meta/patches/<nodeId>.json.

    Args:
        node_id: Field node id.
        patch_json: JSON string of param patch fields.

    Returns:
        Dict with ok, uri, message, and clamped patch.
    """
    try:
        raw = json.loads(patch_json) if isinstance(patch_json, str) else dict(patch_json)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid JSON: {exc}"}

    ok, msg, clamped = validate_patch(raw)
    if not ok:
        return {"ok": False, "error": msg, "patch": clamped}

    clamped.setdefault("engineId", ENGINE_ID)
    clamped.setdefault(
        "createdAt", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    uri = gcs_io.write_json(f"meta/patches/{node_id}.json", clamped)
    return {"ok": True, "uri": uri, "message": msg, "patch": clamped}


def list_safety_clamps() -> dict[str, Any]:
    """Expose band/gain/duty safety clamps to the model."""
    return {
        "clamps": CLAMPS,
        "vol_soft_max": CLAMPS["vol_soft_max"],
        "vol_hard_max": CLAMPS["vol_hard_max"],
        "band_hz": [17000, 23000],
        "cite": "Fletcher/Leighton JASA DOI 10.1121/1.5063819 — not medical claims",
    }


def seismo_acoustic_priors() -> dict[str, Any]:
    """Short NS / linearized-acoustic / earthquake-coupling priors for prompts."""
    return {"text": prior_text(), "keys": ["structure_borne", "linearized_acoustic", "infra_felt", "sudden_freq"]}


def colab_handoff_note(node_id: str, feature_hint: str = "spectra+vib") -> dict[str, Any]:
    """Emit a Colab ETL job note for Gemini seat analysis (no secrets).

    Args:
        node_id: Field node id.
        feature_hint: What Colab should compute (e.g. spectra+vib).
    """
    note = {
        "job": "iot_asp_colab_etl",
        "nodeId": node_id,
        "featureHint": feature_hint,
        "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "bear-iot-asp-rec"),
        "engineId": ENGINE_ID,
        "gcsPrefix": f"meta/features/{node_id}/",
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "auth": "Colab userdata GCP_SA_JSON only — never download SA JSON to Studio",
    }
    uri = gcs_io.write_json(f"meta/colab-jobs/{node_id}-latest.json", note)
    return {"ok": True, "uri": uri, "note": note}


def ingest_telemetry(telemetry_json: str) -> dict[str, Any]:
    """Ingest one heartbeat / suddenFreq event into meta/telemetry/<nodeId>/<ts>.json.

    Args:
        telemetry_json: Compact telemetry JSON from the public app beacon.
    """
    try:
        tel = json.loads(telemetry_json) if isinstance(telemetry_json, str) else dict(telemetry_json)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid JSON: {exc}"}

    node = str(tel.get("deviceId") or tel.get("nodeId") or "node1")
    ts = tel.get("ts") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    if isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(ts / 1000.0 if ts > 1e12 else ts, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H-%M-%SZ"
        )
    safe_ts = str(ts).replace(":", "-")
    path = f"meta/telemetry/{node}/{safe_ts}.json"
    uri = gcs_io.write_json(path, tel)
    out: dict[str, Any] = {"ok": True, "uri": uri, "path": path, "suddenFreq": is_sudden_freq_event(tel)}
    return out


def process_sudden_freq(node_id: str) -> dict[str, Any]:
    """Core loop helper: if latest telemetry is suddenFreq, author + write patch.

    Args:
        node_id: Field node id.
    """
    latest = read_telemetry(node_id)
    if not latest.get("ok") or not latest.get("payload"):
        return {"ok": False, "error": latest.get("error", "no payload")}
    tel = latest["payload"]
    if not is_sudden_freq_event(tel):
        return {"ok": True, "skipped": True, "reason": "not a suddenFreq event"}
    ok, msg, patch = author_sudden_freq_patch(tel)
    if not ok:
        return {"ok": False, "error": msg}
    written = write_patch(node_id, json.dumps(patch))
    return {"ok": written.get("ok"), "author": msg, "result": written}
