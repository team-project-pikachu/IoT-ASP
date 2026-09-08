"""Material-dependent vibration channel selection (#6).

Chooses which sensing path(s) may drive hop rotation:

* **physical** — DeviceMotion / linear accelerometer (#4)
* **acoustic** — mic spectrum energy (#5)
* **both** / **none** — arming combinations

Canonical policy table. Frontend mirror: ``public/vib-channel-select.js``
(keep ``MATERIAL_CHANNEL_SELECT`` keys/flags in sync; tests assert parity).

Soft algo weights remain in ``priors.MATERIAL_CHANNEL_BIAS``; this module is the
hard arming gate (which channels may set ``vibClass`` / force hops).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

MATERIAL_PRESETS: tuple[str, ...] = ("handheld", "table", "chair", "speaker")
CHANNEL_MODES: tuple[str, ...] = ("physical", "acoustic", "both", "none")

# Issue #6 / docs/specs/04-06-vibration-channels.md Goal table.
# speaker defaults to both (enclosure contact + optional accel); over-air BT
# radiate becomes acoustic-only when DeviceMotion is unavailable/denied.
MATERIAL_CHANNEL_SELECT: dict[str, dict[str, Any]] = {
    "handheld": {
        "mode": "both",
        "armPhysical": True,
        "armAcoustic": True,
        "prefer": "acoustic",
        "setup": "Handheld / free body (acoustic-leaning)",
    },
    "table": {
        "mode": "physical",
        "armPhysical": True,
        "armAcoustic": False,
        "prefer": "physical",
        "setup": "Phone-on-table / rigid mount",
    },
    "chair": {
        "mode": "physical",
        "armPhysical": True,
        "armAcoustic": False,
        "prefer": "physical",
        "setup": "Chair-taped node 3 (infra_felt via physical)",
    },
    "speaker": {
        "mode": "both",
        "armPhysical": True,
        "armAcoustic": True,
        "prefer": "acoustic",
        "setup": "Soundcore enclosure contact / BT radiate (acoustic prefer)",
    },
}

DEFAULT_PRESET = "handheld"


@dataclass(frozen=True)
class ChannelSelection:
    """Resolved arming for one materialPreset (+ optional sensor availability)."""

    material_preset: str
    mode: str
    arm_physical: bool
    arm_acoustic: bool
    prefer: str
    setup: str
    fallback_reason: str | None = None

    def allows_vib_class(self, vib_class: str | None) -> bool:
        """Whether ``updateVibClass`` / detectors may accept this class."""
        cls = (vib_class or "none").strip().lower()
        if cls in ("", "none"):
            return True
        if cls in ("physical", "infra_felt"):
            return self.arm_physical
        if cls == "acoustic":
            return self.arm_acoustic
        return False

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Wire / JS camelCase for arming flags
        d["armPhysical"] = d.pop("arm_physical")
        d["armAcoustic"] = d.pop("arm_acoustic")
        d["materialPreset"] = d.pop("material_preset")
        d["fallbackReason"] = d.pop("fallback_reason")
        return d


def normalize_material_preset(preset: str | None) -> str:
    p = (preset or DEFAULT_PRESET).strip().lower()
    if p not in MATERIAL_CHANNEL_SELECT:
        return DEFAULT_PRESET
    return p


def _mode_from_arms(arm_physical: bool, arm_acoustic: bool) -> str:
    if arm_physical and arm_acoustic:
        return "both"
    if arm_physical:
        return "physical"
    if arm_acoustic:
        return "acoustic"
    return "none"


def select_channels(
    material_preset: str | None,
    *,
    physical_available: bool | None = None,
    acoustic_available: bool | None = None,
) -> ChannelSelection:
    """Return channel arming for a material preset, with optional availability fallbacks.

    ``physical_available`` / ``acoustic_available``:
      * ``None`` — do not apply availability (policy defaults only)
      * ``True`` / ``False`` — AND with policy arms (permission denied / missing sensor)
    """
    preset = normalize_material_preset(material_preset)
    base = MATERIAL_CHANNEL_SELECT[preset]
    arm_p = bool(base["armPhysical"])
    arm_a = bool(base["armAcoustic"])
    reasons: list[str] = []

    if physical_available is False and arm_p:
        arm_p = False
        reasons.append("physical_unavailable")
    if acoustic_available is False and arm_a:
        arm_a = False
        reasons.append("acoustic_unavailable")

    # If preferred channel died, keep the other when still armed by policy+availability.
    prefer = str(base["prefer"])
    if prefer == "physical" and not arm_p and arm_a:
        prefer = "acoustic"
        reasons.append("prefer_fallback_acoustic")
    elif prefer == "acoustic" and not arm_a and arm_p:
        prefer = "physical"
        reasons.append("prefer_fallback_physical")

    mode = _mode_from_arms(arm_p, arm_a)
    return ChannelSelection(
        material_preset=preset,
        mode=mode,
        arm_physical=arm_p,
        arm_acoustic=arm_a,
        prefer=prefer if mode != "none" else "none",
        setup=str(base["setup"]),
        fallback_reason=",".join(reasons) if reasons else None,
    )


def selection_table() -> dict[str, dict[str, Any]]:
    """Material → default selection rows (no availability applied)."""
    return {
        k: select_channels(k).as_dict()
        for k in MATERIAL_PRESETS
    }


def vib_channel_select_bundle() -> dict[str, Any]:
    """Payload fragment for ADK / docs tooling."""
    return {
        "presets": list(MATERIAL_PRESETS),
        "modes": list(CHANNEL_MODES),
        "defaults": selection_table(),
        "docs": [
            "docs/specs/04-06-vibration-channels.md",
            "docs/materials-engineering.md",
            "public/vib-channel-select.js",
        ],
        "hooks": {
            "physical": "#4 DeviceMotion → updateVibClass('physical'|'infra_felt') / forceHopFromShake",
            "acoustic": "#5 mic spectrum → updateVibClass('acoustic') / acousticBurst",
            "gate": "updateVibClass must call allowsVibClass / armPhysical|armAcoustic",
        },
    }
