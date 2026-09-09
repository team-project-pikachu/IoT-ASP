"""Nest sound burst → clamped reactive patch (#88 #96 #103 #45).

The closed loop this module completes
-------------------------------------
1. A Nest camera or doorbell publishes ``sdm.devices.events.CameraSound.Sound``
   (or ``DoorbellChime.Chime``) to the self-hosted Pub/Sub topic.
2. :mod:`.events` pulls and parses it; :mod:`.mapping` turns it into
   ``schemaVersion: 1`` telemetry carrying ``soundBurst: true`` — the field the
   fleet's existing burst path already understands.
3. :mod:`.detector` fuses that with the phone's own acoustic features and asks
   Gemini Enterprise for a ``glass_shatter | sound_burst | other`` label.
4. **This module** turns a confirmed burst into a clamped patch.
5. ``tools.write_patch`` validates and writes ``meta/patches/<deviceId>.json``.
6. The PWA polls that object every 2–5 s and **hot-applies** it in-session — no
   reload, no redeploy (``docs/api-contract.md``, "Hot-apply vs HTML deploy").

So the observable end-to-end latency from a Nest sound event to a louder alarm is
one Pub/Sub delivery plus at most one patch poll.

Why a separate module rather than more branches in ``sudden_freq``
------------------------------------------------------------------
``sudden_freq.author_sudden_freq_patch`` already handles ``soundBurst`` and owns the
vib→algo weighting, band gating and priors. This module does **not** duplicate any of
that — it delegates to it and then layers the *alarm escalation* the Nest witness
justifies (``alarmState`` / ``volBlast``), which the sudden-frequency path has no
reason to set. One authoring implementation, one clamp path.

Safety
------
* **Hold / Manual wins, checked twice.** This module refuses before authoring, and
  ``tools.write_patch`` refuses again at the write. A negative control covers both.
* **Clamps are never bypassed.** Every patch returned here has been through
  ``clamps.validate_patch``; an escalation that would exceed a clamp is refused, not
  silently rewritten.
* **Two witnesses to shout.** ``volBlast`` (jump toward max gain) requires a
  corroborated classification — a Nest acoustic event *and* a phone-side onset. A
  single uncorroborated witness escalates ``alarmState`` but does not blast, because a
  false positive drives a physical alarm louder in a residential setting.
* **Night is courtesy, not battery.** The America/New_York 22:00–07:00 window is a
  documented courtesy schedule (C5: the fleet is continuous 120 V AC, so nothing here
  is a duty-cycle saving). It is surfaced as ``nightNY`` on the patch rationale for the
  phone's existing night curve to apply; this module does not silently cap the alarm.

stdlib only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..clamps import SCHEMA_VERSION, validate_patch
from ..sudden_freq import author_sudden_freq_patch
from . import constants
from .detector import (
    AcousticEvidence,
    BurstClassification,
    GeminiEnterpriseDetector,
    escalation_hint,
    offline_classify,
)

#: Shriek dwell (ms) requested on a confirmed burst. Inside the documented 20–120 clamp.
BURST_SHRIEK_MS: float = 110.0


def evidence_from_telemetry(tel: dict[str, Any]) -> AcousticEvidence:
    """Build detector evidence from one ingested telemetry heartbeat.

    Reads only fields already documented in ``docs/api-contract.md`` plus the additive
    ``nest*`` keys from :mod:`.mapping`. Never reads a preview URL or a raw device id.
    """
    return AcousticEvidence(
        nest_event=tel.get("nestEvent"),
        nest_device_type=tel.get("nestDeviceType"),
        nest_device_ref=tel.get("nestDeviceRef"),
        mic_diff_db=_num(tel.get("micDiff") if tel.get("micDiff") is not None else tel.get("micNet")),
        mic_energy_db=_num(tel.get("micEnergy")),
        band_energy_lf_db=_num(tel.get("bandEnergyLf") if tel.get("bandEnergyLf") is not None else tel.get("lfEnergy")),
        band_energy_us_db=_num(tel.get("bandEnergyUs") if tel.get("bandEnergyUs") is not None else tel.get("usEnergy")),
        band_burst=tel.get("bandBurst"),
        sound_burst=bool(tel.get("soundBurst")),
        extreme_active=bool(tel.get("extremeActive")),
        abs_a=_num(tel.get("absA") if tel.get("absA") is not None else tel.get("a")),
        vib_class=tel.get("vibClass"),
        lag_s=_num(tel.get("nestLagS")),
        night_ny=bool(tel.get("nightNY")),
    )


def _num(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def classify(tel: dict[str, Any], *, detector: GeminiEnterpriseDetector | None = None) -> BurstClassification:
    """Classify one heartbeat. Uses Gemini Enterprise when configured, else offline."""
    evidence = evidence_from_telemetry(tel)
    if detector is None:
        return offline_classify(evidence)
    return detector.classify(evidence)


def author_nest_burst_patch(
    tel: dict[str, Any],
    *,
    detector: GeminiEnterpriseDetector | None = None,
    classification: BurstClassification | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    """Author a clamped reactive patch for a Nest-witnessed acoustic burst.

    Returns ``(ok, message, patch)`` — the same shape as
    ``sudden_freq.author_sudden_freq_patch``, so callers and tests treat the two
    authors interchangeably.

    Refuses (``ok=False``) when Hold/Manual is set, when the classification does not
    warrant escalation, or when the escalated values fail ``clamps.validate_patch``.
    """
    if tel.get("holdManual"):
        return False, "holdManual — refuse patch", {}

    cls = classification or classify(tel, detector=detector)
    hint = escalation_hint(cls, hold_manual=bool(tel.get("holdManual")))
    if not hint:
        return False, f"no escalation for label={cls.label} confidence={cls.confidence:.2f}", {}

    # Delegate the acoustic decision (algo weighting, band gating, priors) to the one
    # authoring implementation, having marked the burst so it takes the burst branch.
    seed = dict(tel)
    seed["soundBurst"] = True
    seed.setdefault("event", "soundBurst")
    seed.setdefault("vibClass", "acoustic")
    ok, msg, patch = author_sudden_freq_patch(seed)
    if not ok:
        return False, f"base author refused: {msg}", patch

    # Layer the alarm escalation the Nest witness justifies. Additive on schemaVersion 1.
    patch["alarmState"] = hint["alarmState"]
    patch["volBlast"] = bool(hint.get("volBlast"))
    patch["trigger"] = hint.get("trigger", "nest_sound_burst")
    patch["nestBurstClass"] = cls.label
    patch["nestBurstConfidence"] = round(float(cls.confidence), 3)
    patch["nestBurstSource"] = cls.source
    patch["nestBurstCorroborated"] = bool(cls.corroborated)
    patch["schemaVersion"] = SCHEMA_VERSION

    if patch["volBlast"]:
        # Blast only on two corroborating witnesses at sufficient confidence; the clamp
        # still bounds this at 100 UI percent.
        patch["vol"] = 100.0
        patch["shriekMs"] = BURST_SHRIEK_MS

    patch["rationale"] = (
        f"{patch.get('rationale', '')} | nest {cls.label} "
        f"({cls.confidence:.2f}, {cls.source}"
        f"{', corroborated' if cls.corroborated else ', single witness'}): {cls.rationale}"
    ).strip(" |")[:900]
    patch["authoredAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Re-validate AFTER escalation. An escalation that breaks a clamp is refused here
    # rather than being silently rewritten (CLAUDE.md invariant 5).
    ok, msg, clamped = validate_patch(patch)
    if not ok:
        return False, f"escalated patch failed clamps: {msg}", clamped
    return True, f"nest {cls.label} → {hint['alarmState']}", clamped


def react(
    tel: dict[str, Any],
    *,
    node_id: str | None = None,
    detector: GeminiEnterpriseDetector | None = None,
    writer: Any = None,
) -> dict[str, Any]:
    """End-to-end: telemetry → classify → author → write. Never raises into a loop.

    ``writer`` defaults to ``tools.write_patch`` (lazy import — ``tools`` pulls numpy via
    ``vib_anomaly``, and this module must stay importable without it). ``write_patch``
    re-checks Hold/Manual and the clamps, so this is defence in depth, not the only gate.
    """
    node = str(node_id or tel.get("deviceId") or tel.get("nodeId") or "node1")
    cls = classify(tel, detector=detector)
    ok, msg, patch = author_nest_burst_patch(tel, classification=cls)
    out: dict[str, Any] = {
        "ok": ok,
        "nodeId": node,
        "label": cls.label,
        "confidence": cls.confidence,
        "source": cls.source,
        "corroborated": cls.corroborated,
        "message": msg,
        "acousticEvents": sorted(constants.ACOUSTIC_EVENTS),
    }
    if not ok:
        out["written"] = False
        return out

    if writer is None:
        try:
            from ..tools import write_patch as writer  # type: ignore[assignment]
        except Exception as exc:  # noqa: BLE001 - author result is still useful
            out["written"] = False
            out["writeError"] = f"{type(exc).__name__}: {exc}"
            out["patch"] = patch
            return out

    import json as _json

    result = writer(node, _json.dumps(patch))
    out["written"] = bool(result.get("ok"))
    out["writeResult"] = {k: result.get(k) for k in ("ok", "uri", "error", "message")}
    out["patch"] = result.get("patch", patch)
    return out
