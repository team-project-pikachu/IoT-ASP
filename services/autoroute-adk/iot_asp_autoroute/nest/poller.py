"""Continuous Nest observation scheduler — a burst is impossible by construction (#85, #3).

Issue #85 asks for *continuous* observation of the Nest fleet, explicitly **not** bursts.
This module is the scheduler that makes that structural rather than aspirational:

* :meth:`NestPoller.plan` is a **pure** function of ``now`` and the poller's state. It
  returns at most **one** due action, mutates nothing, and calling it twice with the same
  ``now`` returns the same action.
* :meth:`NestPoller.step` executes **at most one SDM API call**. There is no loop inside a
  step, so no amount of backlog can turn into a burst — a backlog just means the next
  ``plan()`` is due immediately, one call at a time.
* :meth:`NestPoller.run_forever` sleeps until ``plan().at`` through an **injected** sleep
  callable. It is the only place in the package that sleeps.
* Per-camera polls are phase-staggered by device index and jittered, so N cameras never
  align into a simultaneous volley.
* A cadence **faster** than the documented floor raises :class:`ValueError` — the floors
  come from :mod:`iot_asp_autoroute.nest.constants`, which derives them from the published
  quotas, and are never restated here.

Hybrid transport, and why
-------------------------
The SDM rate-limits page enumerates exactly which calls are metered:
``devices.list`` (5 QPM), ``devices.get`` (10 QPM), ``devices.executeCommand`` (10 QPM),
the ``structures.*`` / ``structures.rooms.*`` methods (5 QPM), plus per-device-instance
caps of 30 QPM **or 100 QPH** for ``CAMERA`` / ``DOORBELL``
(https://developers.google.com/nest/device-access/project/limits). 100 QPH is the cap that
bites a continuous observer: 3600/100 = 36 s sustained per camera. So polling can only ever
be the *slow* signal.

The fast signal is Pub/Sub. Device events are delivered to a Cloud Pub/Sub topic
(https://developers.google.com/nest/device-access/subscribe-to-events,
https://developers.google.com/nest/device-access/api/events); a ``:pull`` is a call to
``pubsub.googleapis.com``, which is not one of the SDM methods the limits page meters.
UNVERIFIED: no Google page states in so many words that Pub/Sub delivery is exempt from SDM
quota — the exemption here is inferred from the limits page enumerating only SDM methods.
The design therefore never *depends* on that inference: the event path is scheduled on its
own cadence and, if it were metered tomorrow, the SDM limiter would still gate every
``devices.*`` call independently.

Division of labour, then: **events carry reaction** (a ``CameraSound.Sound`` reaches the
existing burst path within one ``events_cadence_s``), **polling carries liveness** —
connectivity reconciliation and proof the fleet is still answering — at the 36 s floor.

Hard guards
-----------
* The poller **never writes** ``meta/patches/``. Every write path goes through
  :func:`assert_not_patch_path`, which delegates to
  ``iot_asp_autoroute.features_live.assert_not_patch_path`` (lazily, because that module
  pulls numpy/scipy through ``colab_etl``) and falls back to a byte-identical stdlib
  re-implementation in a bare environment.
* Every payload handed to the sink passes :func:`assert_telemetry_only`, which refuses
  ``mapping.FORBIDDEN_KEYS`` — the patch fields plus ``holdManual`` / ``suddenFreq``.
* Under ``holdManual`` the poller keeps **observing** (SDM reads and Pub/Sub pulls are
  read-only and safe) but still authors nothing: patch authorship lives in
  ``sudden_freq`` / ``tools.write_patch``, which already refuse under Hold.
* No raw SDM device id leaves this module: step results and :meth:`health` report
  ``mapping.device_ref`` hashes (CLAUDE.md #7).

stdlib only at import time. ``tools`` (numpy/scipy) and ``google-*`` are lazy.
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from .. import gcs_io
from . import constants, mapping
from .events import EventDeduper
from .sdm_client import SdmThrottled

__all__ = [
    "ACTION_EVENTS",
    "ACTION_GET",
    "ACTION_LIST",
    "MIN_EVENTS_CADENCE_S",
    "NestPoller",
    "PatchWriteRefused",
    "PollAction",
    "TELEMETRY_PREFIX",
    "assert_not_patch_path",
    "assert_telemetry_only",
    "nest_state_object_name",
    "telemetry_object_name",
]

# ── action kinds ─────────────────────────────────────────────────────────────

ACTION_LIST: str = "list"
ACTION_GET: str = "get"
ACTION_EVENTS: str = "events"

#: Deterministic tie-break when two actions are due at the same instant: drain the
#: (unmetered) event backlog first, then reconcile the fleet, then poll instances.
_KIND_PRIORITY: dict[str, int] = {ACTION_EVENTS: 0, ACTION_LIST: 1, ACTION_GET: 2}

#: Local guard only — Pub/Sub pull is not an SDM method and the limits page sets no floor
#: for it. One second simply keeps ``run_forever`` from becoming a spin loop.
MIN_EVENTS_CADENCE_S: float = 1.0

#: Cadence comparisons are float arithmetic on derived values (3600/100 = 36.0); a caller
#: passing exactly the floor must be accepted.
_CADENCE_EPS: float = 1e-9

#: Consecutive-failure reschedule multiplier ceiling, so a persistent outage backs off but
#: never parks the poller for longer than a few cadences.
_ERROR_BACKOFF_MAX_MULT: float = 8.0

#: Pub/Sub ``maxMessages`` per pull. One pull is one round trip regardless.
DEFAULT_MAX_MESSAGES: int = 10

TELEMETRY_PREFIX: str = "meta/telemetry/"
FORBIDDEN_PREFIX: str = "meta/patches"


# ── write guards ─────────────────────────────────────────────────────────────


class PatchWriteRefused(ValueError):
    """A Nest write path tried to touch ``meta/patches`` or carry a patch field.

    A ``ValueError`` subclass so existing ``except ValueError`` callers keep working,
    but distinct so :meth:`NestPoller.step` can re-raise it instead of folding a
    programming error into the ordinary per-cycle error counter. Invariant #2 of
    NEST_DESIGN.md and CLAUDE.md #6 are not "retry next cycle" conditions.
    """


def _fallback_assert_not_patch_path(object_name: str) -> None:
    """Stdlib twin of ``features_live.assert_not_patch_path`` (same refusals).

    Used only when ``features_live`` cannot be imported (it reaches numpy/scipy through
    ``colab_etl``). ``tests/test_nest_poller.py`` asserts the two agree on every case.
    """
    s = str(object_name)
    parts = s.split("/")
    if s.startswith("/") or "\\" in s or any(seg in ("", ".", "..") for seg in parts):
        raise PatchWriteRefused(
            f"refuse: unsafe object name {s!r} (absolute, '\\', empty, '.' or '..' segment)"
        )
    if s.startswith(FORBIDDEN_PREFIX):
        raise PatchWriteRefused("refuse: nest.poller never writes meta/patches")


def assert_not_patch_path(object_name: str) -> None:
    """Refuse ``meta/patches`` and path-unsafe object names before any write.

    Delegates to ``iot_asp_autoroute.features_live.assert_not_patch_path`` — the repo's
    single implementation of this guard — importing it lazily so this module stays
    stdlib-only at import time. Falls back to :func:`_fallback_assert_not_patch_path`
    when numpy/scipy are absent.
    """
    try:
        from ..features_live import assert_not_patch_path as _guard  # noqa: PLC0415
    except Exception:  # noqa: BLE001 - bare env: numpy/scipy missing
        _fallback_assert_not_patch_path(object_name)
        return
    try:
        _guard(object_name)
    except ValueError as exc:  # re-typed, message preserved verbatim
        raise PatchWriteRefused(str(exc)) from None


def assert_telemetry_only(payload: Mapping[str, Any]) -> None:
    """Refuse a payload carrying any patch-authoring or control key.

    ``mapping.FORBIDDEN_KEYS`` is the shared list (patch fields plus ``holdManual`` /
    ``suddenFreq`` / ``algo``). A Nest observation is evidence, never a decision: it may
    not smuggle a patch field into the ingest path, and it may not assert or clear Hold.
    """
    if not isinstance(payload, Mapping):
        raise PatchWriteRefused("refuse: telemetry payload must be a mapping")
    bad = sorted(k for k in payload if k in mapping.FORBIDDEN_KEYS)
    if bad:
        raise PatchWriteRefused(
            f"refuse: nest.poller emits telemetry only, never patch/control keys {bad}"
        )


def telemetry_object_name(node_id: str, ts: str) -> str:
    """``meta/telemetry/<node>/<ts with ':'→'-'>.json``, guarded before it is returned."""
    node = str(node_id).strip()
    stamp = str(ts).strip().replace(":", "-")
    if not node or not stamp:
        raise ValueError("refuse: node_id and ts are required to build an object name")
    name = f"{TELEMETRY_PREFIX}{node}/{stamp}.json"
    assert_not_patch_path(name)
    return name


def nest_state_object_name(device_ref: str) -> str:
    """``meta/nest/state/<ref>.json`` (private tree), guarded before it is returned.

    ``device_ref`` is the truncated ``mapping.device_ref`` hash, never a raw SDM id.
    """
    ref = str(device_ref).strip()
    if not ref:
        raise ValueError("refuse: device_ref is required to build a state object name")
    name = f"{constants.GCS_NEST_STATE_PREFIX}/{ref}.json"
    assert_not_patch_path(name)
    return name


# ── the planned action ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class PollAction:
    """One due action. ``kind`` is ``"list"`` | ``"get"`` | ``"events"``.

    ``at`` is the absolute time on the injected clock at which the action may run: the
    later of its scheduled slot and, when a limiter was supplied, the earliest instant
    that call shape has quota. ``device_id`` is the raw SDM id (in memory only — it is
    hashed before it reaches any result dict, log or health surface).
    """

    at: float
    kind: str
    device_id: str | None
    reason: str


# ── the poller ───────────────────────────────────────────────────────────────


class NestPoller:
    """Continuous, quota-paced observation of one Nest fleet bound to one ASP node.

    ``client`` is duck-typed against
    :class:`~iot_asp_autoroute.nest.sdm_client.SdmClient` (``list_devices``,
    ``get_device``, optionally ``status``). ``puller`` is duck-typed against
    :class:`~iot_asp_autoroute.nest.events.PubSubPuller` (``pull``, ``acknowledge``,
    optionally ``status``); omit it and the poller runs poll-only.

    ``limiter`` should be the **same** limiter the client was built with. It is used only
    for *planning* (``next_allowed_at`` is side-effect free), so ``plan()`` can hand
    ``run_forever`` a sleep target that already respects quota instead of waking up to be
    refused. Omit it and the client's ``SdmThrottled`` still reschedules correctly — one
    wasted wake-up, never a wasted API call.

    ``sink(telemetry) -> None`` receives every heartbeat; it defaults to
    ``tools.ingest_telemetry`` (lazy, guarded — ``tools`` pulls numpy/scipy) and falls
    back to a ``gcs_io`` write under ``meta/telemetry/``. Every payload is checked by
    :func:`assert_telemetry_only` and every derived object name by
    :func:`assert_not_patch_path` first.
    """

    def __init__(
        self,
        client: Any,
        *,
        node_id: str,
        puller: Any | None = None,
        sink: Callable[[dict[str, Any]], Any] | None = None,
        limiter: Any | None = None,
        list_cadence_s: float | None = None,
        camera_cadence_s: float | None = None,
        events_cadence_s: float = 10.0,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
        jitter_frac: float = 0.1,
        # ── additive beyond NEST_DESIGN.md, all optional ──
        hold_manual: bool = False,
        wall_clock: Callable[[], float] = time.time,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        write_state: bool = True,
        deduper: Any | None = None,
    ) -> None:
        node = str(node_id).strip() if node_id is not None else ""
        if not node:
            raise ValueError("node_id is required (the ASP node the Nest fleet is bound to)")
        if not (0.0 <= float(jitter_frac) < 1.0):
            raise ValueError(f"jitter_frac must be in [0, 1), got {jitter_frac!r}")

        self._client = client
        self._node_id = node
        self._puller = puller
        self._sink = sink
        self._limiter = limiter
        self._clock = clock
        self._wall_clock = wall_clock
        self._rng = rng if rng is not None else random.Random()
        self._jitter_frac = float(jitter_frac)
        self._max_messages = max(1, int(max_messages))
        self._write_state = bool(write_state)
        self._hold_manual = bool(hold_manual)

        self._list_cadence_s = _validate_cadence(
            list_cadence_s,
            constants.DEFAULT_LIST_CADENCE_S,
            "list_cadence_s",
            f"devices.list is {constants.METHOD_QUOTAS[constants.METHOD_DEVICES_LIST][0]} QPM",
        )
        self._camera_cadence_s = _validate_cadence(
            camera_cadence_s,
            constants.DEFAULT_CAMERA_CADENCE_S,
            "camera_cadence_s",
            "a camera instance is 30 QPM or 100 QPH, so 3600/100 s is the sustained floor",
        )
        self._events_cadence_s = _validate_cadence(
            events_cadence_s,
            MIN_EVENTS_CADENCE_S,
            "events_cadence_s",
            "local anti-spin guard; Pub/Sub pull is not an SDM method",
        )

        self._deduper = deduper if deduper is not None else EventDeduper()

        # ── schedule + fleet state ────────────────────────────────────────────
        start = float(self._clock())
        self._next_list_at: float = start
        self._next_events_at: float = start if puller is not None else math.inf
        self._next_device_at: dict[str, float] = {}
        self._devices: dict[str, Any] = {}
        self._device_order: list[str] = []
        self._connectivity: dict[str, str | None] = {}

        # ── counters (health) ─────────────────────────────────────────────────
        self._steps = 0
        self._calls = 0
        self._pulls = 0
        self._events_seen = 0
        self._telemetry = 0
        self._throttles = 0
        self._errors = 0
        self._consecutive_errors = 0
        self._last_event_at: float | None = None
        self._last_call_at: float | None = None
        self._last_error: str | None = None

        self._warm(constants.METHOD_DEVICES_LIST, None, None, start)

    # ── configuration ────────────────────────────────────────────────────────

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def hold_manual(self) -> bool:
        """Hold / Manual passthrough. Observation continues; authorship never starts."""
        return self._hold_manual

    def set_hold_manual(self, value: bool) -> None:
        """Record the fleet's Hold state so :meth:`health` can report it.

        Deliberately does **not** stop polling: SDM reads and Pub/Sub pulls are
        read-only, and Hold is a rule about *authoring patches* (CLAUDE.md #6), which
        this module never does under any state.
        """
        self._hold_manual = bool(value)

    def effective_camera_cadence_s(self, n_cameras: int | None = None) -> float:
        """Per-camera cadence actually scheduled, given how many cameras are known.

        The per-instance floor (36 s) is not the only constraint: ``devices.get`` is
        10 QPM **project-wide**, so N cameras need at least
        ``N × constants.method_min_interval_s("devices.get")`` seconds per camera to stay
        continuous. ``constants.max_cameras_at_cadence(36.0)`` == 6 is the same fact read
        the other way round.
        """
        n = len(self._device_order) if n_cameras is None else int(n_cameras)
        if n <= 0:
            return self._camera_cadence_s
        spread = n * constants.method_min_interval_s(constants.METHOD_DEVICES_GET)
        return max(self._camera_cadence_s, spread)

    # ── planning (PURE) ──────────────────────────────────────────────────────

    def plan(self, now: float) -> PollAction | None:
        """Next due action, or ``None`` when nothing is scheduled. **Pure.**

        Reads the clock nowhere, mutates nothing, and is safe to call repeatedly while
        deciding how long to sleep. The limiter is consulted only through
        ``next_allowed_at``, which is documented side-effect free, and every bucket it
        could create was already warmed at scheduling time.
        """
        now = float(now)
        candidates: list[tuple[float, int, int, PollAction]] = []

        if self._puller is not None and math.isfinite(self._next_events_at):
            candidates.append(
                (
                    self._next_events_at,
                    _KIND_PRIORITY[ACTION_EVENTS],
                    -1,
                    PollAction(
                        at=self._next_events_at,
                        kind=ACTION_EVENTS,
                        device_id=None,
                        reason="pubsub pull (unmetered by the SDM limits page)",
                    ),
                )
            )

        list_at = self._planned_at(
            constants.METHOD_DEVICES_LIST, self._next_list_at, None, None, now
        )
        candidates.append(
            (
                list_at,
                _KIND_PRIORITY[ACTION_LIST],
                -1,
                PollAction(
                    at=list_at,
                    kind=ACTION_LIST,
                    device_id=None,
                    reason="fleet reconciliation at the devices.list floor",
                ),
            )
        )

        for index, device_id in enumerate(self._device_order):
            scheduled = self._next_device_at.get(device_id)
            if scheduled is None:
                continue
            device_type = _device_type(self._devices.get(device_id))
            at = self._planned_at(
                constants.METHOD_DEVICES_GET, scheduled, device_id, device_type, now
            )
            candidates.append(
                (
                    at,
                    _KIND_PRIORITY[ACTION_GET],
                    index,
                    PollAction(
                        at=at,
                        kind=ACTION_GET,
                        device_id=device_id,
                        reason="instance liveness at the per-camera hourly floor",
                    ),
                )
            )

        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        return candidates[0][3]

    def _planned_at(
        self,
        method: str,
        scheduled: float,
        device_id: str | None,
        device_type: str | None,
        now: float,
    ) -> float:
        """``max(scheduled slot, earliest instant the limiter allows this shape)``."""
        if self._limiter is None:
            return float(scheduled)
        try:
            allowed = float(
                self._limiter.next_allowed_at(
                    method, device_id=device_id, device_type=device_type, now=now
                )
            )
        except Exception:  # noqa: BLE001 - planning must never raise
            return float(scheduled)
        return max(float(scheduled), allowed)

    def _warm(
        self, method: str, device_id: str | None, device_type: str | None, now: float
    ) -> None:
        """Materialise a limiter bucket at *scheduling* time, so ``plan`` stays pure.

        ``SdmRateLimiter`` creates a bucket lazily on first query; doing that from
        ``plan()`` would be a (harmless but real) mutation. Warming here keeps the
        purity property exact rather than approximate.
        """
        if self._limiter is None:
            return
        try:
            self._limiter.next_allowed_at(
                method, device_id=device_id, device_type=device_type, now=float(now)
            )
        except Exception:  # noqa: BLE001
            return

    # ── one step, at most one SDM call ───────────────────────────────────────

    def step(self, now: float) -> dict[str, Any]:
        """Execute at most **one** action — and so at most one SDM API call.

        Returns a result dict; it never raises for an expected condition. A
        :class:`~iot_asp_autoroute.nest.sdm_client.SdmThrottled` is **not** an error: it
        is the limiter saying "not yet", so the action is rescheduled to ``retry_at``,
        ``throttled`` is reported and the consecutive-error count is left alone.
        """
        now = float(now)
        action = self.plan(now)
        result: dict[str, Any] = {
            "ok": True,
            "kind": None,
            "at": None,
            "deviceRef": None,
            "calls": 0,
            "telemetry": 0,
            "events": 0,
            "throttled": False,
            "error": None,
            "holdManual": self._hold_manual,
            "reason": None,
        }
        if action is None:
            result["reason"] = "idle"
            return result

        result["kind"] = action.kind
        result["at"] = action.at
        result["deviceRef"] = (
            mapping.device_ref(action.device_id) if action.device_id else None
        )
        if action.at > now:
            result["reason"] = "not-due"
            result["sleepS"] = action.at - now
            return result

        self._steps += 1
        try:
            if action.kind == ACTION_EVENTS:
                self._do_events(now, result)
            elif action.kind == ACTION_LIST:
                self._do_list(now, result)
            else:
                self._do_get(str(action.device_id), now, result)
        except PatchWriteRefused:
            # A guard tripped: that is a defect in this module, not a flaky cycle.
            raise
        except SdmThrottled as exc:
            # Not a failure: the local budget simply is not available yet.
            self._throttles += 1
            retry_at = _finite(getattr(exc, "retry_at", None), now + self._cadence_for(action))
            self._reschedule(action, retry_at)
            result["throttled"] = True
            result["reason"] = "throttled"
            result["retryAt"] = retry_at
            return result
        except Exception as exc:  # noqa: BLE001 - one bad cycle must not kill the loop
            self._errors += 1
            self._consecutive_errors += 1
            self._last_error = f"{type(exc).__name__}: {exc}"
            mult = min(_ERROR_BACKOFF_MAX_MULT, float(2 ** (self._consecutive_errors - 1)))
            retry_at = _finite(
                getattr(exc, "retry_at", None), now + self._cadence_for(action) * mult
            )
            self._reschedule(action, retry_at)
            result["ok"] = False
            result["error"] = self._last_error
            result["reason"] = "error"
            result["retryAt"] = retry_at
            return result

        self._consecutive_errors = 0
        result["reason"] = "done"
        return result

    # ── action handlers ──────────────────────────────────────────────────────

    def _do_list(self, now: float, result: dict[str, Any]) -> None:
        """One ``devices.list``: reconcile the fleet and its connectivity."""
        devices = self._client.list_devices(now=now)
        self._calls += 1
        self._last_call_at = now
        result["calls"] = 1
        self._next_list_at = now + self._jittered(
            self._list_cadence_s, constants.DEFAULT_LIST_CADENCE_S
        )
        result["telemetry"] += self._register(devices, now, emit_all=False)

    def _do_get(self, device_id: str, now: float, result: dict[str, Any]) -> None:
        """One ``devices.get`` against a single instance — the liveness heartbeat."""
        device_type = _device_type(self._devices.get(device_id))
        device = self._client.get_device(device_id, device_type=device_type, now=now)
        self._calls += 1
        self._last_call_at = now
        result["calls"] = 1
        cadence = self.effective_camera_cadence_s()
        self._next_device_at[device_id] = now + self._jittered(
            cadence, constants.DEFAULT_CAMERA_CADENCE_S
        )
        result["telemetry"] += self._register([device], now, emit_all=True)

    def _do_events(self, now: float, result: dict[str, Any]) -> None:
        """One Pub/Sub ``:pull`` (plus the matching ``:acknowledge``).

        Not an SDM method, so it consumes none of the quotas the limits page meters and
        is not gated by the limiter — see the module docstring, including the UNVERIFIED
        note on that inference. ``acknowledge`` is part of the same action: leaving
        messages unacked would redeliver them forever.
        """
        pairs = self._puller.pull(max_messages=self._max_messages)
        self._pulls += 1
        self._next_events_at = now + self._jittered(
            self._events_cadence_s, MIN_EVENTS_CADENCE_S
        )

        ack_ids: list[str] = []
        for ack_id, event in pairs or ():
            if isinstance(ack_id, str) and ack_id:
                ack_ids.append(ack_id)
            if event is None:
                continue
            if self._deduper.seen(event, now):
                continue
            self._events_seen += 1
            self._last_event_at = now
            result["events"] += 1
            device_id = getattr(event, "device_id", "") or ""
            known = self._devices.get(device_id)
            telemetry = mapping.event_to_telemetry(
                event,
                node_id=self._node_id,
                now=float(self._wall_clock()),
                source=mapping.SOURCE_EVENT,
                device_type=_device_type(known),
                connectivity=_connectivity(known),
            )
            if self._emit(telemetry):
                result["telemetry"] += 1
        if ack_ids:
            self._puller.acknowledge(ack_ids)

    # ── fleet bookkeeping ────────────────────────────────────────────────────

    def _register(self, devices: Iterable[Any], now: float, *, emit_all: bool) -> int:
        """Record devices, schedule new cameras with a staggered phase, emit heartbeats.

        ``emit_all=False`` (a ``devices.list`` reconciliation) emits a heartbeat only for
        a newly-seen device or a changed ``Connectivity`` status, so one list call cannot
        fan out into an unbounded write volley. ``emit_all=True`` (a ``devices.get``) is
        the deliberate per-instance liveness heartbeat.
        """
        emitted = 0
        new_ids: list[str] = []
        for device in devices or ():
            device_id = str(getattr(device, "device_id", "") or "")
            if not device_id:
                continue
            is_new = device_id not in self._devices
            previous = self._connectivity.get(device_id)
            current = _connectivity(device)
            self._devices[device_id] = device
            self._connectivity[device_id] = current
            if is_new:
                self._device_order.append(device_id)
                if _is_camera_like(device):
                    new_ids.append(device_id)
                self._warm(
                    constants.METHOD_DEVICES_GET, device_id, _device_type(device), now
                )
            if self._write_state:
                self._write_state_record(device)
            if emit_all or is_new or current != previous:
                if self._emit(self._poll_telemetry(device)):
                    emitted += 1

        if new_ids:
            self._schedule_new(new_ids, now)
        return emitted

    def _schedule_new(self, new_ids: list[str], now: float) -> None:
        """Phase-stagger newly discovered cameras so N of them never align.

        Device *i* of *n* is offset by ``i × cadence / n`` plus the usual jitter, which
        spreads the fleet evenly across one cadence. Without this, every camera
        discovered by the same ``devices.list`` would come due at the same instant and
        the limiter would have to serialise a volley — legal, but exactly the burst
        shape #85 rules out.
        """
        cadence = self.effective_camera_cadence_s()
        total = max(1, len(self._device_order))
        for device_id in new_ids:
            index = self._device_order.index(device_id)
            phase = cadence * (index % total) / total
            self._next_device_at[device_id] = now + self._jittered(phase, 0.0)

    def _poll_telemetry(self, device: Any) -> dict[str, Any]:
        """A ``nestSource: "poll"`` heartbeat: reference, type, connectivity, nothing else.

        Deliberately narrower than ``mapping.device_to_state`` (which also lists trait
        names for the private ``meta/nest/state`` tree): the public heartbeat carries
        only the wire fields ``docs/api-contract.md`` names for a Nest poll.
        """
        state = mapping.device_to_state(device)
        telemetry: dict[str, Any] = {
            "schemaVersion": state.get("schemaVersion"),
            "deviceId": self._node_id,
            "ts": mapping.normalize_ts(None, now=float(self._wall_clock())),
            "nestSource": mapping.SOURCE_POLL,
        }
        for key in ("nestDeviceRef", "nestDeviceType", "nestConnectivity"):
            value = state.get(key)
            if value:
                telemetry[key] = value
        return telemetry

    def _write_state_record(self, device: Any) -> None:
        """Write ``meta/nest/state/<ref>.json`` (private tree), guarded. Never fatal."""
        state = mapping.device_to_state(device)
        ref = str(state.get("nestDeviceRef") or "")
        if not ref:
            return
        try:
            name = nest_state_object_name(ref)  # asserts not-a-patch-path
            gcs_io.write_json(name, state)
        except ValueError:
            raise
        except Exception:  # noqa: BLE001 - a state-tree write must not stall observation
            return

    def _emit(self, telemetry: dict[str, Any]) -> bool:
        """Hand one heartbeat to the sink after both guards pass.

        :func:`assert_telemetry_only` and :func:`assert_not_patch_path` are checked
        **before** the sink sees the payload, so the refusal happens here even when the
        sink is a caller-supplied function that would happily write anywhere.
        """
        assert_telemetry_only(telemetry)
        telemetry_object_name(self._node_id, str(telemetry.get("ts") or ""))
        sink = self._sink if self._sink is not None else _default_sink
        sink(telemetry)
        self._telemetry += 1
        return True

    # ── scheduling helpers ───────────────────────────────────────────────────

    def _cadence_for(self, action: PollAction) -> float:
        if action.kind == ACTION_EVENTS:
            return self._events_cadence_s
        if action.kind == ACTION_LIST:
            return self._list_cadence_s
        return self.effective_camera_cadence_s()

    def _reschedule(self, action: PollAction, at: float) -> None:
        at = float(at)
        if action.kind == ACTION_EVENTS:
            self._next_events_at = at
        elif action.kind == ACTION_LIST:
            self._next_list_at = at
        elif action.device_id:
            self._next_device_at[action.device_id] = at

    def _jittered(self, cadence: float, floor: float) -> float:
        """``cadence × (1 ± jitter_frac)``, clamped so it never drops below ``floor``.

        ``floor`` is the documented quota floor for that cadence (0 for a stagger
        phase), so jitter can spread calls **later** freely but can never pull one
        earlier than the published minimum spacing. Deterministic under a seeded ``rng``.
        """
        base = float(cadence)
        if self._jitter_frac > 0.0:
            base += float(cadence) * self._rng.uniform(-self._jitter_frac, self._jitter_frac)
        return max(float(floor), base)

    # ── the loop (the only sleeper in the package) ───────────────────────────

    def run_forever(
        self,
        *,
        sleep: Callable[[float], Any] = time.sleep,
        max_steps: int | None = None,
        stop: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        """Sleep until ``plan().at``, take one step, repeat.

        ``sleep`` is injected and is always called with a **non-negative** duration.
        ``max_steps`` and ``stop()`` make the loop finite and testable; with neither it
        runs until the process is killed. Nothing here bursts: one iteration is one
        ``plan()`` and one ``step()``, and ``step()`` is at most one API call.
        """
        steps = 0
        stopped = "max_steps"
        while max_steps is None or steps < int(max_steps):
            if stop is not None and stop():
                stopped = "stop"
                break
            now = float(self._clock())
            action = self.plan(now)
            delay = (
                self._events_cadence_s
                if action is None
                else max(0.0, float(action.at) - now)
            )
            if delay > 0.0:
                sleep(delay)
            if action is None:
                steps += 1
                continue
            self.step(float(self._clock()))
            steps += 1

        return {
            "ok": self._consecutive_errors == 0,
            "steps": steps,
            "stopped": stopped,
            "calls": self._calls,
            "pulls": self._pulls,
            "events": self._events_seen,
            "telemetry": self._telemetry,
            "throttled": self._throttles,
            "errors": self._errors,
            "consecutiveErrors": self._consecutive_errors,
            "holdManual": self._hold_manual,
        }

    # ── health ───────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """Cadences, limiter snapshot, error count, event age, Hold passthrough.

        This is what the ADK tool and the PWA surface render, so it carries **no** raw
        device id: instances appear as ``mapping.device_ref`` hashes. Never raises.
        """
        now = float(self._clock())
        health: dict[str, Any] = {
            "nodeId": self._node_id,
            "holdManual": self._hold_manual,
            "listCadenceS": self._list_cadence_s,
            "cameraCadenceS": self._camera_cadence_s,
            "effectiveCameraCadenceS": self.effective_camera_cadence_s(),
            "eventsCadenceS": self._events_cadence_s,
            "jitterFrac": self._jitter_frac,
            "devices": len(self._device_order),
            "deviceRefs": [mapping.device_ref(d) for d in self._device_order],
            "steps": self._steps,
            "calls": self._calls,
            "pulls": self._pulls,
            "events": self._events_seen,
            "telemetry": self._telemetry,
            "throttled": self._throttles,
            "errors": self._errors,
            "consecutiveErrors": self._consecutive_errors,
            "lastError": self._last_error,
            "lastEventAgeS": None if self._last_event_at is None else now - self._last_event_at,
            "lastCallAgeS": None if self._last_call_at is None else now - self._last_call_at,
            "eventsEnabled": self._puller is not None,
            "writesPatches": False,
        }
        action = self.plan(now)
        health["nextAction"] = (
            None
            if action is None
            else {
                "kind": action.kind,
                "inS": max(0.0, action.at - now),
                "deviceRef": mapping.device_ref(action.device_id)
                if action.device_id
                else None,
                "reason": action.reason,
            }
        )
        health["limiter"] = _safe_call(
            getattr(self._limiter, "snapshot", None), now
        )
        health["client"] = _safe_call(getattr(self._client, "status", None))
        health["puller"] = _safe_call(getattr(self._puller, "status", None))
        health["deduper"] = _safe_call(getattr(self._deduper, "stats", None))
        return health

    def __repr__(self) -> str:  # noqa: D105 - never leak node internals or device ids
        return (
            f"<NestPoller node={self._node_id!r} devices={len(self._device_order)} "
            f"calls={self._calls} events={self._events_seen} "
            f"holdManual={self._hold_manual}>"
        )

    __str__ = __repr__


# ── module helpers ───────────────────────────────────────────────────────────


def _validate_cadence(value: Any, floor: float, label: str, why: str) -> float:
    """Return the cadence, refusing anything faster than the documented floor."""
    if value is None:
        return float(floor)
    try:
        cadence = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"refuse: {label} must be a number, got {value!r}") from None
    if not math.isfinite(cadence):
        raise ValueError(f"refuse: {label} must be finite, got {value!r}")
    if cadence < float(floor) - _CADENCE_EPS:
        raise ValueError(
            f"refuse: {label}={cadence} s is faster than the documented floor "
            f"{floor} s ({why}); a caller may only make a cadence slower. "
            "See https://developers.google.com/nest/device-access/project/limits"
        )
    return cadence


def _finite(value: Any, fallback: float) -> float:
    """``float(value)`` when it is a finite number, else ``fallback``."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float(fallback)
    out = float(value)
    return out if math.isfinite(out) else float(fallback)


def _device_type(device: Any) -> str | None:
    value = getattr(device, "type", None)
    return value if isinstance(value, str) and value else None


def _connectivity(device: Any) -> str | None:
    value = getattr(device, "connectivity", None)
    return value if isinstance(value, str) and value else None


def _is_camera_like(device: Any) -> bool:
    value = getattr(device, "is_camera_like", None)
    if isinstance(value, bool):
        return value
    return _device_type(device) in constants.CAMERA_LIKE_TYPES


def _safe_call(fn: Any, *args: Any) -> Any:
    """Call an optional health hook; ``None`` on absence or failure. Never raises."""
    if not callable(fn):
        return None
    try:
        return fn(*args)
    except Exception:  # noqa: BLE001 - health must never raise
        return None


def _default_sink(telemetry: dict[str, Any]) -> Any:
    """``tools.ingest_telemetry`` when importable, else a guarded ``gcs_io`` write.

    ``tools`` reaches numpy/scipy through ``vib_anomaly``; the fallback keeps the poller
    (and ``scripts/nest_dev.sh``) working in a bare stdlib environment. Both paths write
    only under ``meta/telemetry/``.
    """
    try:
        from ..tools import ingest_telemetry  # noqa: PLC0415
    except Exception:  # noqa: BLE001 - bare env
        name = telemetry_object_name(
            str(telemetry.get("deviceId") or ""), str(telemetry.get("ts") or "")
        )
        return gcs_io.write_json(name, telemetry)
    return ingest_telemetry(json.dumps(telemetry))
