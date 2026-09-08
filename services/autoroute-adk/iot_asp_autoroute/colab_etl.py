"""Colab ↔ ADK shared ETL: telemetry feature columns + SciPy vib anomaly.

Authoritative anomaly path lives in ``vib_anomaly`` (1 Hz preferred, quantum
0.0005 g). This module maps api-contract telemetry fields into feature JSON
written under ``meta/features/<deviceId>/`` for Gemini Enterprise / ADK.

Credential policy: env / Colab userdata **names** only — never embed secrets.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .clamps import ALLOWED_ALGOS, SCHEMA_VERSION, normalize_vol_ui_percent, validate_patch
from .sudden_freq import author_sudden_freq_patch, is_sudden_freq_event, normalize_algo
from .vib_anomaly import (
    VIB_QUANTUM,
    detect_disturbances,
    detect_from_telemetry_points,
    synthetic_demo_series,
)

# Feature / telemetry columns aligned with docs/api-contract.md (schemaVersion 1).
# ★ = required on wire heartbeat; others optional but preserved when present.
TELEMETRY_FEATURE_COLUMNS: tuple[str, ...] = (
    "schemaVersion",  # ★
    "deviceId",  # ★
    "ts",  # ★
    "seed",
    "algo",  # ★
    "peakHz",
    "suddenFreq",  # ★
    "suddenFreqMeta",
    "suddenAuto",
    "suddenState",
    "geminiAutorouteFlag",
    "event",
    "absA",
    "a",  # alias → absA
    "micEnergy",
    "audioContextState",
    "ctxState",  # alias → audioContextState
    "materialPreset",
    "fMin",
    "fMax",
    "band",
    "lfDriveCapable",
    "lfArmed",
    "power",
    "nightNY",
    "vol",
    "pulseMs",
    "shriekMs",
    "vibThreshold",
    "vibClass",
    "holdManual",
)

VIB_CLASS_ALLOWED = frozenset({"none", "physical", "acoustic", "infra_felt"})
BAND_ALLOWED = frozenset({"17-23k", "10-20"})
ENGINE_ID_DEFAULT = "iot-asp-autoroute"
SAMPLE_HZ = 1.0


def normalize_telemetry(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize aliases to canonical api-contract keys; no PII fields."""
    t = dict(raw)
    t.setdefault("schemaVersion", SCHEMA_VERSION)
    if "absA" not in t and "a" in t:
        t["absA"] = t["a"]
    if "audioContextState" not in t and "ctxState" in t:
        t["audioContextState"] = t["ctxState"]
    if "deviceId" not in t and "nodeId" in t:
        t["deviceId"] = t["nodeId"]
    if "algo" in t:
        t["algo"] = normalize_algo(str(t["algo"]))
    vib = str(t.get("vibClass") or "none").lower()
    if vib not in VIB_CLASS_ALLOWED:
        vib = "none"
    t["vibClass"] = vib
    band = str(t.get("band") or "17-23k").replace(" ", "")
    if band not in BAND_ALLOWED:
        band = "17-23k"
    t["band"] = band
    if "vol" in t and t["vol"] is not None:
        try:
            t["vol"] = normalize_vol_ui_percent(float(t["vol"]))
        except (TypeError, ValueError):
            t["vol"] = 100.0
    return t


def project_telemetry_columns(t: dict[str, Any]) -> dict[str, Any]:
    """Keep only contract-known columns (plus normalized absA / audioContextState)."""
    out: dict[str, Any] = {}
    for key in TELEMETRY_FEATURE_COLUMNS:
        if key in ("a", "ctxState"):
            continue
        if key in t and t[key] is not None:
            out[key] = t[key]
    return out


def prior_hint(t: dict[str, Any]) -> str:
    """NS / seismo-acoustic style label from vib vs mic energy — not CFD."""
    abs_a = float(t.get("absA") or 0.0)
    mic = float(t.get("micEnergy") or 0.0)
    vib = str(t.get("vibClass") or "none")
    if vib == "infra_felt":
        return "infra_felt"
    if vib == "physical" or abs_a > mic:
        return "structure_borne"
    if vib == "acoustic" or mic > abs_a:
        return "air_borne"
    return "linearized_acoustic"


def extract_features(
    telemetry: dict[str, Any],
    *,
    vib_series: list[float] | None = None,
    engine_id: str = ENGINE_ID_DEFAULT,
) -> dict[str, Any]:
    """Build feature JSON for ``meta/features/<deviceId>/<ts>.json``.

    SciPy anomaly uses shared ``vib_anomaly`` (1 Hz / 0.0005 g quantum).
    """
    t = normalize_telemetry(telemetry)
    cols = project_telemetry_columns(t)
    node = str(t.get("deviceId") or "node1")
    anomaly: dict[str, Any]
    if vib_series is not None:
        anomaly = detect_disturbances(
            vib_series, quantum=VIB_QUANTUM, sample_hz=SAMPLE_HZ
        )
    else:
        anomaly = detect_from_telemetry_points([t])
        anomaly["sampleHz"] = SAMPLE_HZ

    features = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": "iot_asp_features",
        "deviceId": node,
        "ts": t.get("ts")
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engineId": engine_id,
        "telemetry": cols,
        "derived": {
            "priorHint": prior_hint(t),
            "priorKeys": ["structure_borne", "linearized_acoustic", "infra_felt", "sudden_freq"],
            "suddenFreqEvent": is_sudden_freq_event(t),
            "vibQuantumG": VIB_QUANTUM,
            "sampleHz": SAMPLE_HZ,
            "anomalySharedModule": "iot_asp_autoroute.vib_anomaly",
        },
        "anomaly": {
            "ok": anomaly.get("ok"),
            "n": anomaly.get("n"),
            "disturbance": anomaly.get("disturbance"),
            "peaks": anomaly.get("peaks"),
            "last": anomaly.get("last"),
            "mad": anomaly.get("mad"),
            "quantum": anomaly.get("quantum", VIB_QUANTUM),
            "sampleHz": anomaly.get("sampleHz", SAMPLE_HZ),
            "engine": anomaly.get("engine"),
            "functions": anomaly.get("functions"),
        },
        "credentialPolicy": "userdata-or-env-refs-only",
    }
    return features


def suggest_patch_stub(
    telemetry: dict[str, Any],
    *,
    engine_id: str = ENGINE_ID_DEFAULT,
) -> dict[str, Any]:
    """Heuristic patch **suggestion** — ADK worker must still clamp + write.

    Never treat this as authoritative ``meta/patches/`` output.
    """
    t = normalize_telemetry(telemetry)
    if t.get("holdManual"):
        return {
            "ok": False,
            "refused": True,
            "reason": "holdManual",
            "suggestion": None,
        }
    ok, reason, patch = author_sudden_freq_patch(t)
    if not ok:
        return {"ok": False, "refused": False, "reason": reason, "suggestion": None}
    patch["engineId"] = engine_id
    patch.setdefault("schemaVersion", SCHEMA_VERSION)
    # Defense-in-depth: validate with shared clamps (worker remains source of truth)
    vok, vreason, clamped = validate_patch(patch)
    return {
        "ok": vok,
        "refused": False,
        "reason": reason if vok else vreason,
        "suggestion": clamped if vok else None,
        "note": "suggestion-only; ADK clamps before GCS patch write",
        "algoWhitelist": sorted(ALLOWED_ALGOS),
    }


def sample_telemetry_fixture(device_id: str = "node1") -> dict[str, Any]:
    """Offline fixture matching api-contract heartbeat (no PII)."""
    return {
        "schemaVersion": 1,
        "deviceId": device_id,
        "ts": "2026-09-07T23:00:00Z",
        "seed": 42,
        "algo": "hop",
        "peakHz": 19500,
        "suddenFreq": True,
        "suddenFreqMeta": {"flux": 12.4, "bandDb": -42.0},
        "suddenAuto": True,
        "suddenState": "rotate",
        "geminiAutorouteFlag": True,
        "event": "suddenFreq",
        "absA": 0.12,
        "micEnergy": 0.03,
        "audioContextState": "running",
        "materialPreset": "table",
        "fMin": 17000,
        "fMax": 23000,
        "band": "17-23k",
        "lfDriveCapable": False,
        "lfArmed": False,
        "power": "ac120",
        "nightNY": False,
        "vol": 100,
        "pulseMs": 80,
        "shriekMs": 50,
        "vibThreshold": 0.15,
        "vibClass": "physical",
        "holdManual": False,
    }


def offline_dry_run() -> dict[str, Any]:
    """Run feature extract + anomaly + patch stub without GCS/Vertex."""
    tel = sample_telemetry_fixture()
    series = synthetic_demo_series(60)
    features = extract_features(tel, vib_series=series)
    suggestion = suggest_patch_stub(tel)
    hold_tel = dict(tel)
    hold_tel["holdManual"] = True
    hold_block = suggest_patch_stub(hold_tel)
    missing = [
        c
        for c in (
            "schemaVersion",
            "deviceId",
            "ts",
            "algo",
            "suddenFreq",
            "band",
            "vibClass",
            "absA",
            "holdManual",
        )
        if c not in features["telemetry"]
    ]
    return {
        "ok": features.get("anomaly", {}).get("ok") is True
        and suggestion.get("ok") is True
        and hold_block.get("refused") is True
        and not missing,
        "missingTelemetryColumns": missing,
        "featureColumnCount": len(features["telemetry"]),
        "vibQuantumG": VIB_QUANTUM,
        "sampleHz": SAMPLE_HZ,
        "anomalyDisturbance": features["anomaly"].get("disturbance"),
        "anomalyFunctions": features["anomaly"].get("functions"),
        "sharedModule": "iot_asp_autoroute.vib_anomaly",
        "suggestionAlgo": (suggestion.get("suggestion") or {}).get("algo"),
        "holdManualRefused": hold_block.get("refused"),
        "features": features,
        "suggestion": suggestion,
        "holdBlock": hold_block,
    }
