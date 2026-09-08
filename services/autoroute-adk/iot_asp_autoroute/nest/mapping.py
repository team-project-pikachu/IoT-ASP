"""Map Nest SDM observations onto schemaVersion-1 additive telemetry.

Issue #103 / #84 / #86, spec ``docs/specs/103-nest-sdm-continuous.md``.

This module is the *only* place a Nest event becomes a public wire payload.
:class:`iot_asp_autoroute.nest.events.NestEvent` may hold ``previewUrl``, a raw
SDM device resource name, and a device id in memory (the poller needs them to
call ``devices.get``). None of those leave here. The wire is an allowlist:
``nestEvent`` values come from :data:`constants.EVENT_WIRE_NAMES`, and the
device is identified by :func:`device_ref` (truncated SHA-256), never by the
resource name.

Unknown event types are ignored (``None``), not passed through under a made-up
name. Clip-preview URLs become the boolean ``nestHasClip``. Tokens never have a
field.

stdlib only. No network, no sleeps, no GCS writes — the poller owns I/O.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, Final

from ..clamps import SCHEMA_VERSION
from . import constants
from .events import NestEvent, REDACTED, parse_event

__all__ = [
    "DEVICE_REF_HEX_LEN",
    "WIRE_KEYS",
    "NestWire",
    "device_ref",
    "device_type_wire",
    "event_to_wire",
    "device_to_wire",
    "envelope_to_wire",
    "assert_wire_safe",
]

#: Hex length of ``nestDeviceRef``. Same recipe :func:`rate_limit.bucket_ref`
#: uses for per-device bucket keys, so a health snapshot and a telemetry row
#: can be joined without ever printing the SDM id.
DEVICE_REF_HEX_LEN: Final[int] = 12

#: Allowlisted schemaVersion-1 additive keys. Anything not in this tuple is
#: dropped by :meth:`NestWire.as_dict` and hidden by :meth:`NestWire.__repr__`.
WIRE_KEYS: Final[tuple[str, ...]] = (
    "schemaVersion",
    "nestEvent",
    "nestDeviceRef",
    "nestDeviceType",
    "nestTs",
    "nestThreadState",
    "nestAcoustic",
    "nestHasClip",
    "nestOnline",
    "nestRelationType",
    "nestSource",
)

#: Substrings that must never appear in a wire JSON blob. Documentation
#: placeholders (``device-id``, ``previewUrl``) are included so a regression
#: that copies the fixture through is caught in CI.
_FORBIDDEN_SUBSTRINGS: Final[tuple[str, ...]] = (
    "previewUrl",
    "preview_url",
    "enterprises/",
    "/devices/",
    "Bearer ",
    "Basic ",
    "ya29.",
    "access_token",
    "refresh_token",
)


def device_ref(device_id: str | None) -> str:
    """Truncated SHA-256 of an SDM device id — never the raw id.

    Empty / non-string input yields ``""`` so callers can omit the field.
    """
    if not isinstance(device_id, str) or not device_id:
        return ""
    return hashlib.sha256(device_id.encode("utf-8")).hexdigest()[:DEVICE_REF_HEX_LEN]


def device_type_wire(sdm_type: str | None) -> str | None:
    """Last path segment of an SDM type, when it is a documented type.

    ``sdm.devices.types.CAMERA`` → ``CAMERA``. Unknown / malformed types are
    ignored rather than passed through — a vendor-added type is a new event
    class, not something we invent a wire name for.
    """
    if not isinstance(sdm_type, str) or not sdm_type:
        return None
    known = set(constants.DEVICE_QUOTAS) | set(constants.CAMERA_LIKE_TYPES)
    if sdm_type not in known:
        return None
    label = sdm_type.rsplit(".", 1)[-1]
    return label or None


def _online_from_traits(traits: Mapping[str, Any] | None) -> bool | None:
    """``True``/``False`` from the Connectivity trait, else ``None``."""
    if not isinstance(traits, Mapping):
        return None
    trait = traits.get(constants.TRAIT_CONNECTIVITY)
    if not isinstance(trait, Mapping):
        return None
    status = trait.get("status")
    if status == "ONLINE":
        return True
    if status == "OFFLINE":
        return False
    return None


class NestWire(dict):
    """Allowlisted additive telemetry. ``__repr__`` never prints other keys.

    Subclassing ``dict`` keeps ``json.dumps`` working without a default=.
    Extra keys may be set in memory (a buggy caller) but they cannot reach
    :meth:`as_dict` or :meth:`__repr__`.
    """

    def as_dict(self) -> dict[str, Any]:
        """Stable-order allowlisted payload, omitting ``None`` / ``""``."""
        out: dict[str, Any] = {}
        for key in WIRE_KEYS:
            if key not in self:
                continue
            val = self[key]
            if val is None or val == "":
                continue
            out[key] = val
        return out

    def __repr__(self) -> str:  # noqa: D105 - redaction is the whole point
        parts = [f"{k}={self[k]!r}" for k in WIRE_KEYS if k in self]
        return "<NestWire " + " ".join(parts) + ">"

    __str__ = __repr__


def _build(
    *,
    nest_event: str | None = None,
    device_id: str | None = None,
    device_type: str | None = None,
    ts: str | None = None,
    thread_state: str | None = None,
    acoustic: bool | None = None,
    has_clip: bool | None = None,
    online: bool | None = None,
    relation_type: str | None = None,
    source: str,
) -> NestWire:
    wire = NestWire()
    wire["schemaVersion"] = SCHEMA_VERSION
    wire["nestSource"] = source
    if nest_event is not None:
        wire["nestEvent"] = nest_event
    ref = device_ref(device_id)
    if ref:
        wire["nestDeviceRef"] = ref
    dtype = device_type_wire(device_type)
    if dtype:
        wire["nestDeviceType"] = dtype
    if isinstance(ts, str) and ts:
        wire["nestTs"] = ts
    if thread_state in constants.EVENT_THREAD_STATES:
        wire["nestThreadState"] = thread_state
    if acoustic is not None:
        wire["nestAcoustic"] = bool(acoustic)
    if has_clip is not None:
        wire["nestHasClip"] = bool(has_clip)
    if online is not None:
        wire["nestOnline"] = bool(online)
    if relation_type in constants.RELATION_TYPES:
        wire["nestRelationType"] = relation_type
    return wire


def event_to_wire(
    ev: NestEvent | None,
    *,
    device_type: str | None = None,
) -> NestWire | None:
    """Allowlisted telemetry for one parsed event, or ``None`` to ignore it.

    Ignore rules (negative controls):

    * ``ev`` is not a :class:`NestEvent`
    * ``event_type`` is set but not in :data:`constants.EVENT_WIRE_NAMES`
      (unknown vendor class — do not invent a ``nestEvent``)
    * relation ``type`` is not in :data:`constants.RELATION_TYPES`
    * trait-only envelope with no Connectivity status (nothing to say)
    """
    if not isinstance(ev, NestEvent):
        return None

    if ev.event_type and ev.wire_name is None:
        return None

    if ev.is_relation:
        rel = ev.relation if isinstance(ev.relation, Mapping) else {}
        rtype = rel.get("type")
        if rtype not in constants.RELATION_TYPES:
            return None
        return _build(
            device_id=ev.device_id,
            device_type=device_type,
            ts=ev.timestamp,
            relation_type=str(rtype),
            source="relation",
        )

    if ev.event_type is None:
        online = _online_from_traits(ev.traits)
        if online is None:
            return None
        return _build(
            device_id=ev.device_id,
            device_type=device_type,
            ts=ev.timestamp,
            online=online,
            source="trait",
        )

    return _build(
        nest_event=ev.wire_name,
        device_id=ev.device_id,
        device_type=device_type,
        ts=ev.timestamp,
        thread_state=ev.thread_state,
        acoustic=ev.is_acoustic,
        has_clip=ev.has_clip,
        online=_online_from_traits(ev.traits),
        source="event",
    )


def device_to_wire(dev: Any) -> NestWire | None:
    """Liveness snapshot from a :class:`sdm_client.NestDevice`.

    ``dev`` is duck-typed so this module does not import the client (keeps
    mapping independently testable). Missing / empty devices are ignored.
    """
    if dev is None:
        return None
    device_id = getattr(dev, "device_id", None)
    if not isinstance(device_id, str) or not device_id:
        return None
    traits = getattr(dev, "traits", None)
    return _build(
        device_id=device_id,
        device_type=getattr(dev, "type", None),
        online=_online_from_traits(traits if isinstance(traits, Mapping) else None),
        source="poll",
    )


def envelope_to_wire(
    envelope: Any, *, device_type: str | None = None
) -> NestWire | None:
    """Parse-then-map. ``None`` for anything that is not a mappable SDM envelope."""
    return event_to_wire(parse_event(envelope), device_type=device_type)


def assert_wire_safe(obj: Any) -> dict[str, Any]:
    """Return the allowlisted dict, raising ``ValueError`` if PII leaked.

    Used by the poller before every write and by tests as a negative control.
    """
    if isinstance(obj, NestWire):
        payload = obj.as_dict()
    elif isinstance(obj, Mapping):
        payload = {k: obj[k] for k in WIRE_KEYS if k in obj and obj[k] not in (None, "")}
        payload.setdefault("schemaVersion", SCHEMA_VERSION)
    else:
        raise ValueError("refuse: wire payload is not a mapping")
    blob = json.dumps(payload, default=str)
    for needle in _FORBIDDEN_SUBSTRINGS:
        if needle in blob:
            raise ValueError("refuse: wire payload contained a forbidden substring")
    if REDACTED in blob:
        # redaction marker means we accidentally serialised a repr, not a field
        raise ValueError("refuse: wire payload contained a redaction marker")
    extra = sorted(set(payload) - set(WIRE_KEYS))
    if extra:
        raise ValueError(f"refuse: non-allowlisted wire keys {extra}")
    return payload


def main() -> int:
    """Offline demo: map every fixture, print allowlisted rows, refuse PII."""
    from pathlib import Path

    fixtures = (
        Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "nest"
    )
    names = (
        "camera_sound.json",
        "camera_motion.json",
        "camera_person.json",
        "doorbell_chime.json",
        "clip_preview.json",
        "trait_update.json",
        "relation_update.json",
    )
    for name in names:
        path = fixtures / name
        envelope = json.loads(path.read_text(encoding="utf-8"))
        wire = envelope_to_wire(envelope)
        if wire is None:
            print(f"{name}: ignored")
            continue
        safe = assert_wire_safe(wire)
        print(f"{name}: {safe}")
        print(f"  repr={wire!r}")
    unknown = {
        "eventId": "e",
        "timestamp": "2019-01-01T00:00:01Z",
        "resourceUpdate": {
            "name": "enterprises/project-id/devices/device-id",
            "events": {"sdm.devices.events.NotAReal.Event": {}},
        },
    }
    assert envelope_to_wire(unknown) is None, "unknown event types must be ignored"
    print("unknown event: ignored OK")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI demo
    raise SystemExit(main())
