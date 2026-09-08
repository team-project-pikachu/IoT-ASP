"""Sudden-frequency → autorotate patch heuristics (deterministic mock / ADK tool aid)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .clamps import ALLOWED_ALGOS, SCHEMA_VERSION, normalize_vol_ui_percent, validate_patch
from .priors import (
    band_for_telemetry,
    citations_brief,
    duty_bias_for_vib,
    filter_prior_keys,
    lf_drive_capable,
    next_algo_weighted,
    preferred_algos,
    prior_keys_for_event,
    prior_text,
    vib_algo_weights,
)

ALGO_ROTATE = ("hop", "am_gate", "shriek_chirp", "shriek_sweep", "burst")

UI_TO_WIRE = {
    "hop": "hop",
    "pulse": "am_gate",
    "shriek": "shriek_chirp",
    "am_gate": "am_gate",
    "shriek_chirp": "shriek_chirp",
    "shriek_sweep": "shriek_sweep",
    "burst": "burst",
    "infra_mod": "infra_mod",
}


def normalize_algo(algo: str | None) -> str:
    if not algo:
        return "hop"
    return UI_TO_WIRE.get(str(algo), str(algo))


def is_sudden_freq_event(telemetry: dict[str, Any]) -> bool:
    """True when phone flagged gemini autoroute / sudden rotate state."""
    if telemetry.get("holdManual"):
        return False
    if telemetry.get("suddenFreq") is True:
        return True
    if telemetry.get("geminiAutorouteFlag"):
        return True
    if telemetry.get("event") in ("suddenFreq", "sudden_freq", "spectrum_onset", "mic_onset"):
        return True
    state = str(telemetry.get("suddenState") or "").lower()
    return state in ("rotate", "onset")


def _next_algo(current: str, vib_class: str | None, material_preset: str | None = None) -> str:
    """Weighted vib→algo rotate (NS/seismo priors); falls back to preferred tuple."""
    return next_algo_weighted(current, vib_class, material_preset)


def author_sudden_freq_patch(telemetry: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """
    Deterministic patch author for suddenFreq (dry-run / offline).
    Live Vertex/ADK may replace rationale; clamps always apply.
    Uses NS / seismo-acoustic vib→algo weights; gates LF 10–20 Hz when capable.
    """
    if telemetry.get("holdManual"):
        return False, "holdManual — refuse patch", {}

    # Negative control: explicit nonsense prior keys on telemetry must be ignored.
    raw_priors = telemetry.get("priors")
    if isinstance(raw_priors, list):
        _ = filter_prior_keys([str(x) for x in raw_priors])

    node = str(telemetry.get("deviceId") or telemetry.get("nodeId") or "node1")
    material = telemetry.get("materialPreset")
    vib = telemetry.get("vibClass")
    algo = _next_algo(str(telemetry.get("algo") or "hop"), vib, material)
    peak = telemetry.get("peakHz")
    pulse = float(telemetry.get("pulseMs") or 80)
    shriek = float(telemetry.get("shriekMs") or 50)
    bias = duty_bias_for_vib(vib)
    pulse = max(20.0, min(200.0, pulse + bias["pulseMs"]))
    shriek = max(20.0, min(120.0, shriek + bias["shriekMs"]))
    # Preserve / request max practical Web Audio gain (UI %); clamps enforce ≤100.
    vol = normalize_vol_ui_percent(float(telemetry.get("vol") or 100))
    vol = min(vol, 100.0)

    lf_ok = lf_drive_capable(telemetry)
    band, fmin, fmax = band_for_telemetry(telemetry)
    prior_keys = prior_keys_for_event(vib, lf_capable=lf_ok)
    weights = vib_algo_weights(vib, material)
    preferred = preferred_algos(vib, material)

    rationale = (
        f"suddenFreq autorotate for {node}"
        + (f" @ {round(float(peak))} Hz" if peak is not None else "")
        + f"; vibClass={vib or 'none'}; band={band}; "
        + f"weights→{algo} among {list(preferred)}; "
        + "NS/linearized/seismo priors as constraints only"
    )
    if band == "10-20":
        rationale += "; LF 10–20 Hz gated (lfDriveCapable)"

    cite_ids = [c["id"] for c in citations_brief()[:4]]
    patch: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "algo": algo if algo in ALLOWED_ALGOS else "hop",
        "band": band,
        "fMin": fmin,
        "fMax": fmax,
        "vol": vol,
        "pulseMs": pulse,
        "shriekMs": shriek,
        "vibThreshold": float(telemetry.get("vibThreshold") or 0.15),
        "seedAction": "keep",
        "rationale": rationale,
        "priors": prior_keys,
        "priorWeights": {a: round(weights.get(a, 0.0), 4) for a in preferred},
        "literature": cite_ids,
        "engineId": "iot-asp-autoroute",
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger": "suddenFreq",
        "nodeId": node,
        "priorNotes": prior_text(prior_keys),
        "lfDriveCapable": lf_ok,
    }
    if material:
        patch["materialPreset"] = material
    ok, msg, clamped = validate_patch(patch)
    return ok, msg, clamped
