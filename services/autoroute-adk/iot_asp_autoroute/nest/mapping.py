"""Nest observations → additive ``schemaVersion: 1`` ASP telemetry.

Issue #85 / #86 / #103, spec ``docs/specs/85-nest-google-home-integration.md``.
Wire authority is ``docs/api-contract.md``; nothing here forks that table.

Design rule: **reuse the wire, do not extend the semantics.** A Nest
``CameraSound.Sound`` or ``DoorbellChime.Chime`` is an environmental acoustic
onset observed by a second, independent witness — exactly what the existing
``soundBurst`` / ``event: "soundBurst"`` / ``vibClass: "acoustic"`` fields
already mean. So an acoustic Nest event lands on those three existing keys and
the repo's burst path reacts with no new semantics at all. Everything that is
genuinely new about Nest is namespaced ``nest*`` and is **optional**:
``schemaVersion`` stays ``1`` (NEST_DESIGN.md #1).

What this module must never do
------------------------------
* It never sets ``holdManual``, ``suddenFreq``, ``vol``, or any patch field
  (``algo``, ``fMin``, ``fMax``, ``pulseMs``, ``shriekMs``, ``vibThreshold``,
  ``seedAction``, …). It produces an *observation*; patch authorship stays with
  ``sudden_freq`` / ``tools.write_patch``, which enforce clamps and refuse
  under Hold / Manual.
* It never puts a ``previewUrl``, a raw SDM device id, a device resource name
  or a structure id on the wire. Those are recording URIs and site identifiers
  (CLAUDE.md #7). The wire carries :func:`device_ref` — ``sha256(device_id)``
  truncated to 12 hex characters — which is stable, joinable across records,
  and not reversible to a device id by a reader of the public artifact.
  ``nestClipAvailable`` reports that a clip *exists* without naming it.

Honesty note: SDM never hands a caller audio. ``CameraSound.Sound`` is a
detection signal carrying only ``eventSessionId`` / ``eventId``
(https://developers.google.com/nest/device-access/traits/device/camera-sound),
so ``soundBurst`` here means "Nest reported a sound event", not "this backend
measured acoustic energy". The measured quantities on the wire
(``micEnergy``, ``micDiff``, ``bandEnergy*``) still come only from the phones.

stdlib only, no clock of its own (``now`` is injected), no I/O.
"""

from __future__ import annotations

import hashlib
import math
import time
from datetime import datetime, timezone
from typing import Any, Final, Mapping

from . import constants
from ..clamps import SCHEMA_VERSION

__all__ = [
    "SOURCE_EVENT",
    "SOURCE_POLL",
    "TS_FMT",
    "device_ref",
    "device_to_state",
    "event_to_telemetry",
    "normalize_ts",
]

#: UTC ISO-8601 exactly as the rest of the backend stamps it
#: (``.claude/rules/autoroute-backend.md``).
TS_FMT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"

#: ``nestSource`` values.
SOURCE_EVENT: Final[str] = "event"
SOURCE_POLL: Final[str] = "poll"
SOURCES: Final[frozenset[str]] = frozenset({SOURCE_EVENT, SOURCE_POLL})

#: Length of the truncated ``sha256`` device reference. 12 hex characters is
#: 48 bits — collision-free for a household fleet, and short enough to read in
#: a log line.
DEVICE_REF_LEN: Final[int] = 12

#: Keys this module is forbidden to emit, asserted by ``tests/test_nest_events.py``.
#: Patch fields plus the three control keys a Nest observation must never touch.
FORBIDDEN_KEYS: Final[frozenset[str]] = frozenset(
    {
        "holdManual",
        "suddenFreq",
        "vol",
        "algo",
        "fMin",
        "fMax",
        "pulseMs",
        "shriekMs",
        "vibThreshold",
        "seedAction",
        "rationale",
        "engineId",
        "priors",
        "trigger",
        "nodeId",
    }
)

#: Existing wire vocabulary reused for an acoustic Nest event (docs/api-contract.md).
EVENT_SOUND_BURST: Final[str] = "soundBurst"
VIB_CLASS_ACOUSTIC: Final[str] = "acoustic"


# ── helpers ──────────────────────────────────────────────────────────────────


def _last_segment(value: str) -> str:
    """Last path segment, so a resource name and a bare id hash identically."""
    return value.rstrip("/").rsplit("/", 1)[-1]


def device_ref(device_id: str) -> str:
    """Stable, non-reversible wire reference for an SDM device.

    ``sha256(<last path segment of device_id>)`` truncated to
    :data:`DEVICE_REF_LEN` hex characters. Accepts either a bare device id or a
    full ``enterprises/{project}/devices/{device-id}`` resource name and yields
    the same reference for both. Returns ``""`` for an empty or non-string
    input, so a malformed event produces a missing field rather than the hash
    of the empty string masquerading as a real device.
    """
    if not isinstance(device_id, str) or not device_id.strip():
        return ""
    segment = _last_segment(device_id.strip())
    if not segment:
        return ""
    return hashlib.sha256(segment.encode("utf-8")).hexdigest()[:DEVICE_REF_LEN]


def normalize_ts(value: Any = None, *, now: float | None = None) -> str:
    """Return UTC ``%Y-%m-%dT%H:%M:%SZ``.

    ``value`` is the SDM envelope ``timestamp`` (RFC-3339, e.g.
    ``"2019-01-01T00:00:01Z"``, sometimes with fractional seconds). When it is
    absent or unparseable, ``now`` — injected epoch seconds, never an internal
    clock unless the caller omits it — is used instead.
    """
    if isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).strftime(TS_FMT)
    epoch = float(now) if isinstance(now, (int, float)) and not isinstance(now, bool) else None
    if epoch is None or not math.isfinite(epoch):
        epoch = time.time()
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(TS_FMT)


def _clean_node_id(node_id: Any) -> str:
    if not isinstance(node_id, str) or not node_id.strip():
        raise ValueError("node_id is required (the ASP node the Nest device is bound to)")
    return node_id.strip()


# ── event → telemetry ────────────────────────────────────────────────────────


def event_to_telemetry(
    ev: Any,
    *,
    node_id: str,
    now: float | None = None,
    source: str = SOURCE_EVENT,
    device_type: str | None = None,
    connectivity: str | None = None,
) -> dict[str, Any]:
    """One :class:`~iot_asp_autoroute.nest.events.NestEvent` → a heartbeat dict.

    ``ev`` is duck-typed (``wire_name``, ``timestamp``, ``device_id``,
    ``event_session_id``, ``thread_id``, ``thread_state``, ``preview_url``), so
    this module does not import :mod:`~iot_asp_autoroute.nest.events` and stays
    testable with a stub. ``device_type`` and ``connectivity`` are supplied by
    the caller because an SDM **event** envelope carries neither — only the
    device object from ``devices.list`` / ``devices.get`` does
    (https://developers.google.com/nest/device-access/api/events). Omitting
    them omits the corresponding wire fields rather than guessing a type from
    the event class.

    Emitted keys, all optional except ``schemaVersion`` / ``deviceId`` / ``ts``:

    ``event`` / ``soundBurst`` / ``vibClass`` are the **existing** fields from
    ``docs/api-contract.md`` and appear only for an acoustic event
    (:data:`constants.ACOUSTIC_EVENTS`). Everything else is ``nest*``.
    """
    node = _clean_node_id(node_id)
    src = source if source in SOURCES else SOURCE_EVENT

    wire_name = getattr(ev, "wire_name", None)
    wire_name = wire_name if isinstance(wire_name, str) and wire_name else None
    is_acoustic = wire_name in constants.ACOUSTIC_EVENTS

    out: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "deviceId": node,
        "ts": normalize_ts(getattr(ev, "timestamp", None), now=now),
        "nestSource": src,
    }

    # Existing wire vocabulary — this is how #86/#103 reaches the burst path.
    if is_acoustic:
        out["event"] = EVENT_SOUND_BURST
        out["soundBurst"] = True
        out["vibClass"] = VIB_CLASS_ACOUSTIC

    if wire_name is not None:
        out["nestEvent"] = wire_name

    ref = device_ref(getattr(ev, "device_id", "") or "")
    if ref:
        out["nestDeviceRef"] = ref

    if isinstance(device_type, str) and device_type.strip():
        out["nestDeviceType"] = device_type.strip()
    if isinstance(connectivity, str) and connectivity.strip():
        out["nestConnectivity"] = connectivity.strip()

    session_id = getattr(ev, "event_session_id", None)
    if isinstance(session_id, str) and session_id:
        out["nestEventSessionId"] = session_id
    thread_id = getattr(ev, "thread_id", None)
    if isinstance(thread_id, str) and thread_id:
        out["nestEventThreadId"] = thread_id
    thread_state = getattr(ev, "thread_state", None)
    if isinstance(thread_state, str) and thread_state:
        out["nestEventThreadState"] = thread_state

    preview_url = getattr(ev, "preview_url", None)
    if isinstance(preview_url, str) and preview_url:
        # The URL itself is a recording URI and stays off the wire; only its
        # existence is reported.
        out["nestClipAvailable"] = True

    return out


# ── device → private state record ────────────────────────────────────────────


def device_to_state(dev: Any) -> dict[str, Any]:
    """One device → the record written to ``meta/nest/state/<ref>.json``.

    That tree is private (:data:`constants.GCS_NEST_STATE_PREFIX`), but this
    record is deliberately safe even if it is copied somewhere public: it
    carries the truncated :func:`device_ref`, the device **type**, the
    connectivity status and the trait **names** — never the raw device id, the
    resource name, a structure id, or any trait *value*. Trait values include
    ``sdm.devices.traits.Info.customName``, a user-chosen label that can name a
    room or a person (https://developers.google.com/nest/device-access/traits),
    so no trait payload is copied here.

    ``dev`` is duck-typed against
    :class:`~iot_asp_autoroute.nest.sdm_client.NestDevice` (``device_id``,
    ``type``, ``traits``, ``connectivity``, ``is_camera_like``), so this module
    imports no sibling.
    """
    traits = getattr(dev, "traits", None)
    trait_names = sorted(k for k in traits if isinstance(k, str)) if isinstance(traits, Mapping) else []
    dev_type = getattr(dev, "type", None)
    dev_type = dev_type if isinstance(dev_type, str) and dev_type else None
    connectivity = getattr(dev, "connectivity", None)
    connectivity = connectivity if isinstance(connectivity, str) and connectivity else None
    camera_like = getattr(dev, "is_camera_like", None)

    state: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "nestDeviceRef": device_ref(getattr(dev, "device_id", "") or ""),
        "nestTraits": trait_names,
        "nestEventTraits": [t for t in trait_names if t in constants.CAMERA_TRAITS],
        "nestCameraLike": bool(camera_like)
        if isinstance(camera_like, bool)
        else dev_type in constants.CAMERA_LIKE_TYPES,
    }
    if dev_type is not None:
        state["nestDeviceType"] = dev_type
    if connectivity is not None:
        state["nestConnectivity"] = connectivity
    return state
