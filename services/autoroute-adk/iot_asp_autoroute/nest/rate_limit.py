"""SDM quota pacing — continuous observation, structurally never a burst (#85, #3).

The Smart Device Management API publishes *hard* quotas and answers an overrun with
``RESOURCE_EXHAUSTED`` ("Rate limited"), telling the caller to "resubmit the call once
the quota has expired" — there is no leaky-bucket grace.
Source: https://developers.google.com/nest/device-access/project/limits

Two independent facts from that page drive this module:

* **Per method, project-wide:** ``devices.list`` 5 QPM, ``devices.get`` 10 QPM,
  ``devices.executeCommand`` 10 QPM (plus "Each trait command
  (``devices.executeCommand``) is limited to 5 QPM per project, per user, per device").
* **Per device instance:** ``CAMERA`` / ``DOORBELL`` "30 QPM or 100 QPH",
  ``THERMOSTAT`` "5 QPM or 100 QPH".

The *hourly* cap is the one that bites a continuous observer: 100 QPH is
``3600 / 100 = 36.0`` s sustained per camera, eighteen times slower than the 2.0 s the
per-minute cap alone would allow. A limiter that only models QPM passes a unit test and
then earns ``RESOURCE_EXHAUSTED`` in the field an hour later. Every number here is read
from :mod:`iot_asp_autoroute.nest.constants`; nothing is re-derived or hardcoded.

Design (the three properties the acceptance tests check):

1. **Sliding windows, not fixed buckets.** A fixed-window counter admits ``2L`` calls
   across a window boundary. Each window here is evaluated against the actual call
   timestamps, so a call at ``t`` occupies ``[t, t + span)`` and nothing else.
2. **Every applicable window must have headroom**, simultaneously — per-method,
   per-device-instance and (for commands) per-device-per-command.
3. **A pacing floor.** Windows alone still permit a 100-call burst followed by 58 idle
   minutes. Issue #85 asks for *continuous* observation, so a bucket additionally
   refuses any call closer than ``constants.min_interval_s(qpm, qph)`` to the previous
   one. That is what makes ``DEFAULT_LIST_CADENCE_S`` (12.0 s) and
   ``DEFAULT_CAMERA_CADENCE_S`` (36.0 s) the *achievable* steady state rather than an
   aspiration.

No network, no sleeps, no global clock: every entry point takes ``now`` from the
caller's injected clock, and jitter comes from an injected :class:`random.Random`, so a
run is byte-reproducible. Memory is bounded — timestamps older than the longest window
are dropped on write, so a process running for weeks retains at most ``qph`` (or
``qpm``) marks per bucket.

stdlib only.
"""

from __future__ import annotations

import hashlib
import math
import random
from bisect import bisect_right, insort
from typing import Any, Final

from . import constants

# QPM / QPH are, by definition, "queries per 60 s" and "queries per 3600 s"; these are
# the window spans those units name, not a restatement of any constant in constants.py.
MINUTE_S: Final[float] = 60.0
HOUR_S: Final[float] = 3600.0

#: ``2 ** attempt`` is clamped at this exponent before the float multiply, so a runaway
#: attempt counter cannot raise ``OverflowError`` (the result is capped at
#: ``constants.BACKOFF_MAX_S`` long before this matters).
MAX_BACKOFF_EXP: Final[int] = 64

#: Idle per-device buckets are evicted above this many tracked devices, so a long-lived
#: process that has seen many device ids does not grow without bound.
MAX_TRACKED_BUCKETS: Final[int] = 512

#: Bounded fix-point iterations when solving "earliest instant every window allows".
#: Two passes suffice in practice; the extra headroom absorbs float ULP nudges.
_FIXPOINT_ITERS: Final[int] = 8

_KIND_METHOD: Final[str] = "method"
_KIND_DEVICE: Final[str] = "device"
_KIND_COMMAND: Final[str] = "command"
#: Bucket-key kinds whose identifier half is a raw SDM device id — a site identifier
#: under CLAUDE.md #7, so it is hashed before it can reach a health/telemetry surface.
_PII_KINDS: Final[frozenset[str]] = frozenset({_KIND_DEVICE, _KIND_COMMAND})


def bucket_ref(key: str) -> str:
    """PII-safe rendering of a bucket key for snapshots and logs.

    ``method:devices.list`` is public API vocabulary and passes through unchanged;
    ``device:<sdm device id>`` becomes ``device:<sha256(id)[:12]>`` because a raw SDM
    device id identifies a site (CLAUDE.md #7). The digest recipe is the same one the
    wire mapper uses for ``nestDeviceRef``.
    """
    kind, sep, ident = str(key).partition(":")
    if not sep or not ident or kind not in _PII_KINDS:
        return str(key)
    return f"{kind}:{hashlib.sha256(ident.encode('utf-8')).hexdigest()[:12]}"


class QuotaBucket:
    """Sliding-window limiter over one or two windows (per-minute and per-hour).

    ``qpm`` is required; ``qph`` is optional because the SDM limits page documents an
    hourly cap only for device instances. Beyond the windows the bucket enforces the
    pacing floor ``constants.min_interval_s(qpm, qph)`` between consecutive calls, which
    is what turns a quota into a continuous cadence instead of a burst-then-starve
    pattern.

    All times are seconds on the caller's clock (monotonic or epoch — the bucket only
    ever compares and adds). Nothing here sleeps or reads a clock of its own.
    """

    def __init__(self, key: str, qpm: int, qph: int | None = None) -> None:
        # Validation (and the floor itself) lives in constants.min_interval_s: a
        # non-positive quota raises ValueError there rather than silently pacing at 0.
        self._min_interval = constants.min_interval_s(qpm, qph)
        self.key = str(key)
        self.qpm = int(qpm)
        self.qph = None if qph is None else int(qph)
        windows: list[tuple[float, int]] = [(MINUTE_S, self.qpm)]
        if self.qph is not None:
            windows.append((HOUR_S, self.qph))
        self._windows: tuple[tuple[float, int], ...] = tuple(windows)
        self._max_span: float = max(span for span, _ in self._windows)
        self._ts: list[float] = []

    # ── introspection ────────────────────────────────────────────────────────

    @property
    def min_interval_s(self) -> float:
        """Minimum sustainable seconds between calls (``constants.min_interval_s``)."""
        return self._min_interval

    @property
    def windows(self) -> tuple[tuple[float, int], ...]:
        """``((span_s, limit), ...)`` — 60 s always, 3600 s when ``qph`` is set."""
        return self._windows

    def __len__(self) -> int:
        """Retained timestamps (bounded by the longest window's limit)."""
        return len(self._ts)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<QuotaBucket {self.key!r} qpm={self.qpm} qph={self.qph} held={len(self._ts)}>"

    # ── internals ────────────────────────────────────────────────────────────

    def _count_in(self, at: float, span: float) -> int:
        """Calls occupying the window ending at ``at`` — that is, ``ts > at - span``.

        Half-open on the left, so two calls exactly ``span`` apart never share a window;
        that is the same boundary the independent audit in the tests uses (a call at
        ``t`` occupies ``[t, t + span)``).
        """
        return len(self._ts) - bisect_right(self._ts, at - span)

    def _earliest(self, start: float) -> float:
        """Earliest instant ``>= start`` at which every constraint has headroom."""
        cand = float(start)
        for _ in range(_FIXPOINT_ITERS):
            bump = cand
            if self._ts:
                paced = self._ts[-1] + self._min_interval
                if paced > bump:
                    bump = paced
            for span, limit in self._windows:
                if self._count_in(bump, span) >= limit:
                    # The limit-th newest call is the one that has to age out.
                    release = self._ts[len(self._ts) - limit] + span
                    # ``release`` can land one ULP short of clearing the window after a
                    # float add; nudge instead of spinning on the same value.
                    bump = release if release > bump else math.nextafter(bump, math.inf)
            if bump == cand:
                return cand
            cand = bump
        return cand  # pragma: no cover - fix-point converges in <= 2 passes

    def _prune(self, now: float) -> None:
        """Drop marks older than the longest window — they can never bind again."""
        if not self._ts:
            return
        cutoff = float(now) - self._max_span
        drop = bisect_right(self._ts, cutoff)
        if drop:
            del self._ts[:drop]

    # ── public API ───────────────────────────────────────────────────────────

    def next_allowed_at(self, now: float) -> float:
        """Earliest time a call may go; exactly ``now`` when the bucket is free.

        Side-effect free, so a scheduler may call it repeatedly while planning.
        """
        return self._earliest(float(now))

    def try_acquire(self, now: float) -> bool:
        """Record a call at ``now`` iff every window and the pacing floor allow it."""
        now = float(now)
        if self.next_allowed_at(now) > now:
            return False
        self.record(now)
        return True

    def record(self, now: float) -> None:
        """Record a call unconditionally (used to replay a call log into a bucket)."""
        now = float(now)
        if not math.isfinite(now):
            raise ValueError(f"refuse: now must be finite, got {now!r}")
        insort(self._ts, now)
        self._prune(now)

    def remaining(self, now: float) -> dict[str, int | None]:
        """Headroom left in each window: ``{"minute": int, "hour": int | None}``."""
        now = float(now)
        minute = self.qpm - self._count_in(now, MINUTE_S)
        hour = None if self.qph is None else self.qph - self._count_in(now, HOUR_S)
        return {
            "minute": max(0, minute),
            "hour": None if hour is None else max(0, hour),
        }


class SdmRateLimiter:
    """Composes the project-wide method bucket with the per-device-instance bucket.

    A call is allowed only when EVERY applicable bucket allows it:

    * ``method:<method>`` — the project-wide QPM from ``constants.METHOD_QUOTAS``.
    * ``device:<device_id>`` — the instance quota from ``constants.DEVICE_QUOTAS``
      (30 QPM **or** 100 QPH for a camera), whenever a ``device_id`` is supplied.
    * ``command:<device_id>`` — ``devices.executeCommand`` only: "Each trait command
      (devices.executeCommand) is limited to 5 QPM per project, per user, per device."
      (https://developers.google.com/nest/device-access/project/limits). This bucket
      only ever tightens; the 36 s camera floor already dominates it in practice.

    ``penalize`` records a backoff deadline on every bucket of the offending shape.
    Attributing ``RESOURCE_EXHAUSTED`` to one specific quota is not possible from the
    error alone, so the deadline is applied conservatively to all of them.
    """

    def __init__(self, *, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()
        self._buckets: dict[str, QuotaBucket] = {}
        self._device_types: dict[str, str | None] = {}
        self._penalty_until: dict[str, float] = {}

    # ── bucket resolution ────────────────────────────────────────────────────

    @staticmethod
    def _method_key(method: str) -> str:
        return f"{_KIND_METHOD}:{method}"

    @staticmethod
    def _device_key(device_id: str) -> str:
        return f"{_KIND_DEVICE}:{device_id}"

    @staticmethod
    def _command_key(device_id: str) -> str:
        return f"{_KIND_COMMAND}:{device_id}"

    def _method_bucket(self, method: str) -> QuotaBucket:
        try:
            qpm, qph = constants.METHOD_QUOTAS[method]
        except KeyError:
            raise ValueError(f"unknown SDM method: {method}") from None
        key = self._method_key(method)
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = self._buckets[key] = QuotaBucket(key, qpm, qph)
        return bucket

    def _device_bucket(self, device_id: str, device_type: str | None) -> QuotaBucket:
        """Per-instance bucket, tightened (never loosened) if the type is learned late.

        An unknown or missing ``device_type`` resolves to the camera quota, matching
        ``constants.device_min_interval_s``. If a later call names a stricter type
        (a thermostat is 5 QPM, not 30) the bucket is rebuilt at the stricter quota and
        the existing marks are replayed, so history is never lost by learning more.
        """
        qpm, qph = constants.DEVICE_QUOTAS.get(
            device_type or "", constants.DEVICE_QUOTAS[constants.TYPE_CAMERA]
        )
        key = self._device_key(device_id)
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = self._buckets[key] = QuotaBucket(key, qpm, qph)
            self._device_types[device_id] = device_type
            return bucket
        tight_qpm = min(bucket.qpm, qpm)
        # ``None`` means "no hourly cap documented for this unit"; the tighter of the two
        # is the smallest cap that exists, so a documented cap always beats ``None``.
        hourly = [q for q in (bucket.qph, qph) if q is not None]
        tight_qph = min(hourly) if hourly else None
        if tight_qpm != bucket.qpm or tight_qph != bucket.qph:
            replacement = QuotaBucket(key, tight_qpm, tight_qph)
            for mark in list(bucket._ts):  # noqa: SLF001 - replay via the public record()
                replacement.record(mark)
            bucket = self._buckets[key] = replacement
            self._device_types[device_id] = device_type
        return bucket

    def _command_bucket(self, device_id: str) -> QuotaBucket:
        key = self._command_key(device_id)
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = self._buckets[key] = QuotaBucket(key, constants.TRAIT_COMMAND_QPM, None)
        return bucket

    def _shape(
        self, method: str, device_id: str | None, device_type: str | None
    ) -> list[QuotaBucket]:
        buckets = [self._method_bucket(method)]
        if device_id:
            buckets.append(self._device_bucket(str(device_id), device_type))
            if method == constants.METHOD_DEVICES_EXECUTE_COMMAND:
                buckets.append(self._command_bucket(str(device_id)))
        return buckets

    # ── public API ───────────────────────────────────────────────────────────

    def next_allowed_at(
        self,
        method: str,
        *,
        device_id: str | None = None,
        device_type: str | None = None,
        now: float,
    ) -> float:
        """Earliest time this call shape may go — the max over every applicable bucket
        and any outstanding backoff deadline. ``now`` when nothing is blocking."""
        now = float(now)
        at = now
        for bucket in self._shape(method, device_id, device_type):
            at = max(at, bucket.next_allowed_at(now))
            penalty = self._penalty_until.get(bucket.key)
            if penalty is not None and penalty > at:
                at = penalty
        return at

    def try_acquire(
        self,
        method: str,
        *,
        device_id: str | None = None,
        device_type: str | None = None,
        now: float,
    ) -> bool:
        """Record the call in every applicable bucket iff all of them allow it now.

        All-or-nothing: a partially recorded call would let one window drift ahead of
        another and eventually admit a burst.
        """
        now = float(now)
        if self.next_allowed_at(
            method, device_id=device_id, device_type=device_type, now=now
        ) > now:
            return False
        for bucket in self._shape(method, device_id, device_type):
            bucket.record(now)
        self._gc(now)
        return True

    def penalize(
        self,
        method: str,
        *,
        device_id: str | None = None,
        device_type: str | None = None,
        now: float,
        attempt: int,
    ) -> float:
        """Full-jitter exponential backoff after ``RESOURCE_EXHAUSTED`` / 5xx.

        ``sleep = rng.uniform(0, min(BACKOFF_MAX_S, BACKOFF_BASE_S * 2 ** attempt))`` —
        the AWS "full jitter" form, chosen so a fleet of pollers that all trip the same
        project quota do not retry in lockstep. Deterministic under a seeded ``rng``.

        Returns the absolute time before which no call of this shape may be made. The
        deadline only ever moves later: a fresh penalty never shortens a standing one.
        """
        now = float(now)
        bound = self.backoff_bound_s(attempt)
        delay = self._rng.uniform(0.0, bound)
        until = now + delay
        for bucket in self._shape(method, device_id, device_type):
            prev = self._penalty_until.get(bucket.key)
            if prev is None or until > prev:
                self._penalty_until[bucket.key] = until
        return until

    @staticmethod
    def backoff_bound_s(attempt: int) -> float:
        """Un-jittered ceiling for ``attempt``: ``min(BACKOFF_MAX_S, BASE * 2**attempt)``.

        Monotonically non-decreasing in ``attempt`` and never above
        ``constants.BACKOFF_MAX_S``. A negative attempt clamps to 0; an absurd attempt
        clamps at :data:`MAX_BACKOFF_EXP` so the float multiply cannot overflow.
        """
        exp = max(0, min(int(attempt), MAX_BACKOFF_EXP))
        return min(constants.BACKOFF_MAX_S, constants.BACKOFF_BASE_S * float(2**exp))

    def penalty_until(
        self,
        method: str,
        *,
        device_id: str | None = None,
        device_type: str | None = None,
    ) -> float | None:
        """Standing backoff deadline for this shape, or ``None``."""
        deadlines = [
            self._penalty_until[b.key]
            for b in self._shape(method, device_id, device_type)
            if b.key in self._penalty_until
        ]
        return max(deadlines) if deadlines else None

    def snapshot(self, now: float) -> dict[str, Any]:
        """Per-bucket headroom for telemetry / ``poller.health()``.

        Device ids are hashed (:func:`bucket_ref`) — a raw SDM device id is a site
        identifier and must never reach a public surface (CLAUDE.md #7).
        """
        now = float(now)
        buckets: dict[str, Any] = {}
        for key, bucket in sorted(self._buckets.items()):
            buckets[bucket_ref(key)] = {
                "qpm": bucket.qpm,
                "qph": bucket.qph,
                "minIntervalS": bucket.min_interval_s,
                "remaining": bucket.remaining(now),
                "nextAllowedAt": bucket.next_allowed_at(now),
                "held": len(bucket),
            }
        penalties = {
            bucket_ref(key): until
            for key, until in sorted(self._penalty_until.items())
            if until > now
        }
        return {
            "now": now,
            "buckets": buckets,
            "penaltyUntil": penalties,
            "listFloorS": constants.DEFAULT_LIST_CADENCE_S,
            "cameraFloorS": constants.DEFAULT_CAMERA_CADENCE_S,
        }

    # ── housekeeping ─────────────────────────────────────────────────────────

    def _gc(self, now: float) -> None:
        """Evict idle per-device buckets and elapsed penalties (bounded memory)."""
        self._penalty_until = {k: v for k, v in self._penalty_until.items() if v > now}
        if len(self._buckets) <= MAX_TRACKED_BUCKETS:
            return
        idle = [
            key
            for key, bucket in self._buckets.items()
            if key.partition(":")[0] in _PII_KINDS
            and len(bucket) == 0
            and key not in self._penalty_until
        ]
        for key in idle:
            del self._buckets[key]
            self._device_types.pop(key.partition(":")[2], None)


__all__ = ["MINUTE_S", "HOUR_S", "QuotaBucket", "SdmRateLimiter", "bucket_ref"]
