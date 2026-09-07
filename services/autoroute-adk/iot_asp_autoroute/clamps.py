"""Safety clamps for autoroute patches (schemaVersion 1 — UI-percent vol)."""

from __future__ import annotations

from typing import Any

ALLOWED_ALGOS = frozenset(
    {"hop", "am_gate", "shriek_chirp", "shriek_sweep", "burst", "infra_mod"}
)

# vol is UI percent matching public/index.html slider (0–12 soft).
CLAMPS = {
    "fMin": (17000.0, 23000.0),
    "fMax": (17000.0, 23000.0),
    "vol_soft_max": 12.0,
    "vol_hard_max": 20.0,
    "pulseMs": (20.0, 200.0),
    "shriekMs": (20.0, 120.0),
    "vibThreshold": (0.01, 2.0),
}

SCHEMA_VERSION = 1


def normalize_vol_ui_percent(vol: float) -> float:
    """Legacy linear gain (≤1) → UI percent; values >1 already treated as percent."""
    if vol <= 1.0:
        return vol * 100.0
    return vol


def validate_patch(patch: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """Return (ok, message, clamped_patch)."""
    out = dict(patch)
    out.setdefault("schemaVersion", SCHEMA_VERSION)
    algo = out.get("algo", "hop")
    if algo not in ALLOWED_ALGOS:
        return False, f"algo not allowed: {algo}", out

    for key, (lo, hi) in (
        ("fMin", CLAMPS["fMin"]),
        ("fMax", CLAMPS["fMax"]),
        ("pulseMs", CLAMPS["pulseMs"]),
        ("shriekMs", CLAMPS["shriekMs"]),
        ("vibThreshold", CLAMPS["vibThreshold"]),
    ):
        if key in out and out[key] is not None:
            try:
                v = float(out[key])
            except (TypeError, ValueError):
                return False, f"{key} not numeric", out
            if v < lo or v > hi:
                return False, f"{key}={v} outside [{lo},{hi}]", out
            out[key] = v

    if "vol" in out and out["vol"] is not None:
        try:
            vol = normalize_vol_ui_percent(float(out["vol"]))
        except (TypeError, ValueError):
            return False, "vol not numeric", out
        if vol > CLAMPS["vol_hard_max"]:
            return False, f"vol={vol} exceeds hard max {CLAMPS['vol_hard_max']}", out
        if vol > CLAMPS["vol_soft_max"]:
            out["vol"] = CLAMPS["vol_soft_max"]
            out.setdefault("rationale", "")
            out["rationale"] = (out["rationale"] + " | soft-clamped vol").strip(" |")
        else:
            out["vol"] = max(0.0, vol)

    fmin, fmax = out.get("fMin"), out.get("fMax")
    if fmin is not None and fmax is not None and float(fmin) >= float(fmax):
        return False, "fMin must be < fMax", out

    return True, "ok", out
