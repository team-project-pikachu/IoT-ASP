"""Gemini Enterprise acoustic-burst detector for Nest events (#87 #96 #103).

What this classifies, and what it honestly cannot
-------------------------------------------------
The SDM API does **not** hand a caller an audio file. Three separate facts, each from a
fetched page:

* ``sdm.devices.events.CameraSound.Sound`` carries only ``eventSessionId`` and
  ``eventId`` — a *detection signal*, no payload.
  Source: https://developers.google.com/nest/device-access/traits/device/camera-sound
* ``CameraClipPreview`` yields "a 10 frame video file in mp4 format" via ``previewUrl``.
  Source: https://developers.google.com/nest/device-access/traits/device/camera-clip-preview
* Audio exists **only on the live stream**: ``CameraLiveStream`` advertises
  ``"audioCodecs": ["OPUS"]`` over ``["RTSP", "WEB_RTC"]``, and "Only the Opus codec is
  supported for audio".
  Source: https://developers.google.com/nest/device-access/traits/device/camera-live-stream

So "process the audio data with Gemini Enterprise" resolves into two tiers, and this
module ships tier 1:

**Tier 1 — evidence bundle (implemented).** The fleet already computes real acoustic
features on the phones: ``micEnergy``, ``outLevel``, ``micDiff`` (``micEnergy − 0.85 ·
outLevel``), ``bandEnergyLf`` / ``bandEnergyUs``, ``bandBurst``, ``soundBurst``,
``extremeActive`` (``docs/api-contract.md``). A Nest ``Sound`` event is a second,
independent witness to the same physical instant. This module fuses them into an
:class:`AcousticEvidence` bundle and asks the Gemini Enterprise engine to classify the
burst. No media stack, no raw audio, nothing that cannot run on Cloud Run.

**Tier 2 — raw Opus (parked, seam only).** Pulling live-stream Opus and handing bytes to
a multimodal model needs a WebRTC/RTSP media client (aiortc/ffmpeg), which breaks the
repo's stdlib-first dependency policy and cannot run inside the ADK dry-run. The seam is
:func:`classify` accepting an optional ``audio_ref`` the caller resolves; today every
caller passes ``None``. Tracked in ``docs/specs/85-nest-google-home-integration.md``.

Engine
------
Gemini Enterprise engine ``iot-asp-autoroute`` on ``bear-iot-asp-rec``
(``docs/gemini-enterprise.md``). The serving-config resource name format
``projects/{project}/locations/{location}/collections/{collection}/engines/{engine}/servingConfigs/{sc}``
is per the Discovery Engine reference (Context7 library
``/websites/cloud_google_java_reference_google-cloud-discoveryengine``).

Safety posture
--------------
* The detector is **advisory**. It returns a classification; it never writes a patch and
  never touches ``meta/patches/``. Escalation hints go through
  :func:`escalation_hint`, and the caller must still pass them to
  ``tools.write_patch``, which enforces clamps and refuses under ``holdManual``.
* The prompt carries **features and an event class only** — never audio bytes, preview
  URLs, still-image URLs, transcripts, raw SDM device ids, structure ids or account
  identifiers. :func:`_prompt_payload` is the single place that builds it, and
  ``tests/test_nest_detector.py`` asserts sentinels never escape.
* Every network path degrades to :func:`offline_classify`, a deterministic heuristic, so
  CI, the dry-run and a credential-less laptop always produce an answer.

stdlib only; ``google.auth`` is imported lazily and only when a live call is attempted.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Final

from . import constants

DISCOVERY_ENGINE_BASE: Final[str] = "https://discoveryengine.googleapis.com/v1"
DEFAULT_LOCATION: Final[str] = "global"
DEFAULT_COLLECTION: Final[str] = "default_collection"
DEFAULT_SERVING_CONFIG: Final[str] = "default_search"

ENV_ENGINE_ID: Final[str] = "IOT_ASP_GEMINI_ENGINE_ID"
ENV_LOCATION: Final[str] = "GOOGLE_CLOUD_LOCATION"
DEFAULT_ENGINE_ID: Final[str] = "iot-asp-autoroute"

#: Classification labels. `glass_shatter` is the #95/#96 event class; `sound_burst` is
#: the generic acoustic onset already on the wire; `other` means do not escalate.
#: HomeNest twin wire keys (`eventClass` camelCase) live in services/gemini-burst-detect
#: and native/IoTASPHome AcousticDetectResult (#96); `other` maps to stub `unknown`.
LABEL_GLASS_SHATTER: Final[str] = "glass_shatter"
LABEL_SOUND_BURST: Final[str] = "sound_burst"
LABEL_OTHER: Final[str] = "other"
LABELS: Final[frozenset[str]] = frozenset({LABEL_GLASS_SHATTER, LABEL_SOUND_BURST, LABEL_OTHER})

SOURCE_GEMINI: Final[str] = "gemini_enterprise"
SOURCE_OFFLINE: Final[str] = "offline_heuristic"

#: micDiff (dB) above which the phone's own mic corroborates an environmental onset.
#: 6.0 dB is the threshold already used by `mic_diff.burst_decision` — reused, not
#: re-invented, so the two paths cannot drift.
MIC_DIFF_CORROBORATION_DB: Final[float] = 6.0
#: Seconds between the Nest event and the phone observation for them to count as one
#: physical instant. Nest event delivery is not instantaneous, so this is generous.
CORROBORATION_WINDOW_S: Final[float] = 12.0


class DetectorError(RuntimeError):
    """Raised only by :meth:`GeminiEnterpriseDetector.classify_strict`."""


@dataclass(frozen=True)
class AcousticEvidence:
    """What is known about one candidate acoustic burst. No PII, no media."""

    nest_event: str | None = None
    """`sound` | `chime` | `motion` | `person` | `clip_preview` | None."""
    nest_device_type: str | None = None
    nest_device_ref: str | None = None
    """Truncated hash from `mapping.device_ref` — never a raw SDM device id."""
    mic_diff_db: float | None = None
    mic_energy_db: float | None = None
    band_energy_lf_db: float | None = None
    band_energy_us_db: float | None = None
    band_burst: str | None = None
    sound_burst: bool = False
    extreme_active: bool = False
    abs_a: float | None = None
    vib_class: str | None = None
    lag_s: float | None = None
    """Seconds between the Nest event and the phone observation."""
    night_ny: bool = False
    audio_ref: str | None = None
    """Tier-2 seam. Always None today; see the module docstring."""

    @property
    def nest_is_acoustic(self) -> bool:
        return self.nest_event in constants.ACOUSTIC_EVENTS

    @property
    def phone_corroborates(self) -> bool:
        """True when the phone's own mic saw an onset near the same instant."""
        if self.lag_s is not None and abs(self.lag_s) > CORROBORATION_WINDOW_S:
            return False
        if self.sound_burst or self.extreme_active:
            return True
        return self.mic_diff_db is not None and self.mic_diff_db >= MIC_DIFF_CORROBORATION_DB


@dataclass(frozen=True)
class BurstClassification:
    """Advisory result. Never a patch."""

    label: str
    confidence: float
    rationale: str
    source: str
    corroborated: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    def as_wire(self) -> dict[str, Any]:
        """Additive schemaVersion-1 telemetry fields (`docs/api-contract.md`)."""
        out: dict[str, Any] = {
            "nestBurstClass": self.label,
            "nestBurstConfidence": round(float(self.confidence), 3),
            "nestBurstSource": self.source,
            "nestBurstCorroborated": bool(self.corroborated),
        }
        if self.label in (LABEL_GLASS_SHATTER, LABEL_SOUND_BURST):
            out["soundBurst"] = True
            out["vibClass"] = "acoustic"
        return out


def offline_classify(ev: AcousticEvidence) -> BurstClassification:
    """Deterministic fallback — no model, no network, always available.

    Conservative by construction: it escalates to ``glass_shatter`` only when two
    independent witnesses agree (a Nest acoustic event AND a phone-side onset), because
    a false escalation drives the alarm louder.
    """
    corroborated = ev.nest_is_acoustic and ev.phone_corroborates
    if corroborated:
        strong = (ev.mic_diff_db is not None and ev.mic_diff_db >= 2 * MIC_DIFF_CORROBORATION_DB) or ev.extreme_active
        if strong and ev.band_burst in ("us", "both"):
            return BurstClassification(
                LABEL_GLASS_SHATTER,
                0.72,
                "Nest acoustic event corroborated by a strong phone-side onset with "
                "high-band energy — consistent with a sharp fracture transient.",
                SOURCE_OFFLINE,
                corroborated=True,
            )
        return BurstClassification(
            LABEL_SOUND_BURST,
            0.60,
            "Nest acoustic event corroborated by a phone-side onset.",
            SOURCE_OFFLINE,
            corroborated=True,
        )
    if ev.nest_is_acoustic:
        return BurstClassification(
            LABEL_SOUND_BURST,
            0.40,
            "Nest reported sound with no phone-side corroboration in the window.",
            SOURCE_OFFLINE,
        )
    if ev.phone_corroborates:
        return BurstClassification(
            LABEL_SOUND_BURST,
            0.35,
            "Phone-side onset with no corroborating Nest acoustic event.",
            SOURCE_OFFLINE,
        )
    return BurstClassification(
        LABEL_OTHER, 0.05, "No acoustic witness on either path.", SOURCE_OFFLINE
    )


def escalation_hint(cls: BurstClassification, *, hold_manual: bool = False) -> dict[str, Any]:
    """Alarm-escalation *hints* for the patch author (#88). Never a patch.

    Returns ``{}`` under ``holdManual`` — Hold/Manual wins, and the refusal is made here
    as well as in ``tools.write_patch`` so a caller that forgets still cannot escalate.
    Fields are the ones already documented on the wire: ``alarmState`` and ``volBlast``.
    """
    if hold_manual:
        return {}
    if cls.label == LABEL_GLASS_SHATTER and cls.confidence >= 0.6:
        return {"alarmState": "triggered", "volBlast": True, "trigger": "nest_glass_shatter"}
    if cls.label == LABEL_SOUND_BURST and cls.corroborated:
        return {"alarmState": "triggered", "volBlast": False, "trigger": "nest_sound_burst"}
    return {}


def _prompt_payload(ev: AcousticEvidence) -> dict[str, Any]:
    """The ONLY place the model-bound payload is built.

    Everything here is a scalar feature or an event class. No audio, no URLs, no raw
    device or structure ids, no account identifiers, no transcripts.
    """
    return {
        "nestEvent": ev.nest_event,
        "nestDeviceType": ev.nest_device_type,
        "nestDeviceRef": ev.nest_device_ref,
        "micDiffDb": ev.mic_diff_db,
        "micEnergyDb": ev.mic_energy_db,
        "bandEnergyLfDb": ev.band_energy_lf_db,
        "bandEnergyUsDb": ev.band_energy_us_db,
        "bandBurst": ev.band_burst,
        "soundBurst": ev.sound_burst,
        "extremeActive": ev.extreme_active,
        "absA": ev.abs_a,
        "vibClass": ev.vib_class,
        "lagS": ev.lag_s,
        "nightNY": ev.night_ny,
    }


PROMPT_INSTRUCTION: Final[str] = (
    "You classify one candidate acoustic burst observed by a near-ultrasonic research "
    "fleet. Two independent witnesses may be present: a Google Nest camera acoustic "
    "event, and phone-side microphone features (micDiff is micEnergy minus 0.85x "
    "outLevel, a best-effort echo compensation, in dB). Reply with STRICT JSON only, no "
    "prose: {\"label\": one of \"glass_shatter\"|\"sound_burst\"|\"other\", "
    "\"confidence\": 0.0-1.0, \"rationale\": short string}. Escalate to glass_shatter "
    "only when both witnesses agree and the transient is sharp and high-band; a false "
    "escalation drives a physical alarm louder. Evidence follows as JSON."
)


class GeminiEnterpriseDetector:
    """Classify a burst with the Gemini Enterprise engine, degrading gracefully.

    ``transport(method, url, headers, body) -> (status, headers, body_bytes)`` is
    injectable so tests never reach the network. ``token_provider()`` returns an access
    token; the default lazily uses Application Default Credentials and returns ``None``
    when unavailable, which routes every call to :func:`offline_classify`.
    """

    def __init__(
        self,
        *,
        project: str | None = None,
        engine_id: str | None = None,
        location: str | None = None,
        serving_config: str = DEFAULT_SERVING_CONFIG,
        transport: Callable[..., tuple[int, dict[str, str], bytes]] | None = None,
        token_provider: Callable[[], str | None] | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        self.project = project or os.environ.get(constants.ENV_GCP_PROJECT, "bear-iot-asp-rec")
        self.engine_id = engine_id or os.environ.get(ENV_ENGINE_ID, DEFAULT_ENGINE_ID)
        self.location = location or os.environ.get(ENV_LOCATION, DEFAULT_LOCATION)
        self.serving_config = serving_config
        self._transport = transport or _urllib_transport
        self._token_provider = token_provider or _adc_token
        self.timeout_s = float(timeout_s)

    @property
    def serving_config_name(self) -> str:
        """`projects/{p}/locations/{l}/collections/{c}/engines/{e}/servingConfigs/{sc}`."""
        return (
            f"projects/{self.project}/locations/{self.location}"
            f"/collections/{DEFAULT_COLLECTION}/engines/{self.engine_id}"
            f"/servingConfigs/{self.serving_config}"
        )

    @property
    def answer_url(self) -> str:
        return f"{DISCOVERY_ENGINE_BASE}/{self.serving_config_name}:answer"

    def classify(self, ev: AcousticEvidence) -> BurstClassification:
        """Best-effort classification. Never raises; falls back offline."""
        try:
            return self.classify_strict(ev)
        except Exception:  # noqa: BLE001 — advisory path must never break the loop
            return offline_classify(ev)

    def classify_strict(self, ev: AcousticEvidence) -> BurstClassification:
        """Live call; raises :class:`DetectorError` instead of falling back."""
        token = self._token_provider()
        if not token:
            raise DetectorError("no Gemini Enterprise credential available")
        body = json.dumps(
            {
                "query": {"text": PROMPT_INSTRUCTION + "\n" + json.dumps(_prompt_payload(ev), sort_keys=True)},
                "answerGenerationSpec": {"includeCitations": False, "ignoreLowRelevantContent": False},
            }
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-goog-user-project": self.project,
        }
        status, _hdrs, payload = self._transport("POST", self.answer_url, headers, body)
        if status != 200:
            raise DetectorError(f"discoveryengine :answer returned HTTP {status}")
        return _parse_answer(payload, ev)


def _parse_answer(payload: bytes, ev: AcousticEvidence) -> BurstClassification:
    """Parse a Discovery Engine :answer body into a classification.

    Tolerant: the engine may wrap the JSON in prose or fences. An unusable body raises,
    so :meth:`classify` falls back rather than inventing a label.
    """
    try:
        obj = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DetectorError(f"unparseable answer body: {type(exc).__name__}") from None
    text = ""
    answer = obj.get("answer")
    if isinstance(answer, dict):
        text = str(answer.get("answerText") or "")
    if not text:
        text = str(obj.get("answerText") or "")
    inner = _extract_json_object(text)
    if inner is None:
        raise DetectorError("answer contained no JSON object")
    label = str(inner.get("label") or "").strip().lower()
    if label not in LABELS:
        raise DetectorError(f"answer label not in whitelist: {label!r}")
    try:
        confidence = float(inner.get("confidence", 0.0))
    except (TypeError, ValueError):
        raise DetectorError("answer confidence not numeric") from None
    confidence = max(0.0, min(1.0, confidence))
    return BurstClassification(
        label,
        confidence,
        str(inner.get("rationale") or "")[:400],
        SOURCE_GEMINI,
        corroborated=ev.nest_is_acoustic and ev.phone_corroborates,
        raw={"servingConfigAnswer": True},
    )


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """First balanced ``{...}`` in ``text`` that parses as a JSON object."""
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj = json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = -1
                    continue
                if isinstance(obj, dict):
                    return obj
                start = -1
    return None


def _urllib_transport(
    method: str, url: str, headers: dict[str, str], body: bytes | None
) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20.0) as resp:  # noqa: S310 - https only
            return int(resp.status), dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), dict(exc.headers or {}), exc.read()


def _adc_token() -> str | None:
    """Application Default Credentials token, or None when unavailable.

    Lazy import: ``google-auth`` is optional, and this module must import without it.
    """
    try:
        import google.auth  # type: ignore
        import google.auth.transport.requests  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    try:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(google.auth.transport.requests.Request())
        return str(creds.token) if creds.token else None
    except Exception:  # noqa: BLE001
        return None
