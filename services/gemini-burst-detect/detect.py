"""Gemini Enterprise / Vertex acoustic event detector stub (M8).

Does NOT call paid APIs. Wire live `gcloud ai` / Vertex only after owner auth
(bettyctai@gmail.com) + 1Password `dev` keys.

Event classes: sound_burst | glass_shatter | unknown
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
            "escalate_db": self.escalate_db,
        }


def detect(features: Mapping[str, Any], *, onset_db: float = 9.0, glass_rise_ms_max: float = 80.0) -> DetectResult:
    """Heuristic stub mirroring native StubBurstDetectClient."""
    energy = float(features.get("energyDeltaDb") or features.get("energy_delta_db") or 0.0)
    rise_ms = float(features.get("riseMs") or features.get("rise_ms") or 999.0)
    hint_raw = str(features.get("eventClassHint") or features.get("event_class_hint") or "unknown")
    try:
        hint = AcousticEventClass(hint_raw)
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
