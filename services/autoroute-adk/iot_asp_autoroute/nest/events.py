"""SDM event envelopes: tolerant parsing, thread de-duplication, Pub/Sub pull.

Issue #85 / #86 / #103, spec ``docs/specs/85-nest-google-home-integration.md``.

This module is the *ingress* half of the Nest integration. It turns whatever
Google hands us — a Pub/Sub ``ReceivedMessage``, a raw SDM envelope, a partial
or corrupt payload — into a :class:`NestEvent`, or into ``None``. It never
raises on malformed input: one bad message must never take down a poll cycle.

Verified API facts (each carries the page that states it)
---------------------------------------------------------

* A **resource-update** envelope has ``eventId``, ``timestamp``,
  ``resourceUpdate`` (with ``name`` and ``events`` and/or ``traits``),
  ``userId``, and optionally ``eventThreadId``, ``eventThreadState`` and
  ``resourceGroup``::

      {
        "eventId": "...",
        "timestamp": "2019-01-01T00:00:01Z",
        "resourceUpdate": {
          "name": "enterprises/project-id/devices/device-id",
          "events": {
            "sdm.devices.events.CameraMotion.Motion": {
              "eventSessionId": "...", "eventId": "..."
            }
          }
        },
        "userId": "...",
        "eventThreadId": "...",
        "eventThreadState": "STARTED",
        "resourceGroup": ["enterprises/project-id/devices/device-id"]
      }

  Source: https://developers.google.com/nest/device-access/api/events
* A **trait-update** envelope carries ``resourceUpdate.traits`` and **no**
  ``events`` key (the doc example is a ``ThermostatMode`` change) and has no
  ``eventThreadId`` / ``eventThreadState`` — same page.
* A **relation** envelope carries ``relationUpdate`` with ``type``
  (``CREATED`` / ``UPDATED`` / ``DELETED``), ``subject`` (a structure) and
  ``object`` (a device), and **no** ``resourceUpdate`` — same page.
* ``eventThreadState`` is ``STARTED`` (first), ``UPDATED`` (ongoing) or
  ``ENDED`` (final); ``resourceGroup`` lists "resources that might have similar
  updates to this event" — same page.
* Per-event payload keys, each from its own trait page:

  ============================================ ==========================================
  event                                        payload keys
  ============================================ ==========================================
  ``CameraMotion.Motion``                      ``eventSessionId``, ``eventId``
  ``CameraPerson.Person``                      ``eventSessionId``, ``eventId``
  ``CameraSound.Sound``                        ``eventSessionId``, ``eventId``
  ``DoorbellChime.Chime``                      ``eventSessionId``, ``eventId``
  ``CameraClipPreview.ClipPreview``            ``eventSessionId``, ``previewUrl``
  ============================================ ==========================================

  ``ClipPreview`` is the odd one out: it has **no** inner ``eventId`` and
  instead carries ``previewUrl``, "a 10 frame video file in mp4 format"
  fetched with ``Authorization: Bearer <access token>``.
  Sources: https://developers.google.com/nest/device-access/traits/device/camera-motion
  · .../camera-person · .../camera-sound · .../doorbell-chime
  · .../camera-clip-preview
* Pub/Sub pull is ``POST https://pubsub.googleapis.com/v1/{subscription}:pull``
  with body ``{"maxMessages": <int>}``; the response is
  ``{"receivedMessages": [{"ackId": str, "message": {"data": <base64>,
  "attributes": {...}, "messageId": str, "publishTime": str,
  "orderingKey": str}, "deliveryAttempt": int}]}``. Acknowledgement is
  ``POST .../{subscription}:acknowledge`` with ``{"ackIds": [...]}``, whose
  success body is an empty JSON object; ``ackIds`` "must not be empty".
  Sources: https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/pull
  · https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/acknowledge

House rules
-----------
stdlib only. ``google.auth`` is imported lazily inside
:func:`google_adc_token_provider`, so importing this module works with no
``google-*`` package installed. HTTP goes through an injectable transport, so
every test is offline. No sleeps, no retries, no internal clock: the caller
passes ``now``.

PII: ``previewUrl``, raw device ids and structure ids are recording URIs / site
identifiers (CLAUDE.md #7). They live on :class:`NestEvent` in memory because
the poller needs them, but :meth:`NestEvent.__repr__` redacts them and it is
:mod:`iot_asp_autoroute.nest.mapping` — never this module — that decides what
reaches the public wire.
"""

from __future__ import annotations

import base64
import binascii
import json
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Final, Mapping, Sequence

from . import constants
from .auth import Transport, urllib_transport

__all__ = [
    "NestEvent",
    "PubSubError",
    "PubSubPuller",
    "EventDeduper",
    "parse_event",
    "parse_pubsub_message",
    "google_adc_token_provider",
    "device_id_from_resource",
]

#: Redaction marker used wherever a site identifier would otherwise be printed.
REDACTED: Final[str] = "<redacted>"

#: Deterministic tie-break when one envelope carries several events at once (a
#: real camera commonly publishes ``Motion`` **and** ``ClipPreview`` in the same
#: message). The acoustic classes come first because they are the ones the ASP
#: burst path (#86 #103) reacts to; ``clip_preview`` is last because it is
#: media metadata about another event, not an observation of its own. Any event
#: id not listed here sorts after all of these, in the payload's own key order.
EVENT_PRIORITY: Final[tuple[str, ...]] = (
    constants.EVENT_CAMERA_SOUND,
    constants.EVENT_DOORBELL_CHIME,
    constants.EVENT_CAMERA_PERSON,
    constants.EVENT_CAMERA_MOTION,
    constants.EVENT_CLIP_PREVIEW,
)

_DEFAULT_MAX_MESSAGES: Final[int] = 10
_MAX_MESSAGES_CAP: Final[int] = 1000


# ── helpers ──────────────────────────────────────────────────────────────────


def _as_str(value: Any) -> str | None:
    """``value`` when it is a non-empty ``str``, else ``None``."""
    return value if isinstance(value, str) and value else None


def _as_mapping(value: Any) -> dict[str, Any]:
    """A shallow ``dict`` copy when ``value`` is a mapping, else ``{}``."""
    return dict(value) if isinstance(value, Mapping) else {}


def device_id_from_resource(name: str | None) -> str:
    """Last path segment of ``enterprises/{project}/devices/{device-id}``.

    Accepts a bare id too, so callers may pass either form. Returns ``""`` for
    anything that is not a usable string.
    """
    if not isinstance(name, str) or not name:
        return ""
    return name.rstrip("/").rsplit("/", 1)[-1]


# ── the parsed event ─────────────────────────────────────────────────────────


@dataclass(frozen=True, repr=False)
class NestEvent:
    """One parsed SDM envelope — a device event, a trait update, or a relation.

    ``traits`` is ``resourceUpdate.traits`` (empty for an event-only envelope);
    ``relation`` is ``relationUpdate`` (``None`` for a resource update); ``raw``
    is the whole envelope, kept for the private ``meta/nest/events`` tree and
    for audit. ``device_name``, ``device_id`` and ``preview_url`` are site
    identifiers and are redacted by :meth:`__repr__`.
    """

    event_id: str = ""
    timestamp: str = ""
    device_name: str = ""
    device_id: str = ""
    event_type: str | None = None
    wire_name: str | None = None
    event_session_id: str | None = None
    sdm_event_id: str | None = None
    preview_url: str | None = None
    thread_id: str | None = None
    thread_state: str | None = None
    traits: dict[str, Any] = field(default_factory=dict)
    relation: dict[str, Any] | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_acoustic(self) -> bool:
        """True for ``sound`` / ``chime`` — the classes the burst path uses."""
        return self.wire_name in constants.ACOUSTIC_EVENTS

    @property
    def is_relation(self) -> bool:
        """True when this envelope was a ``relationUpdate``."""
        return self.relation is not None

    @property
    def has_clip(self) -> bool:
        """True when a ``previewUrl`` was present (the URL itself stays off-wire)."""
        return bool(self.preview_url)

    def __repr__(self) -> str:  # pragma: no cover - exercised by the PII test
        """Never prints a device id, a device resource name or a preview URL."""
        return (
            "<NestEvent eventId={eid!r} ts={ts!r} type={etype!r} wire={wire!r} "
            "thread={thread!r}/{state!r} device={dev} clip={clip}>".format(
                eid=self.event_id,
                ts=self.timestamp,
                etype=self.event_type,
                wire=self.wire_name,
                thread=self.thread_id,
                state=self.thread_state,
                dev=REDACTED if self.device_id else "none",
                clip="yes" if self.preview_url else "no",
            )
        )


# ── parsing ──────────────────────────────────────────────────────────────────


def _pick_event(events: Mapping[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """Choose one event id from ``resourceUpdate.events`` deterministically.

    Known classes win in :data:`EVENT_PRIORITY` order; otherwise the first key
    in the payload's own order is used, so an event class Google adds later is
    still surfaced (with ``wire_name`` ``None``) rather than dropped.
    """
    for candidate in EVENT_PRIORITY:
        if candidate in events:
            return candidate, _as_mapping(events.get(candidate))
    for key, value in events.items():
        if isinstance(key, str) and key:
            return key, _as_mapping(value)
    return None, {}


def _any_preview_url(events: Mapping[str, Any]) -> str | None:
    """``previewUrl`` from **any** event payload in the envelope.

    A ``ClipPreview`` frequently rides along with the ``Motion`` event it
    describes, so the clip flag must not depend on which event won the
    priority tie-break above.
    """
    for value in events.values():
        url = _as_str(_as_mapping(value).get("previewUrl"))
        if url:
            return url
    return None


def parse_event(envelope: Any) -> NestEvent | None:
    """Parse an SDM event envelope. Tolerant; never raises.

    Returns ``None`` only when ``envelope`` is not an SDM envelope at all —
    that is, not a mapping, or a mapping carrying neither a ``resourceUpdate``
    nor a ``relationUpdate`` object. Everything else parses: unknown keys are
    ignored, missing optional keys become ``None``, a trait-only update parses
    with ``event_type is None``, and a relation update parses with
    :attr:`NestEvent.relation` set.
    """
    if not isinstance(envelope, Mapping):
        return None

    resource = envelope.get("resourceUpdate")
    relation = envelope.get("relationUpdate")
    has_resource = isinstance(resource, Mapping)
    has_relation = isinstance(relation, Mapping)
    if not has_resource and not has_relation:
        return None

    resource_map = _as_mapping(resource)
    events_map = _as_mapping(resource_map.get("events"))
    traits_map = _as_mapping(resource_map.get("traits"))

    event_type, payload = _pick_event(events_map)
    wire_name = constants.EVENT_WIRE_NAMES.get(event_type or "")

    device_name = _as_str(resource_map.get("name")) or ""
    if not device_name and has_relation:
        # A relation update names the device in `object` and the structure in
        # `subject`. https://developers.google.com/nest/device-access/api/events
        device_name = _as_str(_as_mapping(relation).get("object")) or ""

    return NestEvent(
        event_id=_as_str(envelope.get("eventId")) or "",
        timestamp=_as_str(envelope.get("timestamp")) or "",
        device_name=device_name,
        device_id=device_id_from_resource(device_name),
        event_type=event_type,
        wire_name=wire_name,
        event_session_id=_as_str(payload.get("eventSessionId")),
        sdm_event_id=_as_str(payload.get("eventId")),
        preview_url=_any_preview_url(events_map),
        thread_id=_as_str(envelope.get("eventThreadId")),
        thread_state=_as_str(envelope.get("eventThreadState")),
        traits=traits_map,
        relation=_as_mapping(relation) if has_relation else None,
        raw=dict(envelope),
    )


def _b64_decode(data: str) -> bytes | None:
    """Decode base64 ``data``, tolerating missing ``=`` padding and URL-safe alphabets.

    Pub/Sub documents ``PubsubMessage.data`` as base64. Real producers vary in
    whether they pad, so both forms decode here; anything undecodable returns
    ``None`` rather than raising.
    """
    if not isinstance(data, str) or not data:
        return None
    padded = data + "=" * (-len(data) % 4)
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            return decoder(padded)
        except (binascii.Error, ValueError):
            continue
    return None


def parse_pubsub_message(msg: Any) -> NestEvent | None:
    """Parse one Pub/Sub message into a :class:`NestEvent`. Tolerant; never raises.

    Accepts either a ``ReceivedMessage`` (``{"ackId": ..., "message": {...}}``)
    or a bare ``PubsubMessage`` (``{"data": <base64>, ...}``), because callers
    hold one or the other depending on which layer they are at. Returns
    ``None`` for a missing/undecodable ``data``, for a payload that is not
    JSON, or for JSON that is not an SDM envelope.
    """
    if not isinstance(msg, Mapping):
        return None
    inner = msg.get("message")
    payload = inner if isinstance(inner, Mapping) else msg
    raw = _b64_decode(payload.get("data"))
    if raw is None:
        return None
    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return parse_event(envelope)


# ── de-duplication ───────────────────────────────────────────────────────────


class EventDeduper:
    """Collapse an event thread and repeated ``eventSessionId`` deliveries.

    SDM publishes a ``STARTED`` / ``UPDATED`` / ``ENDED`` sequence for one
    physical happening, all sharing an ``eventThreadId``, and Pub/Sub itself
    guarantees at-least-once delivery — so the same message can arrive twice.
    Both collapse to a single handled event here.

    The de-dup key is, in order of preference, ``eventSessionId`` (Google's own
    "ID given to events occurring as part of a single session of related
    events"), then ``eventThreadId``, then the envelope ``eventId``. So two
    different session ids are always two events, even inside one thread.

    Bounded both ways: an entry expires ``ttl_s`` after it was **first** seen
    (not refreshed on each hit, so a pathological repeat stream cannot pin a key
    forever), and the map never holds more than ``max_keys`` entries — the
    oldest is evicted first. Purely a function of the injected ``now``; there is
    no clock inside.
    """

    def __init__(self, *, ttl_s: float = 300.0, max_keys: int = 4096) -> None:
        if ttl_s <= 0:
            raise ValueError(f"ttl_s must be positive, got {ttl_s}")
        if max_keys <= 0:
            raise ValueError(f"max_keys must be positive, got {max_keys}")
        self._ttl_s = float(ttl_s)
        self._max_keys = int(max_keys)
        self._first_seen: "OrderedDict[str, float]" = OrderedDict()
        self._hits = 0
        self._drops = 0

    # -- key ------------------------------------------------------------------

    @staticmethod
    def key_for(ev: NestEvent) -> str | None:
        """De-dup key for ``ev``, or ``None`` when it carries no usable id."""
        if ev.event_session_id:
            return f"session:{ev.event_session_id}"
        if ev.thread_id:
            return f"thread:{ev.thread_id}"
        if ev.event_id:
            return f"event:{ev.event_id}"
        return None

    # -- state ----------------------------------------------------------------

    def _purge(self, now: float) -> None:
        deadline = float(now) - self._ttl_s
        while self._first_seen:
            key, first = next(iter(self._first_seen.items()))
            if first > deadline:
                break
            self._first_seen.popitem(last=False)

    def seen(self, ev: NestEvent, now: float) -> bool:
        """``True`` when this event was already handled — the caller drops it.

        An event with no session id, thread id or event id is never suppressed
        (there is nothing to key on), so it is handled every time.
        """
        if not isinstance(ev, NestEvent):
            return False
        self._purge(now)
        key = self.key_for(ev)
        if key is None:
            return False
        if key in self._first_seen:
            self._drops += 1
            return True
        self._first_seen[key] = float(now)
        self._hits += 1
        while len(self._first_seen) > self._max_keys:
            self._first_seen.popitem(last=False)
        return False

    def __len__(self) -> int:
        return len(self._first_seen)

    def stats(self) -> dict[str, int]:
        """``{"tracked", "handled", "suppressed"}`` — counters, never payloads."""
        return {
            "tracked": len(self._first_seen),
            "handled": self._hits,
            "suppressed": self._drops,
        }

    def __repr__(self) -> str:
        return (
            f"<EventDeduper ttlS={self._ttl_s:g} maxKeys={self._max_keys} "
            f"tracked={len(self._first_seen)}>"
        )


# ── Pub/Sub pull transport ───────────────────────────────────────────────────


class PubSubError(RuntimeError):
    """A non-2xx Pub/Sub response. Carries ``status`` and a sanitised message.

    The response body is not embedded: a Pub/Sub error body can echo the
    subscription resource name, and the bearer token is never in a message here.
    """

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"pubsub {status}: {message}")
        self.status = int(status)
        self.message = message


def google_adc_token_provider(
    scopes: Sequence[str] = constants.PUBSUB_SUBSCRIBER_SCOPES,
) -> str:
    """A Pub/Sub-scoped access token from Application Default Credentials.

    ``google.auth`` is imported **inside** this function so that
    ``import iot_asp_autoroute.nest.events`` works with no ``google-*`` package
    installed (NEST_DESIGN.md #6). Raises :class:`PubSubError` with an install
    hint when the package is absent, so the caller sees a diagnosable failure
    rather than an ``ImportError`` from an unexpected depth.

    Source for the scopes: :data:`constants.PUBSUB_SUBSCRIBER_SCOPES`.
    """
    try:  # pragma: no cover - optional dependency, never installed in CI
        import google.auth  # noqa: PLC0415
        import google.auth.transport.requests  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001 - any import failure is the same story
        raise PubSubError(
            0,
            "google-auth is not installed; pass token_provider= explicitly or "
            "install google-auth to use Application Default Credentials",
        ) from exc
    credentials, _project = google.auth.default(scopes=list(scopes))
    credentials.refresh(google.auth.transport.requests.Request())
    token = getattr(credentials, "token", None)
    if not isinstance(token, str) or not token:
        raise PubSubError(0, "Application Default Credentials returned no token")
    return token


class PubSubPuller:
    """Synchronous pull + acknowledge against one Pub/Sub subscription.

    ``subscription`` is the full resource name
    ``projects/{gcp_project}/subscriptions/{subscription_id}``
    (:data:`constants.PUBSUB_SUBSCRIPTION_TEMPLATE`). ``token_provider()``
    returns a Pub/Sub-scoped access token and defaults to
    :func:`google_adc_token_provider`; ``transport`` is the injectable
    ``(method, url, headers, body) -> (status, headers, body)`` callable shared
    with :mod:`iot_asp_autoroute.nest.auth`, so tests never touch the network.

    This class does not sleep, retry, or hold a clock: one call, one round trip.
    """

    def __init__(
        self,
        subscription: str,
        *,
        token_provider: Callable[[], str] | None = None,
        transport: Transport | None = None,
    ) -> None:
        if not isinstance(subscription, str) or not subscription.strip():
            raise ValueError(
                "subscription is required, e.g. "
                "projects/{gcp_project}/subscriptions/{subscription_id} "
                f"(name only; see {constants.ENV_PUBSUB_SUBSCRIPTION})"
            )
        self._subscription = subscription.strip()
        self._token_provider: Callable[[], str] = (
            token_provider or google_adc_token_provider
        )
        self._transport: Transport = transport or urllib_transport
        self._pulls = 0
        self._acks = 0

    # -- internals ------------------------------------------------------------

    def _url(self, verb: str) -> str:
        return f"{constants.PUBSUB_API_BASE}/{self._subscription}:{verb}"

    def _post(self, verb: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._token_provider()}",
            "Content-Type": "application/json",
        }
        status, _resp_headers, raw = self._transport(
            "POST", self._url(verb), headers, body
        )
        if int(status) < 200 or int(status) >= 300:
            raise PubSubError(int(status), f"{verb} failed")
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    # -- public API -----------------------------------------------------------

    def pull(
        self, *, max_messages: int = _DEFAULT_MAX_MESSAGES
    ) -> list[tuple[str, NestEvent | None]]:
        """One ``:pull`` round trip → ``[(ackId, NestEvent | None), ...]``.

        ``maxMessages`` "must be a positive integer". Undecodable or non-SDM
        messages come back paired with ``None`` rather than being dropped, so
        the caller can still acknowledge them and not receive them forever.
        """
        count = int(max_messages)
        if count <= 0:
            raise ValueError(f"max_messages must be positive, got {max_messages}")
        count = min(count, _MAX_MESSAGES_CAP)
        payload = self._post("pull", {"maxMessages": count})
        self._pulls += 1

        received = payload.get("receivedMessages")
        if not isinstance(received, Sequence) or isinstance(received, (str, bytes)):
            return []
        out: list[tuple[str, NestEvent | None]] = []
        for item in received:
            if not isinstance(item, Mapping):
                continue
            ack_id = _as_str(item.get("ackId"))
            if ack_id is None:
                continue
            out.append((ack_id, parse_pubsub_message(item)))
        return out

    def acknowledge(self, ack_ids: Sequence[str]) -> None:
        """One ``:acknowledge`` round trip. A no-op for an empty list.

        The API states ``ackIds`` "must not be empty", so an empty sequence is
        answered locally instead of being sent and refused.
        """
        ids = [i for i in (ack_ids or ()) if isinstance(i, str) and i]
        if not ids:
            return
        self._post("acknowledge", {"ackIds": ids})
        self._acks += 1

    def status(self) -> dict[str, Any]:
        """Counters for ``poller.health()``. Names the subscription, not a token."""
        return {
            "subscription": self._subscription,
            "pulls": self._pulls,
            "acks": self._acks,
        }

    def __repr__(self) -> str:
        return f"<PubSubPuller pulls={self._pulls} acks={self._acks}>"
