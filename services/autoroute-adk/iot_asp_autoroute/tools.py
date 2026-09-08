"""ADK tools: telemetry read, patch write, clamps, priors, Colab handoff."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from . import fleet_log, gcs_io
from .clamps import CLAMPS, SCHEMA_VERSION, validate_patch
from .colab_etl import TELEMETRY_FEATURE_COLUMNS
from .mic_diff import hw_limits_report as _hw_limits_report
from .priors import seismo_bundle
from .sudden_freq import author_sudden_freq_patch, is_sudden_freq_event
from .vib_anomaly import VIB_QUANTUM, detect_disturbances, detect_from_telemetry_points

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


def _latest_hold_manual(node_id: str) -> bool:
    """True when latest telemetry for node has holdManual set (human freeze)."""
    latest = read_telemetry(node_id)
    if not latest.get("ok") or not latest.get("payload"):
        return False
    return bool(latest["payload"].get("holdManual"))


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

    # Hold / Manual wins: refuse remote patch writes while human freeze is set.
    if raw.get("holdManual") or _latest_hold_manual(node_id):
        return {
            "ok": False,
            "error": "holdManual — refuse patch",
            "patch": raw,
        }

    ok, msg, clamped = validate_patch(raw)
    if not ok:
        return {"ok": False, "error": msg, "patch": clamped}

    clamped.setdefault("schemaVersion", SCHEMA_VERSION)
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
    """NS / linearized-acoustic / seismo-acoustic priors + vib→algo weights + cites."""
    return seismo_bundle()


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
        "sharedAnomalyModule": "iot_asp_autoroute.vib_anomaly",
        "vibQuantumG": VIB_QUANTUM,
        "sampleHz": 1.0,
        "telemetryFeatureColumns": list(TELEMETRY_FEATURE_COLUMNS),
        "notebook": "notebooks/iot_asp_colab_etl.ipynb",
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

    tel.setdefault("schemaVersion", SCHEMA_VERSION)
    # Accept absA / a and audioContextState / ctxState aliases from the static app
    if "absA" not in tel and "a" in tel:
        tel["absA"] = tel["a"]
    if "audioContextState" not in tel and "ctxState" in tel:
        tel["audioContextState"] = tel["ctxState"]
    if "suddenFreq" not in tel:
        tel["suddenFreq"] = is_sudden_freq_event(tel)
    tel = fleet_log.enrich_telemetry(tel)  # #22: PII scrub + band/power/nightNY/lf* tags before any write

    node = str(tel.get("deviceId") or tel.get("nodeId") or "node1")
    ts = tel.get("ts") or tel.get("t") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    if isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(ts / 1000.0 if ts > 1e12 else ts, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H-%M-%SZ"
        )
    safe_ts = str(ts).replace(":", "-")
    path = f"meta/telemetry/{node}/{safe_ts}.json"
    uri = gcs_io.write_json(path, tel)
    log = fleet_log.write_log_record(
        node, fleet_log.log_record("info", "ingest", tel, msg=f"piiDropped={tel.get('piiDropped', 0)}")
    )
    out: dict[str, Any] = {
        "ok": True,
        "uri": uri,
        "path": path,
        "suddenFreq": is_sudden_freq_event(tel),
        "log": {"ok": log.get("ok"), "path": log.get("path"), "mode": log.get("mode")},
    }
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

    def _log(level: str, event: str, msg: str = "") -> dict[str, Any]:
        # #22: one structured record per decision; write_log_record never raises.
        return fleet_log.write_log_record(node_id, fleet_log.log_record(level, event, tel, msg=msg))

    if tel.get("holdManual"):
        _log("warn", "hold_refuse", "holdManual — refuse patch")
        return {"ok": False, "error": "holdManual — refuse patch", "skipped": True}
    if not is_sudden_freq_event(tel):
        _log("debug", "skipped", "not a suddenFreq event")
        return {"ok": True, "skipped": True, "reason": "not a suddenFreq event"}
    ok, msg, patch = author_sudden_freq_patch(tel)
    if not ok:
        _log("error", "patch_refused", msg)
        return {"ok": False, "error": msg}
    written = write_patch(node_id, json.dumps(patch))
    if written.get("ok"):
        _log("info", "patch_authored", str(written.get("message") or msg))
    else:
        _log("error", "patch_refused", str(written.get("error") or msg))
    return {"ok": written.get("ok"), "author": msg, "result": written}


def fleet_log_summary(node_id: str, date: str | None = None) -> dict[str, Any]:
    """Aggregate the node's structured fleet log for one UTC date (#22).

    Args:
        node_id: Field node id (e.g. node1).
        date: YYYY-MM-DD (UTC partition). Defaults to today UTC. A NY night spans two
            UTC dates — call twice (D and D+1) to cover it.

    Returns:
        Dict with ok, date, summary (aggregate_records output; count 0 when no records).
    """
    day = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        records = fleet_log.read_log_records(node_id, day)
        summary = fleet_log.aggregate_records(records, window_s=300, node=node_id)
    except Exception as exc:  # noqa: BLE001 - tool must not raise into the agent loop
        return {"ok": False, "date": day, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "date": day, "summary": summary}


def live_features(node_id: str, limit: int = 200) -> dict[str, Any]:
    """Project the last `limit` telemetry points (accel/gyro/micDiff sensors) into meta/features/<nodeId>/<ts>.json (#26).

    Dry-run mirror unless env LIVE_GCS == "1" and IOT_ASP_GCS_BUCKET is set. Never writes meta/patches
    (features_live.assert_not_patch_path guards every write); shriekBias is a hint, not a patch.

    Args:
        node_id: Field node id (e.g. node1).
        limit: Newest telemetry points to consume (objects and .jsonl lines).
    """
    from .features_live import run_live

    return run_live(str(node_id), int(limit))


def hw_limits_report() -> dict[str, Any]:
    """HW-limited leftovers for #25 — full AEC, LF mic, LF TX, alpha calibration; never blocks redeploys.

    Returns:
        Dict with issue, status, blocksRedeploy, nativeCompanionIssue, docs, and the four limits
        (full_aec, lf_mic, lf_tx, alpha_calibration) pointing at docs/algorithms.md,
        docs/iphone-bluetooth.md and the native companion path (#9).
    """
    return _hw_limits_report()
