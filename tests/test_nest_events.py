"""Tests for iot_asp_autoroute.nest.events + nest.mapping (#85 #86 #103) — offline.

Acceptance IDs NE-01 … NE-16 (events) and NM-01 … NM-10 (mapping) from
docs/specs/85-nest-google-home-integration.md.

Everything is deterministic: fixtures under ``tests/fixtures/nest/`` transcribed
from Google's own documentation examples (placeholders ``project-id``,
``device-id``, ``structure-id`` only), an injected transport that records every
request, and an injected clock. No network, no sleeps, no real identifiers, no
secret values.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "services" / "autoroute-adk"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from iot_asp_autoroute.nest import constants as nc  # noqa: E402
from iot_asp_autoroute.nest import events as ne  # noqa: E402
from iot_asp_autoroute.nest import mapping as nm  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "nest"
API_CONTRACT = ROOT / "docs" / "api-contract.md"

# Documentation placeholders only (NEST_DESIGN.md #5).
PROJECT_ID = "project-id"
DEVICE_ID = "device-id"
DEVICE_NAME = f"enterprises/{PROJECT_ID}/devices/{DEVICE_ID}"
SUBSCRIPTION = "projects/gcp-project/subscriptions/subscription-id"

#: Sentinels that must never reach the public wire.
PREVIEW_SENTINEL = "https://preview-sentinel.invalid/DO-NOT-LEAK-CLIP"
RAW_ID_SENTINEL = "RAW-DEVICE-ID-DO-NOT-LEAK"
TOKEN_SENTINEL = "Zx9-TOKEN-SENTINEL-9xZ"


# ── fixtures / fakes ─────────────────────────────────────────────────────────


def load(name: str) -> dict[str, Any]:
    """One documentation-derived envelope fixture."""
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class RecordingTransport:
    """Injected transport: replays queued ``(status, json_obj)``, records requests."""

    def __init__(self, responses: list[tuple[int, Any]]) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, str, dict[str, str], Any]] = []

    def __call__(self, method, url, headers, body=None):
        parsed = json.loads(body.decode("utf-8")) if body else None
        self.requests.append((method, url, dict(headers), parsed))
        if not self.responses:
            raise AssertionError(f"unexpected request: {method} {url}")
        status, payload = self.responses.pop(0)
        raw = b"" if payload is None else json.dumps(payload).encode("utf-8")
        return status, {"Content-Type": "application/json"}, raw

    @property
    def calls(self) -> int:
        return len(self.requests)


class StubEvent:
    """Duck-typed stand-in for NestEvent, so mapping stays independently testable."""

    def __init__(self, **kw: Any) -> None:
        self.wire_name = kw.get("wire_name")
        self.timestamp = kw.get("timestamp", "2019-01-01T00:00:01Z")
        self.device_id = kw.get("device_id", DEVICE_ID)
        self.event_session_id = kw.get("event_session_id")
        self.thread_id = kw.get("thread_id")
        self.thread_state = kw.get("thread_state")
        self.preview_url = kw.get("preview_url")


class StubDevice:
    def __init__(self, **kw: Any) -> None:
        self.device_id = kw.get("device_id", DEVICE_ID)
        self.type = kw.get("type", nc.TYPE_CAMERA)
        self.traits = kw.get("traits", {})
        self.connectivity = kw.get("connectivity")
        self.is_camera_like = kw.get("is_camera_like", True)


def walk_values(obj: Any):
    """Every scalar value at any nesting depth (keys included)."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from walk_values(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from walk_values(item)
    else:
        yield obj


# ── NE-01 … NE-05: one parse per documented event type ───────────────────────


@pytest.mark.parametrize(
    "fixture,event_type,wire_name,acoustic",
    [
        ("camera_sound", nc.EVENT_CAMERA_SOUND, "sound", True),
        ("doorbell_chime", nc.EVENT_DOORBELL_CHIME, "chime", True),
        ("camera_motion", nc.EVENT_CAMERA_MOTION, "motion", False),
        ("camera_person", nc.EVENT_CAMERA_PERSON, "person", False),
        ("clip_preview", nc.EVENT_CLIP_PREVIEW, "clip_preview", False),
    ],
)
def test_ne01_parses_each_documented_event_type(fixture, event_type, wire_name, acoustic):
    """NE-01: every documented event class parses into the right wire name."""
    ev = ne.parse_event(load(fixture))
    assert ev is not None
    assert ev.event_type == event_type
    assert ev.wire_name == wire_name
    assert ev.is_acoustic is acoustic
    assert ev.device_name == DEVICE_NAME
    assert ev.device_id == DEVICE_ID
    assert ev.timestamp == "2019-01-01T00:00:01Z"
    assert ev.event_session_id  # every documented payload carries one
    assert ev.raw["eventId"] == ev.event_id


def test_ne02_clip_preview_has_preview_url_and_no_inner_event_id():
    """NE-02: ClipPreview carries previewUrl and no inner eventId (trait page)."""
    ev = ne.parse_event(load("clip_preview"))
    assert ev is not None
    assert ev.preview_url == "https://previewUrl/..."
    assert ev.sdm_event_id is None
    assert ev.has_clip is True


def test_ne03_sound_event_carries_inner_event_id_not_a_preview_url():
    """NE-03: Sound is a detection signal — eventSessionId + eventId, no media."""
    ev = ne.parse_event(load("camera_sound"))
    assert ev is not None
    assert ev.sdm_event_id is not None
    assert ev.preview_url is None
    assert ev.thread_id is None and ev.thread_state is None  # absent in that example


def test_ne04_thread_state_is_read_from_the_envelope():
    """NE-04: eventThreadId / eventThreadState pass through when present."""
    ev = ne.parse_event(load("camera_motion"))
    assert ev is not None
    assert ev.thread_id == "d67cd3f7-86a7-425e-8bb3-462f92ec9f59"
    assert ev.thread_state == "STARTED"
    assert ev.thread_state in nc.EVENT_THREAD_STATES


def test_ne05_trait_update_without_events_key_still_parses():
    """NE-05: a trait-only resourceUpdate parses with event_type None."""
    ev = ne.parse_event(load("trait_update"))
    assert ev is not None
    assert ev.event_type is None
    assert ev.wire_name is None
    assert ev.is_acoustic is False
    assert "sdm.devices.traits.ThermostatMode" in ev.traits
    assert ev.traits["sdm.devices.traits.ThermostatMode"]["mode"] == "COOL"
    assert ev.relation is None


def test_ne06_relation_update_parses_into_relation():
    """NE-06: relationUpdate parses; the device comes from `object`."""
    ev = ne.parse_event(load("relation_update"))
    assert ev is not None
    assert ev.is_relation is True
    assert ev.relation is not None
    assert ev.relation["type"] == "CREATED"
    assert ev.relation["type"] in nc.RELATION_TYPES
    assert ev.device_id == DEVICE_ID
    assert ev.event_type is None


# ── NE-07 … NE-09: tolerance (negative controls) ─────────────────────────────


@pytest.mark.parametrize(
    "garbage",
    [
        None,
        "",
        "not-json-at-all",
        123,
        [],
        {},
        {"hello": "world"},
        {"eventId": "x", "timestamp": "y"},
        {"resourceUpdate": "not-a-mapping"},
        {"relationUpdate": 7},
        b"bytes",
    ],
)
def test_ne07_parse_event_returns_none_for_non_envelopes(garbage):
    """NE-07 (negative): garbage is None, never an exception."""
    assert ne.parse_event(garbage) is None


@pytest.mark.parametrize(
    "envelope",
    [
        {"resourceUpdate": {}},
        {"resourceUpdate": {"name": 42, "events": "nope", "traits": None}},
        {"resourceUpdate": {"name": DEVICE_NAME, "events": {"": {}}}},
        {"resourceUpdate": {"name": DEVICE_NAME, "events": {"x.y.Z": None}}},
        {"resourceUpdate": {"name": DEVICE_NAME}, "eventThreadState": 5},
        {"relationUpdate": {}},
    ],
)
def test_ne08_malformed_envelopes_parse_without_raising(envelope):
    """NE-08 (negative): a malformed but SDM-shaped envelope degrades, never raises."""
    ev = ne.parse_event(envelope)
    assert ev is not None
    assert isinstance(ev.event_id, str)
    assert isinstance(ev.traits, dict)


def test_ne09_unknown_event_class_is_surfaced_with_no_wire_name():
    """NE-09: an event class Google adds later is kept, not silently dropped."""
    ev = ne.parse_event(
        {
            "eventId": "e",
            "timestamp": "2019-01-01T00:00:01Z",
            "resourceUpdate": {
                "name": DEVICE_NAME,
                "events": {
                    "sdm.devices.events.SomethingNew.Thing": {"eventSessionId": "s"}
                },
            },
            "unknownTopLevelKey": {"ignored": True},
        }
    )
    assert ev is not None
    assert ev.event_type == "sdm.devices.events.SomethingNew.Thing"
    assert ev.wire_name is None
    assert ev.event_session_id == "s"


def test_ne10_combined_motion_and_clip_uses_priority_and_keeps_the_clip_flag():
    """NE-10: one envelope with two events resolves deterministically."""
    envelope = load("camera_motion")
    envelope["resourceUpdate"]["events"][nc.EVENT_CLIP_PREVIEW] = {
        "eventSessionId": "CjY5Y3VKaTZwR3o4Y19YbTVfMF...",
        "previewUrl": "https://previewUrl/...",
    }
    ev = ne.parse_event(envelope)
    assert ev is not None
    assert ev.event_type == nc.EVENT_CAMERA_MOTION  # motion outranks clip_preview
    assert ev.has_clip is True

    envelope["resourceUpdate"]["events"][nc.EVENT_CAMERA_SOUND] = {
        "eventSessionId": "CjY5Y3VKaTZwR3o4Y19YbTVfMF...",
        "eventId": "si_...",
    }
    assert ne.parse_event(envelope).event_type == nc.EVENT_CAMERA_SOUND


# ── NE-11: base64 Pub/Sub decode ─────────────────────────────────────────────


def test_ne11_pubsub_decode_padded_unpadded_and_garbage():
    """NE-11: padded and unpadded base64 both decode; junk is None, not a raise."""
    response = json.loads((FIXTURES / "pubsub_pull_response.json").read_text())
    messages = response["receivedMessages"]

    padded, unpadded, junk = messages
    assert padded["message"]["data"].endswith("=")  # the padded branch is real
    assert "=" not in unpadded["message"]["data"]  # and so is the unpadded one

    ev_padded = ne.parse_pubsub_message(padded)
    assert ev_padded is not None and ev_padded.wire_name == "sound"
    ev_unpadded = ne.parse_pubsub_message(unpadded)
    assert ev_unpadded is not None and ev_unpadded.wire_name == "chime"
    assert ne.parse_pubsub_message(junk) is None

    # a bare PubsubMessage (no ackId wrapper) is accepted too
    assert ne.parse_pubsub_message(padded["message"]) is not None


@pytest.mark.parametrize(
    "msg",
    [
        None,
        {},
        {"message": {}},
        {"message": {"data": None}},
        {"data": "!!!not-base64!!!"},
        {"data": base64.b64encode(b"\xff\xfe not utf-8").decode()},
        {"data": base64.b64encode(b'{"hello": "world"}').decode()},
        {"data": base64.b64encode(b"[1,2,3]").decode()},
    ],
)
def test_ne12_parse_pubsub_message_negative_controls(msg):
    """NE-12 (negative): every undecodable / non-SDM payload is None."""
    assert ne.parse_pubsub_message(msg) is None


# ── NE-13: thread de-duplication ─────────────────────────────────────────────


def thread_event(state: str, *, session: str = "session-a", thread: str = "thread-1"):
    return ne.parse_event(
        {
            "eventId": f"envelope-{state}",
            "timestamp": "2019-01-01T00:00:01Z",
            "resourceUpdate": {
                "name": DEVICE_NAME,
                "events": {nc.EVENT_CAMERA_SOUND: {"eventSessionId": session}},
            },
            "eventThreadId": thread,
            "eventThreadState": state,
        }
    )


def test_ne13_thread_started_updated_ended_is_handled_once():
    """NE-13: one eventThreadId / eventSessionId collapses to a single event."""
    dedup = ne.EventDeduper(ttl_s=300.0, max_keys=16)
    assert dedup.seen(thread_event("STARTED"), 0.0) is False
    assert dedup.seen(thread_event("UPDATED"), 1.0) is True
    assert dedup.seen(thread_event("ENDED"), 2.0) is True
    assert dedup.stats() == {"tracked": 1, "handled": 1, "suppressed": 2}


def test_ne13b_two_event_session_ids_are_two_events():
    """NE-13b: a different eventSessionId is a different happening."""
    dedup = ne.EventDeduper()
    assert dedup.seen(thread_event("STARTED", session="session-a"), 0.0) is False
    assert dedup.seen(thread_event("STARTED", session="session-b"), 0.5) is False
    assert len(dedup) == 2


def test_ne13c_thread_id_keys_when_there_is_no_session_id():
    """NE-13c: a session-less thread still collapses on eventThreadId."""
    def ev(state):
        return ne.parse_event(
            {
                "eventId": f"env-{state}",
                "timestamp": "2019-01-01T00:00:01Z",
                "resourceUpdate": {"name": DEVICE_NAME, "traits": {}},
                "eventThreadId": "thread-9",
                "eventThreadState": state,
            }
        )

    dedup = ne.EventDeduper()
    assert dedup.seen(ev("STARTED"), 0.0) is False
    assert dedup.seen(ev("ENDED"), 1.0) is True


def test_ne14_deduper_is_ttl_and_size_bounded():
    """NE-14: entries expire on the injected clock and the map never grows past max_keys."""
    dedup = ne.EventDeduper(ttl_s=10.0, max_keys=3)
    assert dedup.seen(thread_event("STARTED"), 0.0) is False
    assert dedup.seen(thread_event("UPDATED"), 5.0) is True
    # after the TTL the key is gone, so the same session is handled again
    assert dedup.seen(thread_event("UPDATED"), 11.0) is False

    dedup = ne.EventDeduper(ttl_s=1000.0, max_keys=3)
    for i in range(10):
        dedup.seen(thread_event("STARTED", session=f"s{i}"), float(i))
    assert len(dedup) == 3


def test_ne14b_deduper_negative_controls():
    """NE-14b (negative): bad construction refused; unkeyable events never suppressed."""
    with pytest.raises(ValueError):
        ne.EventDeduper(ttl_s=0.0)
    with pytest.raises(ValueError):
        ne.EventDeduper(max_keys=0)

    dedup = ne.EventDeduper()
    bare = ne.parse_event({"resourceUpdate": {"name": DEVICE_NAME}})
    assert ne.EventDeduper.key_for(bare) is None
    assert dedup.seen(bare, 0.0) is False
    assert dedup.seen(bare, 1.0) is False
    assert dedup.seen("not an event", 0.0) is False  # type: ignore[arg-type]


# ── NE-15: Pub/Sub puller (offline) ──────────────────────────────────────────


def make_puller(transport, subscription: str = SUBSCRIPTION) -> ne.PubSubPuller:
    return ne.PubSubPuller(
        subscription,
        token_provider=lambda: TOKEN_SENTINEL,
        transport=transport,
    )


def test_ne15_pull_and_acknowledge_use_the_documented_endpoints():
    """NE-15: :pull and :acknowledge URLs and bodies match the Pub/Sub REST reference."""
    response = json.loads((FIXTURES / "pubsub_pull_response.json").read_text())
    tr = RecordingTransport([(200, response), (200, {})])
    puller = make_puller(tr)

    pulled = puller.pull(max_messages=10)
    assert [ack for ack, _ in pulled] == ["ack-id-0", "ack-id-1", "ack-id-2"]
    assert [ev.wire_name if ev else None for _, ev in pulled] == ["sound", "chime", None]

    method, url, headers, body = tr.requests[0]
    assert method == "POST"
    assert url == f"{nc.PUBSUB_API_BASE}/{SUBSCRIPTION}:pull"
    assert body == {"maxMessages": 10}
    assert headers["Authorization"] == f"Bearer {TOKEN_SENTINEL}"

    puller.acknowledge([ack for ack, _ in pulled])
    method, url, _headers, body = tr.requests[1]
    assert url == f"{nc.PUBSUB_API_BASE}/{SUBSCRIPTION}:acknowledge"
    assert body == {"ackIds": ["ack-id-0", "ack-id-1", "ack-id-2"]}
    assert puller.status()["pulls"] == 1 and puller.status()["acks"] == 1


def test_ne15b_puller_negative_controls():
    """NE-15b (negative): empty ack is a no-op, non-2xx raises, bad args refused."""
    tr = RecordingTransport([])
    puller = make_puller(tr)

    puller.acknowledge([])
    puller.acknowledge(["", None])  # type: ignore[list-item]
    assert tr.calls == 0  # never sent: the API states ackIds must not be empty

    with pytest.raises(ValueError):
        puller.pull(max_messages=0)
    assert tr.calls == 0

    with pytest.raises(ValueError):
        ne.PubSubPuller("   ", token_provider=lambda: TOKEN_SENTINEL)

    tr = RecordingTransport([(403, {"error": {"message": "nope"}})])
    with pytest.raises(ne.PubSubError) as exc:
        make_puller(tr).pull()
    assert exc.value.status == 403

    # a response with no / malformed receivedMessages yields an empty list
    for payload in ({}, {"receivedMessages": None}, {"receivedMessages": [{}, 7]}):
        assert make_puller(RecordingTransport([(200, payload)])).pull() == []


def test_ne16_no_token_or_site_id_in_any_repr():
    """NE-16 (negative): repr of an event or a puller leaks no id, URL or token."""
    tr = RecordingTransport([])
    puller = make_puller(tr)
    assert TOKEN_SENTINEL not in repr(puller)

    ev = ne.parse_event(
        {
            "eventId": "e",
            "timestamp": "2019-01-01T00:00:01Z",
            "resourceUpdate": {
                "name": f"enterprises/{PROJECT_ID}/devices/{RAW_ID_SENTINEL}",
                "events": {nc.EVENT_CLIP_PREVIEW: {"previewUrl": PREVIEW_SENTINEL}},
            },
        }
    )
    assert ev is not None
    text = repr(ev)
    assert RAW_ID_SENTINEL not in text
    assert PREVIEW_SENTINEL not in text
    assert ne.REDACTED in text


# ── NM-01 … NM-04: mapping onto the existing wire ────────────────────────────


def test_nm01_acoustic_event_reuses_the_existing_burst_fields():
    """NM-01: sound / chime land on event + soundBurst + vibClass (#86 #103)."""
    for fixture in ("camera_sound", "doorbell_chime"):
        ev = ne.parse_event(load(fixture))
        out = nm.event_to_telemetry(ev, node_id="node1", now=1546300801.0)
        assert out["schemaVersion"] == 1
        assert out["deviceId"] == "node1"
        assert out["ts"] == "2019-01-01T00:00:01Z"
        assert out["event"] == "soundBurst"
        assert out["soundBurst"] is True
        assert out["vibClass"] == "acoustic"
        assert out["nestEvent"] in nc.ACOUSTIC_EVENTS
        assert out["nestSource"] == "event"


def test_nm02_non_acoustic_events_never_touch_the_burst_path():
    """NM-02 (negative): motion / person / clip_preview set no burst field."""
    for fixture in ("camera_motion", "camera_person", "clip_preview"):
        ev = ne.parse_event(load(fixture))
        out = nm.event_to_telemetry(ev, node_id="node1")
        assert "event" not in out
        assert "soundBurst" not in out
        assert "vibClass" not in out
        assert out["nestEvent"] == ev.wire_name


def test_nm03_optional_fields_and_source():
    """NM-03: device type / connectivity / clip flag are additive and optional."""
    ev = ne.parse_event(load("clip_preview"))
    out = nm.event_to_telemetry(
        ev,
        node_id="node1",
        source="poll",
        device_type=nc.TYPE_DOORBELL,
        connectivity="ONLINE",
    )
    assert out["nestSource"] == "poll"
    assert out["nestDeviceType"] == nc.TYPE_DOORBELL
    assert out["nestConnectivity"] == "ONLINE"
    assert out["nestClipAvailable"] is True
    assert out["nestEventSessionId"] == ev.event_session_id

    bare = nm.event_to_telemetry(ev, node_id="node1")
    assert "nestDeviceType" not in bare and "nestConnectivity" not in bare
    assert nm.event_to_telemetry(ev, node_id="node1", source="nonsense")["nestSource"] == "event"


def test_nm04_ts_falls_back_to_the_injected_clock():
    """NM-04: an absent / unparseable timestamp uses the injected now, never a real clock."""
    ev = StubEvent(wire_name="sound", timestamp=None)
    assert nm.event_to_telemetry(ev, node_id="n", now=0.0)["ts"] == "1970-01-01T00:00:00Z"
    ev = StubEvent(wire_name="sound", timestamp="not-a-timestamp")
    assert nm.event_to_telemetry(ev, node_id="n", now=86400.0)["ts"] == "1970-01-02T00:00:00Z"
    # fractional seconds and offsets normalise to the repo's UTC format
    ev = StubEvent(wire_name="sound", timestamp="2019-01-01T00:00:01.5Z")
    assert nm.event_to_telemetry(ev, node_id="n")["ts"] == "2019-01-01T00:00:01Z"


def test_nm05_node_id_is_required():
    """NM-05 (negative): a missing node id is refused, never silently defaulted."""
    ev = ne.parse_event(load("camera_sound"))
    for bad in (None, "", "   ", 7):
        with pytest.raises(ValueError):
            nm.event_to_telemetry(ev, node_id=bad)  # type: ignore[arg-type]


# ── NM-06: PII containment ───────────────────────────────────────────────────


def test_nm06_no_preview_url_or_raw_device_id_at_any_depth():
    """NM-06 (negative, the PII gate): sentinels appear in NO value of the telemetry."""
    ev = ne.parse_event(
        {
            "eventId": "e",
            "timestamp": "2019-01-01T00:00:01Z",
            "resourceUpdate": {
                "name": f"enterprises/{PROJECT_ID}/devices/{RAW_ID_SENTINEL}",
                "events": {
                    nc.EVENT_CAMERA_SOUND: {
                        "eventSessionId": "session-a",
                        "eventId": "inner",
                    },
                    nc.EVENT_CLIP_PREVIEW: {"previewUrl": PREVIEW_SENTINEL},
                },
            },
            "userId": "AVPHwEuBfnPOnTqzVFT4IONX2Qqhu9EJ4ubO-bNnQ-yi",
            "resourceGroup": [f"enterprises/{PROJECT_ID}/structures/structure-id"],
        }
    )
    assert ev is not None
    assert ev.preview_url == PREVIEW_SENTINEL  # held in memory …
    assert ev.device_id == RAW_ID_SENTINEL

    out = nm.event_to_telemetry(ev, node_id="node1", device_type=nc.TYPE_CAMERA)
    blob = json.dumps(out)
    for sentinel in (PREVIEW_SENTINEL, RAW_ID_SENTINEL, "structure-id", "previewUrl"):
        assert sentinel not in blob, f"{sentinel} leaked into telemetry"
    for value in walk_values(out):
        if isinstance(value, str):
            assert PREVIEW_SENTINEL not in value
            assert RAW_ID_SENTINEL not in value

    # … and the wire carries the hash instead
    assert out["nestDeviceRef"] == nm.device_ref(RAW_ID_SENTINEL)
    assert out["nestClipAvailable"] is True

    # device_to_state (private tree) is safe too: no raw id, no trait values
    state = nm.device_to_state(
        StubDevice(
            device_id=RAW_ID_SENTINEL,
            traits={nc.TRAIT_INFO: {"customName": "DO-NOT-LEAK-CUSTOM-NAME"}},
            connectivity="ONLINE",
        )
    )
    state_blob = json.dumps(state)
    assert RAW_ID_SENTINEL not in state_blob
    assert "DO-NOT-LEAK-CUSTOM-NAME" not in state_blob
    assert state["nestDeviceRef"] == nm.device_ref(RAW_ID_SENTINEL)
    assert state["nestTraits"] == [nc.TRAIT_INFO]


def test_nm07_device_ref_is_stable_truncated_sha256():
    """NM-07: the ref is sha256[:12], identical for a bare id and a resource name."""
    import hashlib

    expected = hashlib.sha256(DEVICE_ID.encode()).hexdigest()[:12]
    assert nm.device_ref(DEVICE_ID) == expected
    assert nm.device_ref(DEVICE_NAME) == expected
    assert len(nm.device_ref(DEVICE_ID)) == nm.DEVICE_REF_LEN
    assert nm.device_ref(DEVICE_ID) != nm.device_ref("other-device-id")
    for empty in ("", "   ", None, 7, "/"):
        assert nm.device_ref(empty) == ""  # type: ignore[arg-type]


# ── NM-08: never a control or patch field ────────────────────────────────────


def test_nm08_mapper_never_sets_hold_sudden_vol_or_a_patch_field():
    """NM-08 (negative): a Nest observation can never author or influence a patch."""
    for fixture in (
        "camera_sound",
        "doorbell_chime",
        "camera_motion",
        "camera_person",
        "clip_preview",
        "trait_update",
        "relation_update",
    ):
        ev = ne.parse_event(load(fixture))
        out = nm.event_to_telemetry(
            ev, node_id="node1", device_type=nc.TYPE_CAMERA, connectivity="ONLINE"
        )
        leaked = nm.FORBIDDEN_KEYS & set(out)
        assert not leaked, f"{fixture} emitted forbidden key(s): {sorted(leaked)}"
        assert out["schemaVersion"] == 1  # never bumped (NEST_DESIGN.md #1)


# ── NM-09: every emitted key is documented or `nest`-namespaced ──────────────


def documented_wire_fields() -> set[str]:
    """Field names quoted in backticks anywhere in docs/api-contract.md."""
    text = API_CONTRACT.read_text(encoding="utf-8")
    return set(re.findall(r"`([A-Za-z][A-Za-z0-9_]*)`", text))


def test_nm09_emitted_keys_are_documented_or_nest_namespaced():
    """NM-09: additive-only — no undocumented, non-`nest` key ever reaches the wire."""
    documented = documented_wire_fields()
    assert {"schemaVersion", "deviceId", "ts", "soundBurst", "vibClass", "event"} <= documented

    emitted: set[str] = set()
    for fixture in (
        "camera_sound",
        "doorbell_chime",
        "camera_motion",
        "camera_person",
        "clip_preview",
        "trait_update",
        "relation_update",
    ):
        ev = ne.parse_event(load(fixture))
        emitted |= set(
            nm.event_to_telemetry(
                ev, node_id="node1", device_type=nc.TYPE_CAMERA, connectivity="ONLINE"
            )
        )
    emitted |= set(nm.event_to_telemetry(StubEvent(wire_name="sound"), node_id="n"))

    undocumented = {k for k in emitted if k not in documented and not k.startswith("nest")}
    assert not undocumented, f"undocumented non-nest wire keys: {sorted(undocumented)}"
    assert {"nestSource", "nestEvent", "nestDeviceRef"} <= emitted


# ── NM-10: mapping stays stdlib-only and import-safe ─────────────────────────


def test_nm10_modules_add_no_third_party_imports():
    """NM-10: importing events/mapping pulls in no google-*/numpy/scipy module.

    Measured as a *delta* in a fresh interpreter: whatever the parent
    ``iot_asp_autoroute`` package already loads is not this module's business,
    but these two modules must add nothing beyond the stdlib. The ADC token
    provider must still exist — it is lazy, not absent (NEST_DESIGN.md #6).
    """
    import subprocess

    probe = (
        "import sys, importlib\n"
        "import iot_asp_autoroute.nest\n"
        "for m in [k for k in sys.modules if 'nest.events' in k or 'nest.mapping' in k]:\n"
        "    del sys.modules[m]\n"
        "before = set(sys.modules)\n"
        "events = importlib.import_module('iot_asp_autoroute.nest.events')\n"
        "mapping = importlib.import_module('iot_asp_autoroute.nest.mapping')\n"
        "added = set(sys.modules) - before\n"
        "leaked = sorted(m for m in added if m.split('.')[0] in "
        "('google', 'numpy', 'scipy', 'requests'))\n"
        "assert not leaked, leaked\n"
        "assert callable(events.google_adc_token_provider)\n"
        "assert callable(mapping.event_to_telemetry)\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(PKG_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_nm10b_no_top_level_third_party_import_in_either_module():
    """NM-10b: google/numpy/scipy appear in no module-level import statement."""
    import ast

    for name in ("events", "mapping"):
        path = PKG_ROOT / "iot_asp_autoroute" / "nest" / f"{name}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:  # module level only — a lazy import is nested
            roots: list[str] = []
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = [node.module.split(".")[0]]
            forbidden = {"google", "numpy", "scipy", "requests"} & set(roots)
            assert not forbidden, f"{name}.py imports {sorted(forbidden)} at module level"
