"""Seismo-acoustic / linearized-acoustic priors for autoroute prompts (not on-phone CFD)."""

from __future__ import annotations

PRIORS: dict[str, str] = {
    "structure_borne": (
        "Structure-borne / seismo-acoustic coupling: chair/floor frames transmit "
        "broadband vibration; prefer pulse/shriek/burst over continuous hop when "
        "vibClass=physical."
    ),
    "linearized_acoustic": (
        "Linearized acoustic wave equation: near-ultrasonic air path (17–23 kHz) "
        "is weakly nonlinear at residential gain; keep vol soft-capped; band "
        "limits are hard constraints."
    ),
    "infra_felt": (
        "Infrasound honesty: Safari/BT cannot claim true <20 Hz audio; use LF "
        "accel energy as felt proxy → infra_mod / higher pulse duty."
    ),
    "sudden_freq": (
        "Sudden frequency onset (Δf or energy spike in-band): autorotate noise "
        "params (algo cycle + dwell/pulse/shriek jitter) then author a clamped "
        "GCS patch for the node."
    ),
}


def prior_text(keys: list[str] | None = None) -> str:
    if not keys:
        keys = list(PRIORS.keys())
    return "\n".join(f"- {k}: {PRIORS[k]}" for k in keys if k in PRIORS)
