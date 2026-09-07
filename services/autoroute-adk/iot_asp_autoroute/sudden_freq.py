"""Sudden-frequency → autorotate patch heuristics (deterministic mock / ADK tool aid)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .clamps import ALLOWED_ALGOS, SCHEMA_VERSION, normalize_vol_ui_percent, validate_patch
from .priors import prior_text

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


def _next_algo(current: str, vib_class: str | None) -> str:
    cur = normalize_algo(current)
    vib = (vib_class or "none").lower()
    if vib == "physical":
        preferred = ("burst", "shriek_chirp", "am_gate")
    elif vib == "infra_felt":
        preferred = ("infra_mod", "am_gate", "burst")
    elif vib == "acoustic":
        preferred = ("am_gate", "hop", "shriek_sweep")
    else:
        preferred = ALGO_ROTATE
    if cur in preferred:
        i = preferred.index(cur)
        return preferred[(i + 1) % len(preferred)]
    return preferred[0]


def author_sudden_freq_patch(telemetry: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """
    Deterministic patch author for suddenFreq (dry-run / offline).
    Live Vertex/ADK may replace rationale; clamps always apply.
    """
    if telemetry.get("holdManual"):
        return False, "holdManual — refuse patch", {}

    node = str(telemetry.get("deviceId") or telemetry.get("nodeId") or "node1")
    algo = _next_algo(str(telemetry.get("algo") or "hop"), telemetry.get("vibClass"))
    peak = telemetry.get("peakHz")
    pulse = float(telemetry.get("pulseMs") or 80)
    shriek = float(telemetry.get("shriekMs") or 50)
    # Neighbor-safe jitter
    pulse = max(20.0, min(200.0, pulse + 10))
    shriek = max(20.0, min(120.0, shriek + 5))
    vol = normalize_vol_ui_percent(float(telemetry.get("vol") or 8))
    vol = min(vol, 12.0)

    rationale = (
        f"suddenFreq autorotate for {node}"
        + (f" @ {round(float(peak))} Hz" if peak is not None else "")
        + f"; vibClass={telemetry.get('vibClass') or 'none'}; "
        + "NS/linearized priors as constraints only"
    )
    patch: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "algo": algo if algo in ALLOWED_ALGOS else "hop",
        "fMin": float(telemetry.get("fMin") or 17000),
        "fMax": float(telemetry.get("fMax") or 23000),
        "vol": vol,
        "pulseMs": pulse,
        "shriekMs": shriek,
        "vibThreshold": float(telemetry.get("vibThreshold") or 0.15),
        "seedAction": "keep",
        "rationale": rationale,
        "priors": ["sudden_freq", "linearized_acoustic"],
        "engineId": "iot-asp-autoroute",
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger": "suddenFreq",
        "nodeId": node,
        "priorNotes": prior_text(["sudden_freq", "linearized_acoustic"]),
    }
    ok, msg, clamped = validate_patch(patch)
    return ok, msg, clamped
