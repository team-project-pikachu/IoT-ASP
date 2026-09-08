"""Colab ↔ ADK shared ETL: telemetry feature columns + SciPy vib anomaly.

Authoritative anomaly path lives in ``vib_anomaly`` (1 Hz preferred, quantum
0.0005 g). This module maps api-contract telemetry fields into feature JSON
written under ``meta/features/<deviceId>/`` for Gemini Enterprise / ADK.

Credential policy: env / Colab userdata **names** only — never embed secrets.

Sensor channels (accel / gyro / mic-spectrum) are projected when present so
Colab can ingest any vibration or sound carried on the wire / GCS JSONL.
Burst / micDiff field names stay aligned with the frontend burst→shriek path.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from .clamps import ALLOWED_ALGOS, SCHEMA_VERSION, normalize_vol_ui_percent, validate_patch
from .priors import SOUND_BURST_ALGO_BIAS
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
    "ax",
    "ay",
    "az",
    "absOmega",
    "omega",  # alias → absOmega
    "gx",
    "gy",
    "gz",
    "micEnergy",
    "outLevel",
    "micDiff",
    "micNet",  # alias → micDiff (frontend burst path)
    "bandEnergyLf",  # mic/spectrum energy f < 20 Hz
    "bandEnergyUs",  # mic/spectrum energy f > 17 kHz
    "bandBurst",  # lf | us | both | none
    "soundBurst",
    "soundBurstMeta",
    "extremeActive",
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
BAND_BURST_ALLOWED = frozenset({"lf", "us", "both", "none"})
ENGINE_ID_DEFAULT = "iot-asp-autoroute"
SAMPLE_HZ = 1.0
# micDiff = micEnergy − α · outLevel (align with docs/algorithms.md OUT_ALPHA ≈ 0.85)
MIC_DIFF_ALPHA = 0.85
# Quantize micDiff for stable features / evidence (0.1 dB steps)
MIC_DIFF_QUANTUM = 0.1


def _finite(v: Any, default: float | None = None) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(x):
        return default
    return x


def _mag3(x: float | None, y: float | None, z: float | None) -> float | None:
    if x is None and y is None and z is None:
        return None
    return math.sqrt((x or 0.0) ** 2 + (y or 0.0) ** 2 + (z or 0.0) ** 2)


def quantize_mic_diff(diff: float, quantum: float = MIC_DIFF_QUANTUM) -> float:
    q = quantum if quantum > 0 else MIC_DIFF_QUANTUM
    return round(diff / q) * q


def compute_mic_diff(
    telemetry: dict[str, Any],
    *,
    alpha: float = MIC_DIFF_ALPHA,
) -> float | None:
    """Return micDiff when present or derivable: micEnergy − α·outLevel."""
    for key in ("micDiff", "micNet"):
        if telemetry.get(key) is not None:
            d = _finite(telemetry.get(key))
            return quantize_mic_diff(d) if d is not None else None
    mic = _finite(telemetry.get("micEnergy"))
    out = _finite(telemetry.get("outLevel"))
    if mic is None or out is None:
        return None
    # Match frontend: when TX silent (out < -90 dB), no subtraction
    if out < -90.0:
        return quantize_mic_diff(mic)
    return quantize_mic_diff(mic - alpha * out)


def infer_band_burst(t: dict[str, Any]) -> str:
    """lf | us | both | none from explicit tag or LF/US band energies."""
    raw = str(t.get("bandBurst") or "").strip().lower()
    if raw in BAND_BURST_ALLOWED:
        return raw
    lf = _finite(t.get("bandEnergyLf"))
    us = _finite(t.get("bandEnergyUs"))
    # Heuristic thresholds: relative presence when energy reported (dB or linear).
    # Treat missing as absent; only flag when value is finite and elevated.
    lf_on = lf is not None and lf > -90.0 and (lf > -55.0 if lf < 0 else lf > 0.02)
    us_on = us is not None and us > -90.0 and (us > -55.0 if us < 0 else us > 0.02)
    if lf_on and us_on:
        return "both"
    if lf_on:
        return "lf"
    if us_on:
        return "us"
    if t.get("soundBurst") or t.get("extremeActive"):
        # Burst without band tags → assume US path (default TX band)
        return "us"
    return "none"


def normalize_telemetry(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize aliases to canonical api-contract keys; no PII fields."""
    t = dict(raw)
    t.setdefault("schemaVersion", SCHEMA_VERSION)
    if "absA" not in t and "a" in t:
        t["absA"] = t["a"]
    # Accel magnitude from axes when |a| missing
    if t.get("absA") is None:
        mag = _mag3(_finite(t.get("ax")), _finite(t.get("ay")), _finite(t.get("az")))
        if mag is not None:
            t["absA"] = mag
    if "absOmega" not in t and "omega" in t:
        t["absOmega"] = t["omega"]
    if t.get("absOmega") is None:
        om = _mag3(_finite(t.get("gx")), _finite(t.get("gy")), _finite(t.get("gz")))
        if om is not None:
            t["absOmega"] = om
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
    if "micDiff" not in t and t.get("micNet") is not None:
        t["micDiff"] = t["micNet"]
    # Frontend band energies may use micEnergyLf / micEnergyUs names
    if t.get("bandEnergyLf") is None and t.get("micEnergyLf") is not None:
        t["bandEnergyLf"] = t["micEnergyLf"]
    if t.get("bandEnergyUs") is None and t.get("micEnergyUs") is not None:
        t["bandEnergyUs"] = t["micEnergyUs"]
    # micDiff / bandBurst normalization (additive; optional on wire)
    md = compute_mic_diff(t)
    if md is not None:
        t["micDiff"] = md
    t["bandBurst"] = infer_band_burst(t)
    if "soundBurst" in t:
        t["soundBurst"] = bool(t["soundBurst"])
    if "extremeActive" in t:
        t["extremeActive"] = bool(t["extremeActive"])
    return t


def project_telemetry_columns(t: dict[str, Any]) -> dict[str, Any]:
    """Keep only contract-known columns (plus normalized absA / audioContextState)."""
    out: dict[str, Any] = {}
    for key in TELEMETRY_FEATURE_COLUMNS:
        if key in ("a", "ctxState", "omega", "micNet"):
            continue
        if key in t and t[key] is not None:
            out[key] = t[key]
    return out


def prior_hint(t: dict[str, Any]) -> str:
    """NS / seismo-acoustic style label from vib vs mic energy — not CFD."""
    abs_a = float(t.get("absA") or 0.0)
    mic = float(t.get("micEnergy") or 0.0)
    vib = str(t.get("vibClass") or "none")
    if t.get("soundBurst") or t.get("extremeActive"):
        return "sound_burst"
    if vib == "infra_felt":
        return "infra_felt"
    if vib == "physical" or abs_a > mic:
        return "structure_borne"
    if vib == "acoustic" or mic > abs_a:
        return "air_borne"
    return "linearized_acoustic"


def sensor_derived(t: dict[str, Any]) -> dict[str, Any]:
    """Compact derived accel / gyro / mic-band features for meta/features JSON."""
    abs_a = _finite(t.get("absA"), 0.0) or 0.0
    abs_w = _finite(t.get("absOmega"))
    mic_diff = _finite(t.get("micDiff"))
    band_burst = str(t.get("bandBurst") or "none")
    sound_burst = bool(t.get("soundBurst"))
    extreme = bool(t.get("extremeActive"))
    vib_burst = abs_a > float(t.get("vibThreshold") or 0.15)
    gyro_burst = abs_w is not None and abs_w > 0.8  # rad/s heuristic
    lf_us_burst = band_burst in ("lf", "us", "both")
    return {
        "accelMagG": abs_a,
        "accelAxesPresent": all(k in t and t[k] is not None for k in ("ax", "ay", "az")),
        "gyroMagRadS": abs_w,
        "gyroAxesPresent": all(k in t and t[k] is not None for k in ("gx", "gy", "gz")),
        "micDiff": mic_diff,
        "bandEnergyLf": _finite(t.get("bandEnergyLf")),
        "bandEnergyUs": _finite(t.get("bandEnergyUs")),
        "bandBurst": band_burst,
        "soundBurst": sound_burst,
        "extremeActive": extreme,
        "vibBurst": vib_burst,
        "gyroBurst": gyro_burst,
        "lfUsBandBurst": lf_us_burst,
        "shriekBiasEligible": bool(
            sound_burst or extreme or lf_us_burst or vib_burst or gyro_burst
        ),
    }


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
    sensors = sensor_derived(t)
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
            "priorKeys": [
                "structure_borne",
                "linearized_acoustic",
                "infra_felt",
                "sudden_freq",
                "sound_burst",
            ],
            "suddenFreqEvent": is_sudden_freq_event(t),
            "vibQuantumG": VIB_QUANTUM,
            "sampleHz": SAMPLE_HZ,
            "anomalySharedModule": "iot_asp_autoroute.vib_anomaly",
            "sensors": sensors,
            "micDiffAlpha": MIC_DIFF_ALPHA,
            "micDiffQuantum": MIC_DIFF_QUANTUM,
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


def _bias_algo_for_burst(current: str, telemetry: dict[str, Any]) -> str:
    """Prefer shriek/extreme family when sound/vib/gyro bursts in LF/US bands."""
    sensors = sensor_derived(telemetry)
    if not sensors["shriekBiasEligible"]:
        return current
    # Align response band hint: LF burst + capable → infra_mod soft preference
    if sensors.get("bandBurst") == "lf" and telemetry.get("lfDriveCapable"):
        return "infra_mod" if "infra_mod" in ALLOWED_ALGOS else current
    # Classic shriek/burst first; contour-mirrors (cry/siren/death_metal) as secondary
    classic = ("shriek_chirp", "shriek_sweep", "burst")
    mirrors = ("cry_mirror", "siren_mirror", "death_metal_mirror")
    pool = [a for a in classic if a in ALLOWED_ALGOS]
    if not pool:
        pool = [a for a in mirrors if a in ALLOWED_ALGOS]
    if not pool:
        return current
    ranked = sorted(
        pool,
        key=lambda a: (-SOUND_BURST_ALGO_BIAS.get(a, 0.0), a),
    )
    cur = normalize_algo(current)
    if cur in ranked:
        return ranked[(ranked.index(cur) + 1) % len(ranked)]
    return ranked[0]


def suggest_patch_stub(
    telemetry: dict[str, Any],
    *,
    engine_id: str = ENGINE_ID_DEFAULT,
) -> dict[str, Any]:
    """Heuristic patch **suggestion** — ADK worker must still clamp + write.

    Never treat this as authoritative ``meta/patches/`` output.
    Biases shriek/extreme when soundBurst / extremeActive / LF·US band / vib bursts.
    """
    t = normalize_telemetry(telemetry)
    if t.get("holdManual"):
        return {
            "ok": False,
            "refused": True,
            "reason": "holdManual",
            "suggestion": None,
        }
    # Ensure suddenFreq path fires for burst-only heartbeats
    t_for_author = dict(t)
    sensors = sensor_derived(t)
    if sensors["shriekBiasEligible"] and not t_for_author.get("suddenFreq"):
        t_for_author["suddenFreq"] = True
        t_for_author.setdefault("event", "soundBurst")
    ok, reason, patch = author_sudden_freq_patch(t_for_author)
    if not ok:
        return {"ok": False, "refused": False, "reason": reason, "suggestion": None}
    if sensors["shriekBiasEligible"] and patch:
        biased = _bias_algo_for_burst(str(patch.get("algo") or t.get("algo") or "hop"), t)
        patch["algo"] = biased if biased in ALLOWED_ALGOS else patch.get("algo")
        priors = list(patch.get("priors") or [])
        if "sound_burst" not in priors:
            priors.append("sound_burst")
        patch["priors"] = priors
        trigger = "extremeActive" if t.get("extremeActive") else (
            "soundBurst" if t.get("soundBurst") else "sensorBurst"
        )
        patch["trigger"] = trigger
        rationale = str(patch.get("rationale") or "")
        patch["rationale"] = (
            rationale
            + f"; shriekBias from {trigger} bandBurst={sensors.get('bandBurst')}"
            + f" micDiff={sensors.get('micDiff')}"
        )
        # Soft priorWeights overlay for evidence / Gemini
        weights = dict(patch.get("priorWeights") or {})
        for algo, mult in SOUND_BURST_ALGO_BIAS.items():
            if algo in weights:
                weights[algo] = round(float(weights[algo]) * mult, 4)
            else:
                weights[algo] = round(0.1 * mult, 4)
        patch["priorWeights"] = weights
    patch["engineId"] = engine_id
    patch.setdefault("schemaVersion", SCHEMA_VERSION)
    vok, vreason, clamped = validate_patch(patch)
    return {
        "ok": vok,
        "refused": False,
        "reason": reason if vok else vreason,
        "suggestion": clamped if vok else None,
        "note": "suggestion-only; ADK clamps before GCS patch write",
        "algoWhitelist": sorted(ALLOWED_ALGOS),
        "shriekBiasEligible": sensors["shriekBiasEligible"],
        "bandBurst": sensors.get("bandBurst"),
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


def sample_vib_gyro_sound_fixture(device_id: str = "node1") -> dict[str, Any]:
    """Synthetic accel + gyro + mic LF/US band + micDiff burst fixture (offline)."""
    mic_energy = -38.0
    out_level = -52.0
    mic_diff = quantize_mic_diff(mic_energy - MIC_DIFF_ALPHA * out_level)
    return {
        "schemaVersion": 1,
        "deviceId": device_id,
        "ts": "2026-09-08T00:30:00Z",
        "seed": 99,
        "algo": "hop",
        "peakHz": 18500,
        "suddenFreq": False,
        "suddenAuto": True,
        "suddenState": "idle",
        "geminiAutorouteFlag": False,
        "event": "soundBurst",
        "absA": 0.28,
        "ax": 0.12,
        "ay": -0.05,
        "az": 0.25,
        "absOmega": 1.15,
        "gx": 0.4,
        "gy": -0.9,
        "gz": 0.55,
        "micEnergy": mic_energy,
        "outLevel": out_level,
        "micDiff": mic_diff,
        "bandEnergyLf": -48.0,
        "bandEnergyUs": -36.0,
        "bandBurst": "both",
        "soundBurst": True,
        "soundBurstMeta": {
            "energyDelta": 14.0,
            "baselineDb": -62.0,
            "onsetDb": 8.0,
            "micDiff": mic_diff,
        },
        "extremeActive": True,
        "audioContextState": "running",
        "materialPreset": "chair",
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

    sensor_tel = sample_vib_gyro_sound_fixture()
    sensor_features = extract_features(sensor_tel, vib_series=series)
    sensor_suggestion = suggest_patch_stub(sensor_tel)
    sensors = sensor_features["derived"]["sensors"]

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
    sensor_missing = [
        c
        for c in (
            "ax",
            "ay",
            "az",
            "absOmega",
            "gx",
            "gy",
            "gz",
            "micDiff",
            "bandEnergyLf",
            "bandEnergyUs",
            "bandBurst",
            "soundBurst",
            "extremeActive",
            "outLevel",
        )
        if c not in sensor_features["telemetry"]
    ]
    shriek_ok = (
        sensor_suggestion.get("ok") is True
        and sensor_suggestion.get("shriekBiasEligible") is True
        and (sensor_suggestion.get("suggestion") or {}).get("algo")
        in (
            "shriek_chirp",
            "shriek_sweep",
            "burst",
            "infra_mod",
            "cry_mirror",
            "siren_mirror",
            "death_metal_mirror",
        )
    )
    return {
        "ok": features.get("anomaly", {}).get("ok") is True
        and suggestion.get("ok") is True
        and hold_block.get("refused") is True
        and not missing
        and not sensor_missing
        and shriek_ok
        and sensors.get("shriekBiasEligible") is True,
        "missingTelemetryColumns": missing,
        "sensorMissingColumns": sensor_missing,
        "featureColumnCount": len(features["telemetry"]),
        "sensorFeatureColumnCount": len(sensor_features["telemetry"]),
        "vibQuantumG": VIB_QUANTUM,
        "sampleHz": SAMPLE_HZ,
        "anomalyDisturbance": features["anomaly"].get("disturbance"),
        "anomalyFunctions": features["anomaly"].get("functions"),
        "sharedModule": "iot_asp_autoroute.vib_anomaly",
        "suggestionAlgo": (suggestion.get("suggestion") or {}).get("algo"),
        "sensorSuggestionAlgo": (sensor_suggestion.get("suggestion") or {}).get("algo"),
        "sensorShriekBias": sensor_suggestion.get("shriekBiasEligible"),
        "sensorBandBurst": sensors.get("bandBurst"),
        "sensorMicDiff": sensors.get("micDiff"),
        "holdManualRefused": hold_block.get("refused"),
        "features": features,
        "sensorFeatures": sensor_features,
        "suggestion": suggestion,
        "sensorSuggestion": sensor_suggestion,
        "holdBlock": hold_block,
    }
