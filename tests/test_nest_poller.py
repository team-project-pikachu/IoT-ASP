"""Tests for iot_asp_autoroute.nest.poller (#85) — offline, deterministic, stdlib-only.

Acceptance IDs NP-01 … NP-28. The premise of #85 is CONTINUOUS observation, explicitly
not bursts, so the scheduler is checked the same three independent ways the limiter is:

 (1) STRUCTURAL — ``plan()`` is pure, ``step()`` makes at most one API call, and a
                  cadence faster than the documented floor is refused rather than clamped.
 (2) SIMULATION — a simulated clock drives a 3-camera fleet plus a Pub/Sub event stream
                  through ``run_forever`` for hours of simulated time, recording every
                  call the fake client received.
 (3) RECOMPUTATION — :func:`max_calls_in_window` re-derives the busiest 60 s and 3600 s
                  window **from that call log alone** and asserts it never exceeds the
                  quota published at
                  https://developers.google.com/nest/device-access/project/limits.

Negative controls: patch-path refusal (both the delegated and the bare-env guard),
patch-field refusal on the wire, Hold / Manual (observation continues, authorship never
starts), a faster-than-floor cadence, and PII (no raw SDM device id in any result).

Fixtures use Google's own documentation placeholders (``project-id``, ``device-id``);
no real SDM identifier appears anywhere in this file.

Run: PYTHONPATH=services/autoroute-adk python3 -m pytest tests/test_nest_poller.py -q
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from bisect import bisect_left
from pathlib import Path
from typing import Any, Sequence

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "services" / "autoroute-adk"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from iot_asp_autoroute import gcs_io  # noqa: E402
from iot_asp_autoroute.nest import constants, events, mapping, poller  # noqa: E402
from iot_asp_autoroute.nest.poller import (  # noqa: E402
    NestPoller,
    PatchWriteRefused,
    PollAction,
)
from iot_asp_autoroute.nest.rate_limit import SdmRateLimiter  # noqa: E402
from iot_asp_autoroute.nest.sdm_client import (  # noqa: E402
    NestDevice,
    SdmError,
    SdmThrottled,
)

FIXTURES = ROOT / "tests" / "fixtures" / "nest"
POLLER_SRC = PKG_ROOT / "iot_asp_autoroute" / "nest" / "poller.py"
NEST_DEV_SH = ROOT / "scripts" / "nest_dev.sh"

# Documented quotas quoted as literals, so relaxing a constant fails here too.
# Source: https://developers.google.com/nest/device-access/project/limits
DOC_LIST_QPM = 5
DOC_GET_QPM = 10
DOC_CAMERA_QPM = 30
DOC_CAMERA_QPH = 100

NODE = "node1"
# Google's documentation placeholders — never a real SDM device id (CLAUDE.md #7).
CAMERA_IDS = ("device-id", "device-id-2", "device-id-3")
WALL_EPOCH = 1767225600.0  # fixed 2026-01-01T00:00:00Z, so every ``ts`` is deterministic


# --------------------------------------------------------------------------- #
# Independent recomputation checker (same convention as tests/test_nest_rate_limit.py:
# a call at t occupies the half-open interval [t, t + span)).
# --------------------------------------------------------------------------- #


def max_calls_in_window(times: Sequence[float], span: float) -> int:
    """Busiest window of length ``span``, computed from the call log alone."""
    ts = sorted(float(t) for t in times)
    best = 0
    for i, start in enumerate(ts):
        j = bisect_left(ts, start + float(span))
        best = max(best, j - i)
    return best


def min_gap(times: Sequence[float]) -> float:
    ts = sorted(float(t) for t in times)
    if len(ts) < 2:
        return float("inf")
    return min(b - a for a, b in zip(ts, ts[1:]))


# --------------------------------------------------------------------------- #
# Test doubles — a simulated clock and a client that only records.
# --------------------------------------------------------------------------- #


class FakeClock:
    """Simulated monotonic clock. Only ``sleep`` moves it; nothing ever blocks."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = float(start)
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(float(seconds))
        self.t += float(seconds)


def make_device(device_id: str, *, status: str = "ONLINE", doorbell: bool = False) -> NestDevice:
    traits: dict[str, Any] = {constants.TRAIT_CONNECTIVITY: {"status": status}}
    traits[constants.TRAIT_DOORBELL_CHIME if doorbell else constants.TRAIT_CAMERA_SOUND] = {}
    return NestDevice.from_api(
        {
            "name": f"enterprises/project-id/devices/{device_id}",
            "type": constants.TYPE_DOORBELL if doorbell else constants.TYPE_CAMERA,
            "traits": traits,
        }
    )


class FakeClient:
    """Records every call it is asked to make; optionally gated by a real limiter.

    ``limiter`` mirrors what ``SdmClient`` does: ask the limiter first and raise
    :class:`SdmThrottled` (never sleep, never burst) when the budget is not yet there.
    """

    def __init__(
        self,
        device_ids: Sequence[str] = CAMERA_IDS,
        *,
        limiter: Any | None = None,
        fail_times: int = 0,
        connectivity: dict[str, str] | None = None,
    ) -> None:
        self._ids = list(device_ids)
        self._limiter = limiter
        self._fail_times = int(fail_times)
        self._connectivity = dict(connectivity or {})
        #: (method, device_id | None, time) for every call that actually happened.
        self.log: list[tuple[str, str | None, float]] = []
        self.throttles = 0

    # -- helpers --------------------------------------------------------------

    def _gate(self, method: str, device_id: str | None, device_type: str | None, now: float):
        if self._limiter is None:
            return
        if not self._limiter.try_acquire(
            method, device_id=device_id, device_type=device_type, now=now
        ):
            self.throttles += 1
            retry_at = self._limiter.next_allowed_at(
                method, device_id=device_id, device_type=device_type, now=now
            )
            raise SdmThrottled(
                "budget not available yet", retry_at=float(retry_at),
                method=method, device_id=device_id,
            )

    def _maybe_fail(self) -> None:
        if self._fail_times > 0:
            self._fail_times -= 1
            raise SdmError("simulated 500", status=500, rpc_code="INTERNAL", retryable=True)

    # -- SdmClient surface ----------------------------------------------------

    def list_devices(self, *, now: float | None = None) -> list[NestDevice]:
        at = float(now if now is not None else 0.0)
        self._gate(constants.METHOD_DEVICES_LIST, None, None, at)
        self.log.append((constants.METHOD_DEVICES_LIST, None, at))
        self._maybe_fail()
        return [
            make_device(d, status=self._connectivity.get(d, "ONLINE")) for d in self._ids
        ]

    def get_device(
        self, device_id: str, *, device_type: str | None = None, now: float | None = None
    ) -> NestDevice:
        at = float(now if now is not None else 0.0)
        self._gate(constants.METHOD_DEVICES_GET, device_id, device_type, at)
        self.log.append((constants.METHOD_DEVICES_GET, device_id, at))
        self._maybe_fail()
        return make_device(device_id, status=self._connectivity.get(device_id, "ONLINE"))

    def status(self) -> dict[str, Any]:
        return {"calls": len(self.log)}

    # -- assertions -----------------------------------------------------------

    @property
    def calls(self) -> int:
        return len(self.log)

    def times(self, method: str, device_id: str | None = None) -> list[float]:
        return [
            t
            for m, d, t in self.log
            if m == method and (device_id is None or d == device_id)
        ]


class FakePuller:
    """Replays the SDM fixture envelopes as if Pub/Sub had delivered them."""

    def __init__(self, envelopes: Sequence[dict[str, Any]] | None = None, *, repeat: bool = False):
        self._source = list(envelopes or [])
        self._repeat = repeat
        self.queue = [
            (f"ack-{i}", events.parse_event(e)) for i, e in enumerate(self._source)
        ]
        self.acked: list[str] = []
        self.pulls = 0

    def pull(self, *, max_messages: int = 10):
        self.pulls += 1
        if not self.queue and self._repeat:
            self.queue = [
                (f"ack-r{self.pulls}-{i}", events.parse_event(e))
                for i, e in enumerate(self._source)
            ]
        batch, self.queue = self.queue[:max_messages], self.queue[max_messages:]
        return batch

    def acknowledge(self, ack_ids) -> None:
        self.acked.extend(ack_ids)

    def status(self) -> dict[str, Any]:
        return {"pulls": self.pulls, "acks": len(self.acked)}


class RecordingSink:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def __call__(self, telemetry: dict[str, Any]) -> None:
        self.rows.append(dict(telemetry))


def load_envelopes() -> list[dict[str, Any]]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(FIXTURES.glob("*.json"))
        if p.name != "pubsub_pull_response.json"
    ]


@pytest.fixture
def dry_root(tmp_path, monkeypatch):
    """Dry-run mirror under tmp_path so no test writes into the repo's .autoroute-dry."""
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(tmp_path))
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_RUN", "1")
    monkeypatch.delenv("IOT_ASP_GCS_BUCKET", raising=False)
    monkeypatch.setattr(gcs_io, "DRY_RUN", True)
    monkeypatch.setattr(gcs_io, "DRY_ROOT", tmp_path)
    monkeypatch.setattr(gcs_io, "BUCKET", "")
    return tmp_path


def build(
    *,
    client: Any | None = None,
    limiter: Any | None = None,
    clock: FakeClock | None = None,
    sink: Any | None = None,
    puller: Any | None = None,
    **kwargs: Any,
) -> tuple[NestPoller, FakeClient, FakeClock, RecordingSink]:
    """A poller wired to test doubles with a seeded RNG and a fixed wall clock."""
    clk = clock or FakeClock()
    lim = limiter
    cli = client if client is not None else FakeClient(limiter=lim)
    snk = sink if sink is not None else RecordingSink()
    kwargs.setdefault("write_state", False)
    np = NestPoller(
        cli,
        node_id=NODE,
        puller=puller,
        sink=snk,
        limiter=lim,
        clock=clk,
        wall_clock=lambda: WALL_EPOCH + clk.t,
        rng=random.Random(85),
        **kwargs,
    )
    return np, cli, clk, snk


# --------------------------------------------------------------------------- #
# (1) STRUCTURAL
# --------------------------------------------------------------------------- #


# NP-01 the derived floors are the defaults, and they are the documented arithmetic
def test_np01_default_cadences_are_the_documented_floors():
    np, _c, _k, _s = build()
    health = np.health()
    assert health["listCadenceS"] == constants.DEFAULT_LIST_CADENCE_S == 12.0
    assert health["cameraCadenceS"] == constants.DEFAULT_CAMERA_CADENCE_S == 36.0
    assert 60.0 / DOC_LIST_QPM == 12.0
    assert 3600.0 / DOC_CAMERA_QPH == 36.0
    assert health["writesPatches"] is False
    # The SDM floors above are quota-derived. The EVENT cadence is the opposite case:
    # it defaults to the spin-guard floor, because a Pub/Sub `:pull` long-polls on the
    # server and returns as soon as a message exists. Any client-side sleep between
    # pulls is pure added latency on every burst (#103 "respond immediately"), which is
    # why `returnImmediately` is deprecated upstream. If someone raises this default,
    # this assertion should stop them and make them justify it.
    assert health["eventsCadenceS"] == poller.MIN_EVENTS_CADENCE_S == 1.0
    assert health["eventsCadenceS"] < constants.DEFAULT_LIST_CADENCE_S, (
        "the reactive path must never be slower than the liveness path"
    )


# NP-02 a cadence FASTER than the floor is refused, never silently clamped
@pytest.mark.parametrize(
    "kwargs",
    [
        {"list_cadence_s": 11.999},
        {"list_cadence_s": 0.0},
        {"list_cadence_s": -1.0},
        {"camera_cadence_s": 35.9},
        {"camera_cadence_s": 2.0},  # the QPM cap alone would allow this; QPH does not
        {"events_cadence_s": 0.5},
        {"events_cadence_s": float("nan")},
        {"list_cadence_s": "fast"},
    ],
)
def test_np02_faster_than_floor_is_refused(kwargs):
    with pytest.raises(ValueError):
        NestPoller(FakeClient(), node_id=NODE, **kwargs)


# NP-03 exactly the floor, and anything slower, is accepted
@pytest.mark.parametrize(
    "kwargs",
    [
        {"list_cadence_s": constants.DEFAULT_LIST_CADENCE_S},
        {"camera_cadence_s": constants.DEFAULT_CAMERA_CADENCE_S},
        {"list_cadence_s": 60.0, "camera_cadence_s": 300.0, "events_cadence_s": 30.0},
    ],
)
def test_np03_floor_and_slower_are_accepted(kwargs):
    np = NestPoller(FakeClient(), node_id=NODE, **kwargs)
    assert np.health()["consecutiveErrors"] == 0


# NP-04 node_id and jitter_frac are validated
@pytest.mark.parametrize("bad", ["", "   ", None])
def test_np04_node_id_required(bad):
    with pytest.raises(ValueError):
        NestPoller(FakeClient(), node_id=bad)


@pytest.mark.parametrize("bad", [-0.1, 1.0, 2.0])
def test_np04_jitter_frac_range(bad):
    with pytest.raises(ValueError):
        NestPoller(FakeClient(), node_id=NODE, jitter_frac=bad)


# NP-05 plan() is PURE: same `now` -> same action, no mutation, no API call
def test_np05_plan_is_pure():
    limiter = SdmRateLimiter(rng=random.Random(1))
    np, client, clock, _s = build(limiter=limiter, puller=FakePuller())
    np.step(clock.t)  # discover the fleet so plan() has camera candidates too
    clock.t = 1000.0

    before_health = json.dumps(np.health(), sort_keys=True, default=str)
    before_snapshot = json.dumps(limiter.snapshot(clock.t), sort_keys=True)
    calls_before = client.calls

    first = np.plan(clock.t)
    second = np.plan(clock.t)
    third = np.plan(clock.t)

    assert isinstance(first, PollAction)
    assert first == second == third
    assert client.calls == calls_before, "plan() must not perform an API call"
    assert json.dumps(limiter.snapshot(clock.t), sort_keys=True) == before_snapshot, (
        "plan() must not mutate the limiter (buckets are warmed at scheduling time)"
    )
    assert json.dumps(np.health(), sort_keys=True, default=str) == before_health

    # And it stays pure at a different instant, too.
    later = np.plan(clock.t + 500.0)
    assert later == np.plan(clock.t + 500.0)


# NP-06 step() executes AT MOST ONE API call — checked every single step
def test_np06_step_makes_at_most_one_call():
    limiter = SdmRateLimiter(rng=random.Random(2))
    np, client, clock, _s = build(per_camera_get=True, limiter=limiter, puller=FakePuller(load_envelopes(), repeat=True))
    seen_kinds: set[str] = set()
    for _ in range(400):
        before = client.calls
        result = np.step(clock.t)
        assert client.calls - before <= 1, "a step must never make two API calls"
        assert result["calls"] in (0, 1)
        if result["reason"] == "done":
            seen_kinds.add(result["kind"])
        # advance the simulated clock the way run_forever would
        action = np.plan(clock.t)
        clock.t = max(clock.t, action.at) if action else clock.t + 1.0
    assert seen_kinds == {"events", "list", "get"}, seen_kinds


# NP-07 a backlog cannot become a burst: a huge time jump still yields one call per step
def test_np07_backlog_does_not_burst():
    limiter = SdmRateLimiter(rng=random.Random(3))
    np, client, clock, _s = build(limiter=limiter)
    np.step(0.0)
    clock.t = 100_000.0  # a whole day of "missed" cadences at once
    for _ in range(20):
        before = client.calls
        np.step(clock.t)  # same instant, over and over
        assert client.calls - before <= 1
    # The limiter, not the backlog, decides how many actually went through.
    assert max_calls_in_window(client.times(constants.METHOD_DEVICES_GET), 60.0) <= DOC_GET_QPM


# --------------------------------------------------------------------------- #
# (2) SIMULATION + (3) RECOMPUTATION
# --------------------------------------------------------------------------- #


def simulate(hours: float = 2.5, *, seed: int = 85, **kwargs: Any):
    """Drive ``run_forever`` over a simulated clock until ``hours`` have elapsed."""
    limiter = SdmRateLimiter(rng=random.Random(seed))
    clock = FakeClock()
    client = FakeClient(limiter=limiter)
    puller = FakePuller(load_envelopes(), repeat=True)
    np, _c, _k, sink = build(
        client=client, limiter=limiter, clock=clock, puller=puller, **kwargs
    )
    horizon = float(hours) * 3600.0
    summary = np.run_forever(
        sleep=clock.sleep, max_steps=100_000, stop=lambda: clock.t >= horizon
    )
    return np, client, clock, sink, summary, limiter


# NP-08 over a long run the emitted call log never violates the documented quotas
def test_np08_long_run_never_exceeds_documented_quotas():
    np, client, clock, _sink, summary, _lim = simulate(hours=2.5, per_camera_get=True)
    assert clock.t >= 2.5 * 3600.0
    assert client.calls > 100, "the run must actually be continuous, not idle"

    list_times = client.times(constants.METHOD_DEVICES_LIST)
    get_times = client.times(constants.METHOD_DEVICES_GET)
    assert list_times and get_times

    # Per method, project-wide.
    assert max_calls_in_window(list_times, 60.0) <= DOC_LIST_QPM
    assert max_calls_in_window(get_times, 60.0) <= DOC_GET_QPM

    # Per device instance: 30 QPM **or 100 QPH**.
    for device_id in CAMERA_IDS:
        per_device = client.times(constants.METHOD_DEVICES_GET, device_id)
        assert per_device, f"{device_id} was never polled"
        assert max_calls_in_window(per_device, 60.0) <= DOC_CAMERA_QPM
        assert max_calls_in_window(per_device, 3600.0) <= DOC_CAMERA_QPH


# NP-09 continuous, not bursty: every stream keeps running for the whole horizon
def test_np09_run_is_continuous_not_bursty():
    _np, client, clock, _sink, _summary, _lim = simulate(hours=2.5, per_camera_get=True)
    horizon = clock.t
    for times in (
        client.times(constants.METHOD_DEVICES_LIST),
        client.times(constants.METHOD_DEVICES_GET),
    ):
        # first call early, last call late, and no silent hour in between
        assert min(times) < 0.05 * horizon
        assert max(times) > 0.90 * horizon
        assert max(b - a for a, b in zip(sorted(times), sorted(times)[1:])) < 600.0

    # No two devices.get closer than the project-wide floor for that method.
    assert min_gap(client.times(constants.METHOD_DEVICES_GET)) >= (
        constants.method_min_interval_s(constants.METHOD_DEVICES_GET) - 1e-9
    )
    # And no two polls of the SAME camera closer than its sustained floor.
    for device_id in CAMERA_IDS:
        assert min_gap(client.times(constants.METHOD_DEVICES_GET, device_id)) >= (
            constants.DEFAULT_CAMERA_CADENCE_S - 1e-9
        )


# NP-10 the stagger really separates N cameras (they never come due together)
def test_np10_cameras_are_phase_staggered():
    np, client, clock, _s = build(per_camera_get=True, )
    np.step(0.0)  # devices.list discovers three cameras at the same instant
    scheduled = sorted(np._next_device_at.values())  # noqa: SLF001 - white-box on purpose
    assert len(scheduled) == len(CAMERA_IDS)

    cadence = np.effective_camera_cadence_s()
    ideal_spacing = cadence / len(CAMERA_IDS)
    # Phase i*cadence/N, jittered by at most ±jitter_frac of the phase itself, so the
    # worst case still leaves a clear gap between neighbours.
    assert min_gap(scheduled) > ideal_spacing * 0.5
    assert max(scheduled) - min(scheduled) > ideal_spacing

    # Without the stagger all three would be due at exactly the same instant.
    assert len(set(scheduled)) == len(CAMERA_IDS)


# NP-11 with jitter disabled the stagger alone is exactly i*cadence/N
def test_np11_stagger_geometry_without_jitter():
    np, _c, _k, _s = build(jitter_frac=0.0)
    np.step(0.0)
    scheduled = sorted(np._next_device_at.values())  # noqa: SLF001
    cadence = np.effective_camera_cadence_s()
    n = len(CAMERA_IDS)
    assert scheduled == pytest.approx([i * cadence / n for i in range(n)])


# --------------------------------------------------------------------------- #
# Throttling, errors, and the loop
# --------------------------------------------------------------------------- #


# NP-12 SdmThrottled reschedules to retry_at and is NOT counted as an error
def test_np12_throttled_reschedules_without_an_error():
    class AlwaysThrottled(FakeClient):
        def list_devices(self, *, now: float | None = None):
            raise SdmThrottled("not yet", retry_at=float(now or 0.0) + 7.0,
                               method=constants.METHOD_DEVICES_LIST)

    np, client, clock, _s = build(client=AlwaysThrottled())
    result = np.step(0.0)

    assert result["throttled"] is True
    assert result["reason"] == "throttled"
    assert result["error"] is None
    assert result["retryAt"] == pytest.approx(7.0)
    assert client.calls == 0

    health = np.health()
    assert health["errors"] == 0
    assert health["consecutiveErrors"] == 0
    assert health["throttled"] == 1

    # Rescheduled, not retried immediately.
    action = np.plan(0.0)
    assert action.kind == "list"
    assert action.at == pytest.approx(7.0)

    # And a throttle never appears as a failure in the run summary either.
    summary = np.run_forever(sleep=clock.sleep, max_steps=5)
    assert summary["errors"] == 0
    assert summary["throttled"] >= 1


# NP-13 a real failure DOES count, backs off, and recovery resets the counter
def test_np13_errors_are_counted_and_recover():
    np, client, clock, _s = build(client=FakeClient(fail_times=2))
    first = np.step(0.0)
    assert first["ok"] is False
    assert first["reason"] == "error"
    assert np.health()["consecutiveErrors"] == 1

    clock.t = first["retryAt"]
    second = np.step(clock.t)
    assert second["ok"] is False
    assert np.health()["consecutiveErrors"] == 2
    # Backoff is bounded, not unbounded.
    assert second["retryAt"] - clock.t <= constants.DEFAULT_LIST_CADENCE_S * 8.0

    clock.t = second["retryAt"]
    third = np.step(clock.t)
    assert third["ok"] is True
    assert np.health()["consecutiveErrors"] == 0
    assert np.health()["errors"] == 2


# NP-14 run_forever terminates under max_steps and only ever sleeps a non-negative time
def test_np14_run_forever_terminates_and_sleeps_non_negatively():
    limiter = SdmRateLimiter(rng=random.Random(4))
    np, client, clock, _s = build(limiter=limiter, puller=FakePuller(load_envelopes(), repeat=True))
    summary = np.run_forever(sleep=clock.sleep, max_steps=50)

    assert summary["steps"] == 50
    assert summary["stopped"] == "max_steps"
    assert clock.slept, "a continuous poller must actually wait between calls"
    assert all(d >= 0.0 for d in clock.slept), "sleep() must never get a negative duration"
    assert client.calls <= 50
    assert summary["calls"] == client.calls


# NP-15 stop() ends the loop early
def test_np15_run_forever_honours_stop():
    np, _c, clock, _s = build()
    calls = {"n": 0}

    def stop() -> bool:
        calls["n"] += 1
        return calls["n"] > 3

    summary = np.run_forever(sleep=clock.sleep, max_steps=1000, stop=stop)
    assert summary["stopped"] == "stop"
    assert summary["steps"] == 3


# --------------------------------------------------------------------------- #
# Events path
# --------------------------------------------------------------------------- #


# NP-16 an acoustic event reaches the existing burst wire, deduped and acknowledged
def test_np16_acoustic_event_reaches_the_burst_wire():
    envelopes = [json.loads((FIXTURES / "camera_sound.json").read_text(encoding="utf-8"))]
    puller = FakePuller(envelopes)
    np, _c, clock, sink = build(puller=puller)

    result = np.step(0.0)
    assert result["kind"] == "events"
    assert result["events"] == 1
    assert puller.acked == ["ack-0"]

    row = [r for r in sink.rows if r.get("nestSource") == mapping.SOURCE_EVENT][0]
    assert row["schemaVersion"] == 1
    assert row["deviceId"] == NODE
    assert row["event"] == "soundBurst"
    assert row["soundBurst"] is True
    assert row["vibClass"] == "acoustic"
    assert row["nestEvent"] == "sound"

    # Re-delivery of the same eventSessionId is suppressed, not re-ingested.
    puller.queue = [("ack-dup", events.parse_event(envelopes[0]))]
    np._next_events_at = 0.0  # noqa: SLF001 - make it due again at the same instant
    again = np.step(0.0)
    assert again["events"] == 0
    assert puller.acked == ["ack-0", "ack-dup"], "a duplicate must still be acknowledged"


# NP-17 a poll heartbeat carries connectivity, and devices.list only re-emits on change
def test_np17_poll_heartbeat_and_connectivity_reconciliation():
    client = FakeClient(connectivity={CAMERA_IDS[0]: "OFFLINE"})
    np, _c, clock, sink = build(client=client)

    np.step(0.0)  # first devices.list: every device is new -> one heartbeat each
    assert len(sink.rows) == len(CAMERA_IDS)
    offline = [r for r in sink.rows if r.get("nestConnectivity") == "OFFLINE"]
    assert len(offline) == 1
    assert offline[0]["nestSource"] == mapping.SOURCE_POLL
    assert offline[0]["nestDeviceRef"] == mapping.device_ref(CAMERA_IDS[0])
    assert offline[0]["nestDeviceType"] == constants.TYPE_CAMERA

    # Second list, nothing changed -> no new heartbeats (a list must not fan out).
    clock.t = 100.0
    np._next_list_at = clock.t  # noqa: SLF001
    np._next_device_at = {}  # noqa: SLF001 - isolate the list action
    before = len(sink.rows)
    np.step(clock.t)
    assert len(sink.rows) == before

    # Connectivity flips -> exactly one reconciliation heartbeat.
    client._connectivity[CAMERA_IDS[0]] = "ONLINE"  # noqa: SLF001
    clock.t = 200.0
    np._next_list_at = clock.t  # noqa: SLF001
    np.step(clock.t)
    assert len(sink.rows) == before + 1
    assert sink.rows[-1]["nestConnectivity"] == "ONLINE"


# --------------------------------------------------------------------------- #
# NEGATIVE CONTROLS
# --------------------------------------------------------------------------- #

BAD_PATHS = (
    "meta/patches/node1.json",
    "meta/patches",
    "meta/patches/../telemetry/node1/x.json",
    "/meta/telemetry/node1/x.json",
    "meta\\telemetry\\node1\\x.json",
    "meta//telemetry/x.json",
    "meta/./telemetry/x.json",
    "meta/../../etc/passwd",
)


# NP-18 the patch-path guard refuses, and the bare-env twin refuses identically
@pytest.mark.parametrize("bad", BAD_PATHS)
def test_np18_patch_path_guard_refuses(bad):
    with pytest.raises(PatchWriteRefused):
        poller.assert_not_patch_path(bad)
    with pytest.raises(PatchWriteRefused):
        poller._fallback_assert_not_patch_path(bad)  # noqa: SLF001


def test_np18_guard_delegates_to_features_live():
    """The delegated guard is really ``features_live``'s, not a private copy."""
    from iot_asp_autoroute import features_live

    seen: list[str] = []

    def spy(name: str) -> None:
        seen.append(name)

    original = features_live.assert_not_patch_path
    features_live.assert_not_patch_path = spy  # type: ignore[assignment]
    try:
        poller.assert_not_patch_path("meta/telemetry/node1/x.json")
    finally:
        features_live.assert_not_patch_path = original  # type: ignore[assignment]
    assert seen == ["meta/telemetry/node1/x.json"]

    # Good names pass on both paths.
    poller.assert_not_patch_path("meta/telemetry/node1/x.json")
    poller._fallback_assert_not_patch_path("meta/telemetry/node1/x.json")  # noqa: SLF001


# NP-19 object-name builders are guarded and only ever produce allowed prefixes
def test_np19_object_names_are_guarded():
    name = poller.telemetry_object_name(NODE, "2026-01-01T00:00:00Z")
    assert name == "meta/telemetry/node1/2026-01-01T00-00-00Z.json"
    state = poller.nest_state_object_name(mapping.device_ref(CAMERA_IDS[0]))
    assert state.startswith(constants.GCS_NEST_STATE_PREFIX + "/")
    assert CAMERA_IDS[0] not in state

    for bad_node in ("../patches", "meta/patches", "", "a/b", "node 1", "node1\n", None):
        with pytest.raises(ValueError):
            poller.telemetry_object_name(bad_node, "2026-01-01T00:00:00Z")
    for bad_ts in ("", "../../patches/x", "a/b"):
        with pytest.raises(ValueError):
            poller.telemetry_object_name(NODE, bad_ts)
    with pytest.raises(ValueError):
        poller.nest_state_object_name("")
    # A hostile node id is refused at construction, before any API call happens.
    with pytest.raises(ValueError):
        NestPoller(FakeClient(), node_id="../patches")


def test_np19_node_rule_matches_features_live():
    """The copied regex must stay identical to the repo's single definition."""
    from iot_asp_autoroute import features_live

    assert poller.NODE_RE.pattern == features_live.NODE_RE.pattern
    for good in ("node1", "NODE-2", "a_b"):
        assert poller.validate_node(good) == good == features_live.validate_node(good)


# NP-20 a payload carrying a patch or control key is refused before the sink sees it
@pytest.mark.parametrize(
    "extra",
    [
        {"vol": 100},
        {"algo": "hop"},
        {"fMin": 17000},
        {"holdManual": True},
        {"suddenFreq": True},
        {"seedAction": "reseed"},
        {"priors": ["x"]},
    ],
)
def test_np20_patch_field_on_the_wire_is_refused(extra):
    payload = {"schemaVersion": 1, "deviceId": NODE, "ts": "2026-01-01T00:00:00Z"}
    payload.update(extra)
    with pytest.raises(PatchWriteRefused):
        poller.assert_telemetry_only(payload)


def test_np20_guard_runs_before_the_sink():
    """A hostile mapper output never reaches the sink at all."""
    np, _c, _k, sink = build()
    with pytest.raises(PatchWriteRefused):
        np._emit({"deviceId": NODE, "ts": "2026-01-01T00:00:00Z", "vol": 100})  # noqa: SLF001
    assert sink.rows == []


# NP-21 nothing the poller emits is ever a patch field, over a whole simulated run
def test_np21_no_emitted_row_is_ever_patch_shaped():
    _np, _client, _clock, sink, summary, _lim = simulate(hours=1.0)
    assert sink.rows
    assert summary["telemetry"] == len(sink.rows)
    for row in sink.rows:
        assert row["schemaVersion"] == 1
        assert row["deviceId"] == NODE
        assert not (set(row) & mapping.FORBIDDEN_KEYS), row
        assert "previewUrl" not in json.dumps(row), "a recording URI reached the wire"


# NP-22 HOLD / MANUAL: observation continues, authorship never starts
def test_np22_hold_manual_keeps_observing_and_writes_no_patch(dry_root):
    limiter = SdmRateLimiter(rng=random.Random(5))
    clock = FakeClock()
    client = FakeClient(limiter=limiter)
    np, _c, _k, sink = build(
        client=client,
        limiter=limiter,
        clock=clock,
        puller=FakePuller(load_envelopes(), repeat=True),
        hold_manual=True,
        write_state=True,  # exercise the only direct-write path there is
    )
    summary = np.run_forever(sleep=clock.sleep, max_steps=200)

    # Reads are safe and read-only, so observation is NOT suspended under Hold.
    assert summary["calls"] > 0
    assert summary["telemetry"] > 0
    assert np.health()["holdManual"] is True

    # ... and absolutely nothing was authored.
    assert not (dry_root / "meta" / "patches").exists()
    assert list(dry_root.rglob("*.json")), "the run must have written something"
    for path in dry_root.rglob("*.json"):
        rel = str(path.relative_to(dry_root))
        assert not rel.startswith("meta/patches"), rel
    for row in sink.rows:
        assert "holdManual" not in row, "a Nest observation may not assert or clear Hold"

    # Hold can be toggled at runtime and still never gates observation.
    np.set_hold_manual(False)
    assert np.health()["holdManual"] is False


# NP-23 the state tree is private-but-safe: no raw id, no trait values
def test_np23_state_record_is_written_without_a_raw_device_id(dry_root):
    np, _c, clock, _s = build(write_state=True)
    np.step(0.0)
    written = sorted((dry_root / "meta" / "nest" / "state").glob("*.json"))
    assert len(written) == len(CAMERA_IDS)
    for path in written:
        body = json.loads(path.read_text(encoding="utf-8"))
        assert body["nestDeviceRef"] == path.stem
        text = json.dumps(body)
        for device_id in CAMERA_IDS:
            assert device_id not in text
        assert "enterprises/" not in text


# NP-24 PII: no raw SDM device id in a step result or in health()
def test_np24_no_raw_device_id_escapes():
    limiter = SdmRateLimiter(rng=random.Random(6))
    np, _c, clock, _s = build(per_camera_get=True, limiter=limiter, puller=FakePuller(load_envelopes()))
    results = []
    for _ in range(60):
        results.append(np.step(clock.t))
        action = np.plan(clock.t)
        clock.t = max(clock.t, action.at) if action else clock.t + 1.0

    blob = json.dumps({"results": results, "health": np.health()}, default=str)
    for device_id in CAMERA_IDS:
        assert device_id not in blob, f"raw SDM device id {device_id!r} escaped"
    assert "enterprises/" not in blob
    refs = {r["deviceRef"] for r in results if r.get("deviceRef")}
    assert refs, "the run must have planned at least one per-device action"
    assert refs <= {mapping.device_ref(d) for d in CAMERA_IDS}


# --------------------------------------------------------------------------- #
# Health, hygiene, and the dry-run script
# --------------------------------------------------------------------------- #


# NP-25 health() reports everything the ADK tool and the PWA surface need
def test_np25_health_shape():
    limiter = SdmRateLimiter(rng=random.Random(7))
    np, _c, clock, _s = build(limiter=limiter, puller=FakePuller(load_envelopes()))
    np.run_forever(sleep=clock.sleep, max_steps=30)
    health = np.health()
    for key in (
        "nodeId", "holdManual", "listCadenceS", "cameraCadenceS",
        "effectiveCameraCadenceS", "eventsCadenceS", "consecutiveErrors",
        "lastEventAgeS", "limiter", "nextAction", "writesPatches",
    ):
        assert key in health, key
    assert health["nodeId"] == NODE
    assert health["limiter"] is not None and "buckets" in health["limiter"]
    assert health["lastEventAgeS"] is not None and health["lastEventAgeS"] >= 0.0
    assert health["nextAction"]["inS"] >= 0.0
    assert json.dumps(health, default=str)  # health must always be serialisable


# NP-26 effective camera cadence respects the project-wide devices.get budget too
def test_np26_effective_cadence_widens_for_a_large_fleet():
    np, _c, _k, _s = build(client=FakeClient([f"device-id-{i}" for i in range(10)]))
    np.step(0.0)
    floor = constants.method_min_interval_s(constants.METHOD_DEVICES_GET)
    assert np.effective_camera_cadence_s() == pytest.approx(10 * floor)
    assert np.effective_camera_cadence_s() > constants.DEFAULT_CAMERA_CADENCE_S
    # constants.max_cameras_at_cadence is the same fact read the other way round.
    assert constants.max_cameras_at_cadence(constants.DEFAULT_CAMERA_CADENCE_S) == 6


# NP-27 the module imports with stdlib only and never sleeps outside run_forever
def test_np27_module_is_stdlib_only_and_sleeps_only_in_run_forever():
    src = POLLER_SRC.read_text(encoding="utf-8")
    for banned in ("import numpy", "import scipy", "from google", "import google", "import requests"):
        assert banned not in src, banned
    # features_live (numpy/scipy) and tools must be imported lazily, inside a function.
    for line in src.splitlines():
        if line.startswith(("import ", "from ")):
            assert "features_live" not in line and "tools" not in line, line
    # `sleep` is a parameter of run_forever, never called on the time module directly.
    assert "time.sleep(" not in src


# NP-28 scripts/nest_dev.sh runs offline, with no credentials, and prints OK nest_dev
def test_np28_nest_dev_script_runs_offline(tmp_path):
    env = {
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "HOME": str(tmp_path),
        "IOT_ASP_AUTOROUTE_DRY_ROOT": str(tmp_path / "dry"),
        "IOT_ASP_AUTOROUTE_DRY_RUN": "1",
    }
    proc = subprocess.run(
        ["bash", str(NEST_DEV_SH)], capture_output=True, text=True, env=env, timeout=180
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK nest_dev" in proc.stdout
    assert "FAIL" not in proc.stdout
    # It wrote telemetry into the isolated mirror and touched no patch tree.
    assert list((tmp_path / "dry" / "meta" / "telemetry").rglob("*.json"))
    assert not (tmp_path / "dry" / "meta" / "patches").exists()


# NP-21 regression: FORBIDDEN_KEYS is live, despite a static analyser saying otherwise
def test_np21_forbidden_keys_is_used_not_dead_code():
    """`mapping.FORBIDDEN_KEYS` looks unused *within mapping.py* and is not.

    A code-quality bot on PR #107 reported "Unused global variable: 'FORBIDDEN_KEYS'"
    against mapping.py:76. It only analysed that module in isolation and missed the
    cross-module use in `poller.assert_telemetry_only`. Acting on that report would have
    deleted the constant and silently disabled the guard that stops a patch or control
    key reaching the telemetry wire — a safety regression that no other test would catch,
    because the guard would still *exist* and just never match anything.

    This test pins the relationship so the next cleanup has to confront it.
    """
    from iot_asp_autoroute.nest import mapping as _mapping

    assert _mapping.FORBIDDEN_KEYS, "FORBIDDEN_KEYS must not be emptied"
    # The guard must actually consult it: emptying the set must make the guard permissive.
    real = _mapping.FORBIDDEN_KEYS
    try:
        _mapping.FORBIDDEN_KEYS = frozenset()
        poller.assert_telemetry_only({"deviceId": NODE, "vol": 100})  # now permitted
    finally:
        _mapping.FORBIDDEN_KEYS = real
    # ...and restoring it must make the guard refuse again.
    with pytest.raises(PatchWriteRefused):
        poller.assert_telemetry_only({"deviceId": NODE, "vol": 100})
    # Every patch-authoring key the wire contract defines is covered.
    for key in ("vol", "algo", "fMin", "fMax", "pulseMs", "shriekMs", "vibThreshold",
                "seedAction", "priors", "holdManual", "suddenFreq"):
        assert key in real, f"{key} must stay in FORBIDDEN_KEYS"


# NP-25 the default schedule reserves the per-camera budget for commands
def test_np25_default_reserves_command_headroom():
    """A camera's instance budget is shared between devices.get and executeCommand.

    The bucket's pacing floor is the documented 100 QPH camera cap = 36.0 s, while an
    event image must be fetched inside constants.EVENT_IMAGE_TTL_S = 30.0 s. So one
    liveness `get` blocks a CameraEventImage.GenerateImage for LONGER than the image
    exists. Spending the budget on liveness therefore breaks the reactive path that is
    the whole point of #103 — and it buys nothing, because devices.list runs 3x more
    often and already carries connectivity.

    Default must be: no per-camera gets, budget reserved for commands.
    """
    np, _c, _k, _s = build()
    assert np.health()["perCameraGet"] is False
    assert np.health()["commandHeadroomReserved"] is True
    # the arithmetic that makes this necessary, from the frozen constants
    assert constants.DEFAULT_CAMERA_CADENCE_S == 36.0
    assert constants.EVENT_IMAGE_TTL_S == 30.0
    assert constants.DEFAULT_CAMERA_CADENCE_S > constants.EVENT_IMAGE_TTL_S, (
        "if this ever inverts, per-camera polling stops being self-defeating"
    )
    # opt-in still works for callers that want liveness polling
    np2, _c2, _k2, _s2 = build(per_camera_get=True)
    assert np2.health()["perCameraGet"] is True
