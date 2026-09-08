"""Safety clamps for autoroute patches (schemaVersion 1 — UI-percent vol)."""

from __future__ import annotations

import math
from typing import Any

ALLOWED_ALGOS = frozenset(
    {"hop", "am_gate", "shriek_chirp", "shriek_sweep", "burst", "infra_mod"}
)

# Dual TX bands (C6): default ultrasonic; optional LF when patch/telemetry band=10-20.
BAND_US = (17000.0, 23000.0)
BAND_LF = (10.0, 20.0)

# vol is UI percent matching public/index.html slider (0–100 max practical Web Audio).
# Soft == hard: autoroute may drive full slider; Hold/Manual freezes remote patches.
# BT absolute volume + speaker DSP still limit SPL — clamps only bound the app gain path.
# Fleet is continuous 120 V AC (C5) — no battery-duty vol caps.
CLAMPS = {
    "vol_soft_max": 100.0,
    "vol_hard_max": 100.0,
    "pulseMs": (20.0, 200.0),
    "shriekMs": (20.0, 120.0),
    "vibThreshold": (0.01, 2.0),
}

SCHEMA_VERSION = 1


def band_limits(patch: dict[str, Any]) -> tuple[float, float]:
    """Return (lo, hi) Hz for fMin/fMax from band tag or inferred fMin."""
    band = str(patch.get("band") or "").lower().replace(" ", "")
    if band in ("10-20", "10–20", "lf", "infra_tx"):
        return BAND_LF
    if band in ("17-23k", "17–23k", "us", "ultrasonic"):
        return BAND_US
    try:
        fmin = float(patch.get("fMin") or BAND_US[0])
    except (TypeError, ValueError):
        fmin = BAND_US[0]
    if fmin <= 100:
        return BAND_LF
    return BAND_US


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

    flo, fhi = band_limits(out)
    if flo == BAND_LF[0]:
        out.setdefault("band", "10-20")
    else:
        out.setdefault("band", "17-23k")

    for key in ("fMin", "fMax"):
        if key in out and out[key] is not None:
            try:
                v = float(out[key])
            except (TypeError, ValueError):
                return False, f"{key} not numeric", out
            if not math.isfinite(v):
                return False, f"{key} not finite", out
            if v < flo or v > fhi:
                return False, f"{key}={v} outside [{flo},{fhi}] for band {out.get('band')}", out
            out[key] = v

    for key, (lo, hi) in (
        ("pulseMs", CLAMPS["pulseMs"]),
        ("shriekMs", CLAMPS["shriekMs"]),
        ("vibThreshold", CLAMPS["vibThreshold"]),
    ):
        if key in out and out[key] is not None:
            try:
                v = float(out[key])
            except (TypeError, ValueError):
                return False, f"{key} not numeric", out
            if not math.isfinite(v):
                return False, f"{key} not finite", out
            if v < lo or v > hi:
                return False, f"{key}={v} outside [{lo},{hi}]", out
            out[key] = v

    if "vol" in out and out["vol"] is not None:
        try:
            vol = normalize_vol_ui_percent(float(out["vol"]))
        except (TypeError, ValueError):
            return False, "vol not numeric", out
        if not math.isfinite(vol):
            return False, "vol not finite", out
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
