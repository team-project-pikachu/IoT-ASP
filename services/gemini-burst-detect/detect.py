"""Gemini Enterprise / Vertex acoustic event detector stub (M8).

Does NOT call paid APIs. Wire live `gcloud ai` / Vertex only after owner auth
(betty@bearresearch.io) + 1Password `dev` keys.

Event classes: sound_burst | glass_shatter | unknown
Wire keys match Swift `AcousticDetectResult` (camelCase).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class AcousticEventClass(str, Enum):
    SOUND_BURST = "sound_burst"
    GLASS_SHATTER = "glass_shatter"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DetectResult:
    burst: bool
    event_class: AcousticEventClass
    confidence: float
    escalate_db: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "burst": self.burst,
            "eventClass": self.event_class.value,
            "confidence": self.confidence,
            "escalateDb": self.escalate_db,
        }


def _first_present(features: Mapping[str, Any], *keys: str) -> Any:
    """Return the first key that is present (even if the value is 0/False)."""
    for key in keys:
        if key in features:
            return features[key]
    return None


def detect(features: Mapping[str, Any], *, onset_db: float = 9.0, glass_rise_ms_max: float = 80.0) -> DetectResult:
    """Heuristic stub mirroring native StubBurstDetectClient."""
    energy_raw = _first_present(features, "energyDeltaDb", "energy_delta_db")
    energy = 0.0 if energy_raw is None else float(energy_raw)
    rise_raw = _first_present(features, "riseMs", "rise_ms")
    rise_ms = 999.0 if rise_raw is None else float(rise_raw)
    hint_raw = _first_present(features, "eventClassHint", "event_class_hint")
    hint_str = "unknown" if hint_raw is None else str(hint_raw)
    try:
        hint = AcousticEventClass(hint_str)
    except ValueError:
        hint = AcousticEventClass.UNKNOWN

    if energy < onset_db:
        return DetectResult(False, AcousticEventClass.UNKNOWN, 0.1, 0.0)

    if hint == AcousticEventClass.GLASS_SHATTER:
        classified = AcousticEventClass.GLASS_SHATTER if rise_ms <= glass_rise_ms_max else AcousticEventClass.SOUND_BURST
    elif hint == AcousticEventClass.SOUND_BURST:
        classified = AcousticEventClass.SOUND_BURST
    else:
        classified = AcousticEventClass.GLASS_SHATTER if rise_ms <= glass_rise_ms_max else AcousticEventClass.SOUND_BURST

    if classified == AcousticEventClass.GLASS_SHATTER:
        confidence = min(0.95, 0.55 + energy / 40.0)
        escalate = 4.0
    elif classified == AcousticEventClass.SOUND_BURST:
        confidence = min(0.9, 0.45 + energy / 50.0)
        escalate = 2.0
    else:
        confidence = 0.2
        escalate = 1.0

    return DetectResult(True, classified, confidence, escalate)


# Owner-gated live hook names (document only — do not enable without confirmation):
#   gcloud services enable aiplatform.googleapis.com
#   gcloud ai models list
#   gcloud beta ai ... / gcloud alpha ai ...
# Deploy stub hook: Cloud Run / Cloud Functions pointing at this module's HTTP adapter (TODO).


if __name__ == "__main__":
    demo = detect({"energyDeltaDb": 14, "riseMs": 40, "eventClassHint": "glass_shatter"})
    print(demo.as_dict())
