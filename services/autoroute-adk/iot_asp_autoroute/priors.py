"""Seismo-acoustic / linearized-acoustic priors for autoroute prompts (not on-phone CFD).

Weights drive vib→algo routing; citations are constraints for Gemini/ADK prompts only.
Literature IDs from reference/LITERATURE.md (2026-09-07 pull) — no fabricated cites.
"""

from __future__ import annotations

from typing import Any

from .timestore import autoroute_timestore_prior

# Prompt blurbs (keys must stay in sync with VIB_ALGO_WEIGHTS / CITATIONS usage).
PRIORS: dict[str, str] = {
    "structure_borne": (
        "Structure-borne / seismo-acoustic coupling: chair/floor frames transmit "
        "broadband vibration; prefer pulse/shriek/burst over continuous hop when "
        "vibClass=physical. Cite arXiv:2211.03647 (seismo-acoustic nuisance) + "
        "seated WBV human–seat PMIDs (e.g. 27780424)."
    ),
    "linearized_acoustic": (
        "From compressible Navier–Stokes under small perturbations → linearized "
        "acoustic wave equation (1/c0^2)∂t²p' − ∇²p' = S (Lighthill-type sources). "
        "Near-ultrasonic air path 17–23 kHz is weakly nonlinear at residential gain; "
        "band limits are hard constraints. Cite arXiv:2307.01775, arXiv:2509.17986."
    ),
    "infra_felt": (
        "Infrasound honesty: Safari/BT cannot claim true <20 Hz audio; use LF "
        "accel energy as felt proxy → infra_mod / higher pulse duty. Optional "
        "TX band 10–20 Hz only when lfDriveCapable. Cite PMID 33940893 / "
        "DOI 10.1121/10.0003509; Fletcher VHFS ethics DOI 10.1121/1.5063819."
    ),
    "sudden_freq": (
        "Sudden frequency onset (Δf or energy spike in-band): autorotate noise "
        "params (algo cycle + dwell/pulse/shriek jitter) then author a clamped "
        "GCS patch for the node."
    ),
    "sound_burst": (
        "Environmental burst from micDiff in LF (<20 Hz) and/or US (>17 kHz) "
        "only — not mid-band speech/music. Formula: micDiff = micEnergy − α·outLevel "
        "(best-effort self-TX rejection; full AEC limited on iOS Chrome). "
        "While micDiff stays above a rolling baseline (hysteresis quiet window to exit), "
        "keep extreme shriek_chirp / shriek_sweep / burst + clamped dwell/vol/seed variance. "
        "bandBurst=lf|us|both; TX response 17–23 kHz default, 10–20 Hz only if lfDriveCapable. "
        "Hold/Manual freezes. Not on-device CFD."
    ),
    "navier_stokes_constraint": (
        "Do NOT claim full Navier–Stokes / CFD on-device. Use linearized acoustics "
        "and coupling analogies as soft priors only (docs/physics.md)."
    ),
}

# Soft multipliers when telemetry.soundBurst is true (bias shriek + contour-mirrors).
SOUND_BURST_ALGO_BIAS: dict[str, float] = {
    "shriek_chirp": 1.85,
    "shriek_sweep": 1.65,
    "burst": 1.75,
    "cry_mirror": 1.70,
    "siren_mirror": 1.68,
    "death_metal_mirror": 1.72,
    "am_gate": 0.75,
    "hop": 0.35,
    "infra_mod": 0.55,
}

# Burst-only baseline makes contour mirrors eligible before their bias is applied.
SOUND_BURST_MIRROR_BASELINE: dict[str, float] = {
    "cry_mirror": 0.30,
    "siren_mirror": 0.30,
    "death_metal_mirror": 0.30,
}

# Real IDs only — mirrored from reference/LITERATURE.md § NS / seismo-acoustic.
CITATIONS: list[dict[str, str]] = [
    {
        "id": "arxiv:2307.01775",
        "url": "https://arxiv.org/abs/2307.01775",
        "role": "aeroacoustics / quiescent linearized wave equation",
    },
    {
        "id": "arxiv:2509.17986",
        "url": "https://arxiv.org/abs/2509.17986",
        "role": "linearized compressible Navier–Stokes (cavity aeroacoustics)",
    },
    {
        "id": "arxiv:2211.03647",
        "url": "https://arxiv.org/abs/2211.03647",
        "role": "seismo-acoustic nuisance / induced seismicity coupling analogy",
    },
    {
        "id": "doi:10.1121/1.5063819",
        "url": "https://doi.org/10.1121/1.5063819",
        "role": "VHFS/US human effects Part I (exposure ethics, not medical claim)",
    },
    {
        "id": "doi:10.1121/10.0003509",
        "url": "https://doi.org/10.1121/10.0003509",
        "role": "wind-turbine infrasound annoyance / perception (felt <20 Hz context)",
    },
    {
        "id": "pmid:27780424",
        "url": "https://pubmed.ncbi.nlm.nih.gov/27780424/",
        "role": "human–seat coupling / structure-borne chair path",
    },
]

# Soft vib→algo weights (relative). Worker picks argmax / rotate among top set.
VIB_ALGO_WEIGHTS: dict[str, dict[str, float]] = {
    "physical": {
        "burst": 0.40,
        "shriek_chirp": 0.35,
        "am_gate": 0.25,
        "hop": 0.05,
        "shriek_sweep": 0.05,
        "infra_mod": 0.10,
    },
    "infra_felt": {
        "infra_mod": 0.45,
        "am_gate": 0.30,
        "burst": 0.25,
        "shriek_chirp": 0.15,
        "hop": 0.05,
        "shriek_sweep": 0.05,
    },
    "acoustic": {
        "am_gate": 0.40,
        "hop": 0.35,
        "shriek_sweep": 0.25,
        "shriek_chirp": 0.10,
        "burst": 0.05,
        "infra_mod": 0.02,
    },
    "none": {
        "hop": 0.50,
        "am_gate": 0.25,
        "shriek_chirp": 0.15,
        "burst": 0.05,
        "shriek_sweep": 0.05,
        "infra_mod": 0.02,
    },
}

# materialPreset soft multipliers on vib-class channel emphasis (docs/materials-engineering.md).
MATERIAL_CHANNEL_BIAS: dict[str, dict[str, float]] = {
    "handheld": {"acoustic": 1.2, "physical": 0.9, "infra_felt": 0.7, "none": 1.0},
    "table": {"acoustic": 1.0, "physical": 1.2, "infra_felt": 0.9, "none": 1.0},
    "chair": {"acoustic": 0.7, "physical": 1.3, "infra_felt": 1.4, "none": 1.0},
    "speaker": {"acoustic": 1.3, "physical": 0.8, "infra_felt": 0.6, "none": 1.0},
}

KNOWN_PRIOR_KEYS = frozenset(PRIORS.keys())
KNOWN_VIB_CLASSES = frozenset(VIB_ALGO_WEIGHTS.keys())
LF_BAND_HZ = (10.0, 20.0)
US_BAND_HZ = (17000.0, 23000.0)


def filter_prior_keys(keys: list[str] | None) -> list[str]:
    """Keep only known prior keys; drop nonsense (negative-control friendly)."""
    if not keys:
        return list(PRIORS.keys())
    return [k for k in keys if k in KNOWN_PRIOR_KEYS]


def prior_text(keys: list[str] | None = None) -> str:
    selected = filter_prior_keys(keys)
    if not selected:
        return ""
    return "\n".join(f"- {k}: {PRIORS[k]}" for k in selected)


def citations_brief() -> list[dict[str, str]]:
    return list(CITATIONS)


def citations_for_prompt() -> str:
    lines = []
    for c in CITATIONS:
        lines.append(f"- {c['id']}: {c['role']} ({c['url']})")
    return "\n".join(lines)


def normalize_vib_class(vib_class: str | None) -> str:
    v = (vib_class or "none").strip().lower()
    if v not in KNOWN_VIB_CLASSES:
        return "none"
    return v


def vib_algo_weights(
    vib_class: str | None,
    material_preset: str | None = None,
    *,
    sound_burst: bool = False,
) -> dict[str, float]:
    """Return algo→weight map for vib class, optionally scaled by material + soundBurst."""
    vib = normalize_vib_class(vib_class)
    weights = dict(VIB_ALGO_WEIGHTS[vib])
    preset = (material_preset or "").strip().lower()
    bias = MATERIAL_CHANNEL_BIAS.get(preset, {}).get(vib, 1.0)
    if bias != 1.0:
        weights = {a: w * bias for a, w in weights.items()}
    if sound_burst:
        for algo, baseline in SOUND_BURST_MIRROR_BASELINE.items():
            weights.setdefault(algo, baseline * bias)
        weights = {
            a: w * SOUND_BURST_ALGO_BIAS.get(a, 1.0) for a, w in weights.items()
        }
    return weights


def preferred_algos(
    vib_class: str | None,
    material_preset: str | None = None,
    *,
    top_n: int = 3,
    sound_burst: bool = False,
) -> tuple[str, ...]:
    """Ordered preferred wire-algos (highest weight first)."""
    weights = vib_algo_weights(vib_class, material_preset, sound_burst=sound_burst)
    ranked = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
    return tuple(a for a, _ in ranked[:top_n])


def next_algo_weighted(
    current: str | None,
    vib_class: str | None,
    material_preset: str | None = None,
    *,
    sound_burst: bool = False,
) -> str:
    """Rotate within preferred set for vib class (deterministic)."""
    preferred = preferred_algos(vib_class, material_preset, sound_burst=sound_burst)
    if not preferred:
        return "hop"
    cur = (current or "hop").strip()
    # Map UI aliases
    aliases = {"pulse": "am_gate", "shriek": "shriek_chirp"}
    cur = aliases.get(cur, cur)
    if cur in preferred:
        i = preferred.index(cur)
        return preferred[(i + 1) % len(preferred)]
    return preferred[0]


def lf_drive_capable(telemetry: dict[str, Any] | None) -> bool:
    """True when telemetry asserts LF 10–20 Hz TX is hardware-capable and armed."""
    if not telemetry:
        return False
    if telemetry.get("holdManual"):
        return False
    if telemetry.get("lfDriveCapable") is True:
        return True
    # Explicit arm + capable aliases
    if telemetry.get("lfArmed") and telemetry.get("lfDriveCapable") is not False:
        band = str(telemetry.get("band") or "").lower().replace(" ", "")
        if band in ("10-20", "10–20", "lf", "infra_tx"):
            return True
    return False


def prior_keys_for_event(
    vib_class: str | None,
    *,
    lf_capable: bool = False,
    sound_burst: bool = False,
) -> list[str]:
    vib = normalize_vib_class(vib_class)
    keys = ["sudden_freq", "linearized_acoustic", "navier_stokes_constraint"]
    if sound_burst:
        keys.insert(0, "sound_burst")
    if vib == "physical":
        keys.append("structure_borne")
    if vib == "infra_felt" or lf_capable:
        keys.append("infra_felt")
    out: list[str] = []
    for k in keys:
        if k not in out and k in KNOWN_PRIOR_KEYS:
            out.append(k)
    return out


def band_for_telemetry(telemetry: dict[str, Any]) -> tuple[str, float, float]:
    """
    Choose TX band tag + (fMin, fMax).
    LF 10–20 Hz only when capable AND vibClass is infra_felt (or band already LF).
    """
    vib = normalize_vib_class(telemetry.get("vibClass"))
    capable = lf_drive_capable(telemetry)
    band_in = str(telemetry.get("band") or "").lower().replace(" ", "")
    want_lf = capable and (
        vib == "infra_felt" or band_in in ("10-20", "10–20", "lf", "infra_tx")
    )
    if want_lf:
        lo, hi = LF_BAND_HZ
        # Prefer existing in-band values if present
        try:
            fmin = float(telemetry.get("fMin") or lo)
            fmax = float(telemetry.get("fMax") or hi)
        except (TypeError, ValueError):
            fmin, fmax = lo, hi
        fmin = max(lo, min(hi, fmin))
        fmax = max(lo, min(hi, fmax))
        if fmin >= fmax:
            fmin, fmax = lo, hi
        return "10-20", fmin, fmax
    lo, hi = US_BAND_HZ
    try:
        fmin = float(telemetry.get("fMin") or lo)
        fmax = float(telemetry.get("fMax") or hi)
    except (TypeError, ValueError):
        fmin, fmax = lo, hi
    return "17-23k", fmin, fmax


def duty_bias_for_vib(vib_class: str | None) -> dict[str, float]:
    """Pulse/shriek ms deltas for infra_felt aggression (algorithms.md)."""
    vib = normalize_vib_class(vib_class)
    if vib == "infra_felt":
        return {"pulseMs": 20.0, "shriekMs": 15.0}
    if vib == "physical":
        return {"pulseMs": 10.0, "shriekMs": 5.0}
    return {"pulseMs": 10.0, "shriekMs": 5.0}


def seismo_bundle() -> dict[str, Any]:
    """Full payload for ADK tool `seismo_acoustic_priors`."""
    return {
        "text": prior_text(),
        "keys": list(PRIORS.keys()),
        "weights": VIB_ALGO_WEIGHTS,
        "materialChannelBias": MATERIAL_CHANNEL_BIAS,
        "citations": CITATIONS,
        "lfBandHz": list(LF_BAND_HZ),
        "usBandHz": list(US_BAND_HZ),
        "timestore": autoroute_timestore_prior(),
        "honesty": (
            "LF accel is a felt proxy; true infrasound mic/TX requires lfDriveCapable. "
            "No full NS/CFD on-phone."
        ),
        "docs": ["docs/physics.md", "docs/algorithms.md", "reference/LITERATURE.md"],
    }
