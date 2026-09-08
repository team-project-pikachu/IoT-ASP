"""Tests for iot_asp_autoroute.nest.rate_limit (#85) — offline, deterministic, stdlib-only.

This module gets formal verification checked three independent ways, because the whole
premise of #85 is CONTINUOUS observation and a limiter that is merely "probably fine"
earns ``RESOURCE_EXHAUSTED`` an hour into a field run:

 (1) ANALYTIC   — the derived floors equal the arithmetic of the documented quotas
                  (12.0 s for devices.list, 36.0 s per camera, 6 cameras at 36 s).
 (2) SIMULATION — a simulated clock drives a realistic fleet (1 devices.list stream +
                  3 cameras + backoff events) for >2 simulated hours, greedily asking
                  for calls as fast as the limiter permits, recording a call log.
 (3) RECOMPUTATION — :func:`max_calls_in_window` re-derives, from that call log alone
                  and never from the limiter's internal state, the busiest trailing
                  60 s and 3600 s window, and asserts it never exceeds the quota.

The quota numbers asserted here are written as literals taken from
https://developers.google.com/nest/device-access/project/limits and are ALSO asserted to
equal ``nest.constants`` — so relaxing a constant fails this file rather than silently
loosening the fleet.

Run: PYTHONPATH=services/autoroute-adk python3 -m pytest tests/test_nest_rate_limit.py -q
"""

from __future__ import annotations

import math
import random
import sys
from bisect import bisect_left
from pathlib import Path
from typing import Sequence

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "services" / "autoroute-adk"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from iot_asp_autoroute.nest import constants, rate_limit  # noqa: E402
from iot_asp_autoroute.nest.rate_limit import (  # noqa: E402
    QuotaBucket,
    SdmRateLimiter,
    bucket_ref,
)

# Documented quotas, quoted as literals so this file is an independent tripwire.
# Source: https://developers.google.com/nest/device-access/project/limits
DOC_LIST_QPM = 5
DOC_GET_QPM = 10
DOC_EXECUTE_QPM = 10
DOC_TRAIT_COMMAND_QPM = 5
DOC_CAMERA_QPM = 30
DOC_CAMERA_QPH = 100
DOC_THERMOSTAT_QPM = 5
DOC_THERMOSTAT_QPH = 100

# Google's own documentation placeholders — never a real SDM device id (CLAUDE.md #7).
CAMERAS = ("device-id-1", "device-id-2", "device-id-3")

SIM_HORIZON_S = 2 * 3600.0 + 600.0  # > 2 simulated hours, so the hourly cap must bind
# (simulated time, attempt) RESOURCE_EXHAUSTED events injected during the run.
# attempt=9 exercises the BACKOFF_MAX_S cap (2.0 * 2**9 = 1024 > 300).
PENALTY_EVENTS = ((900.0, 0), (1800.0, 3), (5400.0, 9))

EPS = 1e-9


# --------------------------------------------------------------------------- #
# (3) The independent recomputation checker — auditable, no limiter state used.
# --------------------------------------------------------------------------- #


def max_calls_in_window(times: Sequence[float], span: float) -> int:
    """Busiest window of length ``span`` over ``times``, computed from the log alone.

    A call at ``t`` occupies the half-open interval ``[t, t + span)``. The maximum
    over *all* window start offsets is attained by a window whose left edge sits on a
    call: sliding any window left until it touches a call can only add calls, never
    drop one. So scanning the ``len(times)`` window starts that matter is exact, not a
    sample.
    """
    ts = sorted(float(t) for t in times)
    best = 0
    for i, start in enumerate(ts):
        j = bisect_left(ts, start + float(span))
        if j - i > best:
            best = j - i
    return best


def spacings(times: Sequence[float]) -> list[float]:
    ts = sorted(float(t) for t in times)
    return [b - a for a, b in zip(ts, ts[1:])]


# 0. the checker itself is trusted only because it is tested
def test_max_calls_in_window_checker_is_correct():
    assert max_calls_in_window([], 60.0) == 0
    assert max_calls_in_window([1.0], 60.0) == 1
    # Exactly `span` apart => different windows (half-open [t, t+span)).
    assert max_calls_in_window([0.0, 60.0], 60.0) == 1
    assert max_calls_in_window([0.0, 59.999], 60.0) == 2
    # A fixed-window counter's classic failure: 5 late in one minute, 5 early in the
    # next. The checker must see 10, which is what makes it a real audit.
    burst = [55.0, 56.0, 57.0, 58.0, 59.0, 60.0, 61.0, 62.0, 63.0, 64.0]
    assert max_calls_in_window(burst, 60.0) == 10
    assert max_calls_in_window(burst, 5.0) == 5


# --------------------------------------------------------------------------- #
# (1) ANALYTIC — the floors are the arithmetic of the documented quotas.
# --------------------------------------------------------------------------- #


# 1. the documented quota numbers, pinned (relaxing a constant fails here)
def test_documented_quotas_are_unrelaxed():
    assert constants.METHOD_QUOTAS[constants.METHOD_DEVICES_LIST] == (DOC_LIST_QPM, None)
    assert constants.METHOD_QUOTAS[constants.METHOD_DEVICES_GET] == (DOC_GET_QPM, None)
    assert constants.METHOD_QUOTAS[constants.METHOD_DEVICES_EXECUTE_COMMAND] == (
        DOC_EXECUTE_QPM,
        None,
    )
    assert constants.DEVICE_QUOTAS[constants.TYPE_CAMERA] == (DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    assert constants.DEVICE_QUOTAS[constants.TYPE_DOORBELL] == (DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    assert constants.DEVICE_QUOTAS[constants.TYPE_THERMOSTAT] == (
        DOC_THERMOSTAT_QPM,
        DOC_THERMOSTAT_QPH,
    )
    assert constants.TRAIT_COMMAND_QPM == DOC_TRAIT_COMMAND_QPM
    assert constants.BACKOFF_BASE_S == 2.0
    assert constants.BACKOFF_MAX_S == 300.0


# 2. derived floors == the arithmetic, and the hourly cap is what binds a camera
def test_analytic_floors_match_quota_arithmetic():
    # devices.list: 5 QPM, no documented hourly cap -> 60 / 5 = 12.0 s.
    assert constants.min_interval_s(DOC_LIST_QPM) == 60.0 / DOC_LIST_QPM == 12.0
    assert constants.DEFAULT_LIST_CADENCE_S == 12.0
    assert QuotaBucket("method:devices.list", DOC_LIST_QPM).min_interval_s == 12.0

    # A camera: the per-minute cap alone would allow 60/30 = 2.0 s, but 100 QPH is
    # 3600 / 100 = 36.0 s — eighteen times slower, and it is the binding constraint.
    per_minute = 60.0 / DOC_CAMERA_QPM
    per_hour = 3600.0 / DOC_CAMERA_QPH
    assert per_minute == 2.0
    assert per_hour == 36.0
    assert constants.min_interval_s(DOC_CAMERA_QPM, DOC_CAMERA_QPH) == max(per_minute, per_hour)
    assert constants.DEFAULT_CAMERA_CADENCE_S == 36.0
    cam = QuotaBucket("device:device-id", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    assert cam.min_interval_s == 36.0

    # devices.get is 10 QPM project-wide, so N cameras at 36 s need N/36 <= 10/60.
    assert constants.max_cameras_at_cadence(36.0) == 6
    assert (6 / 36.0) <= (DOC_GET_QPM / 60.0) + EPS
    assert (7 / 36.0) > (DOC_GET_QPM / 60.0)


# 3. bucket window shape follows the documented units
def test_bucket_windows_are_minute_and_hour():
    assert rate_limit.MINUTE_S == 60.0 and rate_limit.HOUR_S == 3600.0
    listed = QuotaBucket("method:devices.list", DOC_LIST_QPM)
    assert listed.windows == ((60.0, DOC_LIST_QPM),)
    cam = QuotaBucket("device:device-id", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    assert cam.windows == ((60.0, DOC_CAMERA_QPM), (3600.0, DOC_CAMERA_QPH))


# 4. negative control: a non-positive quota is refused, never paced at zero
@pytest.mark.parametrize("qpm,qph", [(0, None), (-1, None), (5, 0), (5, -3)])
def test_bucket_refuses_nonpositive_quota(qpm, qph):
    with pytest.raises(ValueError):
        QuotaBucket("method:bogus", qpm, qph)


# --------------------------------------------------------------------------- #
# Sliding window, pacing floor, memory.
# --------------------------------------------------------------------------- #


# 5. sliding window: a fixed-window counter admits 2L across a boundary; this does not
def test_sliding_window_boundary_refuses_double_limit():
    b = QuotaBucket("method:devices.list", DOC_LIST_QPM)
    # Replay 5 calls late in the first "minute" (record() is unconditional by design).
    late = [55.0, 56.0, 57.0, 58.0, 59.0]
    for t in late:
        b.record(t)
    assert b.remaining(59.0) == {"minute": 0, "hour": None}

    # A fixed-window counter resets at t=60 and would allow 5 more immediately,
    # putting 10 calls inside the 5-second span [55, 65) — 2L in one window.
    assert b.try_acquire(60.0) is False
    assert b.try_acquire(114.999) is False
    # The oldest of the five ages out exactly 60 s after it was made.
    assert b.next_allowed_at(60.0) == pytest.approx(late[0] + 60.0, abs=EPS)
    assert b.try_acquire(115.0) is True

    log = late + [115.0]
    assert max_calls_in_window(log, 60.0) <= DOC_LIST_QPM


# 6. the boundary holds for the hourly window too
def test_sliding_window_boundary_hourly():
    b = QuotaBucket("device:device-id", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    marks = [36.0 * i for i in range(DOC_CAMERA_QPH)]  # exactly 100 calls, 36 s apart
    for t in marks:
        b.record(t)
    # 3600 s after the first call the hourly window has room again — not one tick before.
    assert b.try_acquire(marks[0] + 3600.0 - 0.001) is False
    assert b.next_allowed_at(marks[-1]) == pytest.approx(marks[0] + 3600.0, abs=EPS)
    assert b.try_acquire(marks[0] + 3600.0) is True
    assert max_calls_in_window(marks + [3600.0], 3600.0) <= DOC_CAMERA_QPH


# 7. NB-2 pacing floor: the hourly cap binds, so calls never crowd to 2.0 s
def test_pacing_floor_prevents_burst_then_starve():
    b = QuotaBucket("device:device-id", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    allowed: list[float] = []
    t = 0.0
    while t <= 3600.0:  # greedy caller asking every 0.5 s for a full hour
        if b.try_acquire(t):
            allowed.append(t)
        t = round(t + 0.5, 6)

    # Windows alone would have permitted 30 calls in the first minute and then 70 more
    # before starving for the rest of the hour. The floor forbids that.
    assert min(spacings(allowed)) >= 36.0 - EPS
    assert max_calls_in_window(allowed, 60.0) <= DOC_CAMERA_QPM
    assert max_calls_in_window(allowed, 3600.0) <= DOC_CAMERA_QPH
    # ...and the observation really is continuous: ~one call per 36 s across the hour.
    assert len(allowed) >= 99
    assert max(spacings(allowed)) <= 36.0 + 0.5 + EPS


# 8. requesting a cadence faster than the floor is refused, not silently absorbed
def test_faster_than_floor_is_refused():
    b = QuotaBucket("device:device-id", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    refused = 0
    granted: list[float] = []
    for i in range(120):  # ask every 2.0 s (what the per-minute cap alone would allow)
        t = 2.0 * i
        if b.try_acquire(t):
            granted.append(t)
        else:
            refused += 1
    assert refused > 0
    assert granted == [36.0 * i for i in range(len(granted))]

    lim = SdmRateLimiter(rng=random.Random(85))
    assert lim.try_acquire(
        constants.METHOD_DEVICES_GET,
        device_id=CAMERAS[0],
        device_type=constants.TYPE_CAMERA,
        now=0.0,
    ) is True
    assert lim.try_acquire(
        constants.METHOD_DEVICES_GET,
        device_id=CAMERAS[0],
        device_type=constants.TYPE_CAMERA,
        now=2.0,
    ) is False
    assert lim.next_allowed_at(
        constants.METHOD_DEVICES_GET,
        device_id=CAMERAS[0],
        device_type=constants.TYPE_CAMERA,
        now=2.0,
    ) == pytest.approx(36.0, abs=EPS)


# 9. exactly-at-the-floor is sustainable forever (the floor is not off by one)
def test_floor_cadence_is_sustainable_indefinitely():
    b = QuotaBucket("device:device-id", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    marks = [36.0 * i for i in range(400)]  # 4 simulated hours at the derived floor
    for t in marks:
        assert b.try_acquire(t) is True, f"floor cadence refused at t={t}"
    assert max_calls_in_window(marks, 60.0) <= DOC_CAMERA_QPM
    assert max_calls_in_window(marks, 3600.0) <= DOC_CAMERA_QPH


# 10. bounded memory: retention never exceeds the longest window's limit
def test_memory_is_bounded_over_many_hours():
    cam = QuotaBucket("device:device-id", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    listed = QuotaBucket("method:devices.list", DOC_LIST_QPM)
    peak_cam = peak_list = 0
    t = 0.0
    while t <= 6 * 3600.0:  # six simulated hours of greedy polling
        cam.try_acquire(t)
        listed.try_acquire(t)
        peak_cam = max(peak_cam, len(cam))
        peak_list = max(peak_list, len(listed))
        t = round(t + 1.0, 6)
    assert peak_cam <= DOC_CAMERA_QPH
    assert peak_list <= DOC_LIST_QPM
    assert len(cam) <= DOC_CAMERA_QPH and len(listed) <= DOC_LIST_QPM


# 11. negative control: non-finite marks are refused before they poison the windows
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_record_refuses_non_finite_time(bad):
    b = QuotaBucket("method:devices.list", DOC_LIST_QPM)
    with pytest.raises(ValueError):
        b.record(bad)
    assert len(b) == 0


# --------------------------------------------------------------------------- #
# SdmRateLimiter composition.
# --------------------------------------------------------------------------- #


# 12. every applicable window must have headroom, simultaneously
def test_method_and_device_buckets_both_bind():
    lim = SdmRateLimiter(rng=random.Random(85))
    kw = {"device_type": constants.TYPE_CAMERA}
    # Ten distinct cameras, each polled once: the per-instance buckets stay idle, so
    # only the project-wide devices.get bucket (10 QPM) can bind.
    for i in range(DOC_GET_QPM):
        dev = f"device-id-{i}"
        assert lim.try_acquire(constants.METHOD_DEVICES_GET, device_id=dev, now=6.0 * i, **kw)
    # An eleventh camera inside the same minute is refused by the METHOD bucket even
    # though that device's own instance bucket has never been touched.
    late = "device-id-10"
    assert lim.try_acquire(constants.METHOD_DEVICES_GET, device_id=late, now=55.0, **kw) is False
    assert lim.next_allowed_at(
        constants.METHOD_DEVICES_GET, device_id=late, now=55.0, **kw
    ) == pytest.approx(60.0, abs=EPS)
    fresh = QuotaBucket(f"device:{late}", DOC_CAMERA_QPM, DOC_CAMERA_QPH)
    assert fresh.try_acquire(55.0) is True  # the device bucket alone would have allowed it


# 12b. six cameras at the 36 s floor is exactly what devices.get sustains (10 QPM)
def test_six_cameras_at_the_floor_sustain_for_an_hour():
    lim = SdmRateLimiter(rng=random.Random(85))
    kw = {"device_type": constants.TYPE_CAMERA}
    six = [f"device-id-{i}" for i in range(constants.max_cameras_at_cadence(36.0))]
    assert len(six) == 6
    calls: list[tuple[float, str]] = []
    for cycle in range(100):  # 100 cycles x 36 s = one simulated hour
        for i, dev in enumerate(six):
            t = 36.0 * cycle + 6.0 * i  # phase-staggered, as poller.py will do
            assert lim.try_acquire(constants.METHOD_DEVICES_GET, device_id=dev, now=t, **kw)
            calls.append((t, dev))
    assert max_calls_in_window([t for t, _ in calls], 60.0) <= DOC_GET_QPM
    for dev in six:
        per = [t for t, d in calls if d == dev]
        assert max_calls_in_window(per, 3600.0) <= DOC_CAMERA_QPH


# 13. negative control: an unknown method is refused, never given a default quota
def test_unknown_method_refused():
    lim = SdmRateLimiter(rng=random.Random(1))
    with pytest.raises(ValueError):
        lim.next_allowed_at("sdm.devices.nope", now=0.0)
    with pytest.raises(ValueError):
        lim.try_acquire("sdm.devices.nope", now=0.0)


# 14. executeCommand also carries the 5 QPM per-device trait-command bucket
def test_execute_command_has_per_device_trait_bucket():
    lim = SdmRateLimiter(rng=random.Random(1))
    lim.try_acquire(
        constants.METHOD_DEVICES_EXECUTE_COMMAND,
        device_id=CAMERAS[0],
        device_type=constants.TYPE_CAMERA,
        now=0.0,
    )
    snap = lim.snapshot(0.0)
    kinds = {key.partition(":")[0] for key in snap["buckets"]}
    assert kinds == {"method", "device", "command"}
    cmd = next(v for k, v in snap["buckets"].items() if k.startswith("command:"))
    assert cmd["qpm"] == DOC_TRAIT_COMMAND_QPM and cmd["qph"] is None


# 15. learning a stricter device type later tightens, never loosens, and keeps history
def test_device_type_learned_late_tightens_bucket():
    lim = SdmRateLimiter(rng=random.Random(1))
    dev = "device-id-thermostat"
    assert lim.try_acquire(constants.METHOD_DEVICES_GET, device_id=dev, now=0.0) is True
    # First call had no type -> camera quota (30/100). Now the type is known: 5 QPM.
    at = lim.next_allowed_at(
        constants.METHOD_DEVICES_GET,
        device_id=dev,
        device_type=constants.TYPE_THERMOSTAT,
        now=1.0,
    )
    assert at == pytest.approx(36.0, abs=EPS)  # 100 QPH still binds over 5 QPM
    bucket = lim._buckets[f"device:{dev}"]  # noqa: SLF001 - white-box on purpose
    assert (bucket.qpm, bucket.qph) == (DOC_THERMOSTAT_QPM, DOC_THERMOSTAT_QPH)
    assert len(bucket) == 1  # the earlier call was replayed, not dropped


# --------------------------------------------------------------------------- #
# Backoff.
# --------------------------------------------------------------------------- #


# 16. NB-4 penalty monotonicity and cap
def test_backoff_bound_is_monotonic_and_capped():
    bounds = [SdmRateLimiter.backoff_bound_s(a) for a in range(0, 20)]
    assert bounds[0] == constants.BACKOFF_BASE_S
    assert all(b <= constants.BACKOFF_MAX_S for b in bounds)
    assert all(b <= c for b, c in zip(bounds, bounds[1:]))
    assert bounds[-1] == constants.BACKOFF_MAX_S
    # 2.0 * 2**7 = 256 <= 300; 2.0 * 2**8 = 512 -> capped.
    assert SdmRateLimiter.backoff_bound_s(7) == 256.0
    assert SdmRateLimiter.backoff_bound_s(8) == constants.BACKOFF_MAX_S
    # negative control: absurd / negative attempts do not overflow or go backwards
    assert SdmRateLimiter.backoff_bound_s(-5) == constants.BACKOFF_BASE_S
    assert SdmRateLimiter.backoff_bound_s(10**6) == constants.BACKOFF_MAX_S


# 17. full jitter: sleep ~ U(0, bound), deterministic under a seeded rng
def test_penalize_is_full_jitter_and_deterministic():
    def deadlines(seed: int) -> list[float]:
        lim = SdmRateLimiter(rng=random.Random(seed))
        out = []
        for attempt in range(12):
            out.append(
                lim.penalize(
                    constants.METHOD_DEVICES_GET,
                    device_id=CAMERAS[0],
                    device_type=constants.TYPE_CAMERA,
                    now=1000.0 * attempt,
                    attempt=attempt,
                )
            )
        return out

    a, b = deadlines(85), deadlines(85)
    assert a == b  # NB-3: same seed, same result
    assert deadlines(86) != a  # a different seed really does move the jitter

    # Reproduce the documented formula independently from the same seeded stream.
    rng = random.Random(85)
    expected = [
        1000.0 * attempt + rng.uniform(0.0, min(constants.BACKOFF_MAX_S, constants.BACKOFF_BASE_S * 2**attempt))
        for attempt in range(12)
    ]
    assert a == pytest.approx(expected, abs=EPS)
    for attempt, until in enumerate(a):
        assert 0.0 <= until - 1000.0 * attempt <= SdmRateLimiter.backoff_bound_s(attempt)


# 18. a penalty blocks the whole shape until its deadline, and never shortens
def test_penalize_blocks_until_deadline_and_only_extends():
    lim = SdmRateLimiter(rng=random.Random(85))
    kw = {"device_id": CAMERAS[0], "device_type": constants.TYPE_CAMERA}
    until = lim.penalize(constants.METHOD_DEVICES_GET, now=0.0, attempt=9, **kw)
    assert until > 0.0
    assert lim.try_acquire(constants.METHOD_DEVICES_GET, now=until - 0.001, **kw) is False
    assert lim.next_allowed_at(constants.METHOD_DEVICES_GET, now=0.0, **kw) == pytest.approx(
        until, abs=EPS
    )
    # A later, smaller penalty must not pull the deadline in.
    shorter = lim.penalize(constants.METHOD_DEVICES_GET, now=0.0, attempt=0, **kw)
    assert shorter <= until
    assert lim.penalty_until(constants.METHOD_DEVICES_GET, **kw) == pytest.approx(until, abs=EPS)
    assert lim.try_acquire(constants.METHOD_DEVICES_GET, now=until, **kw) is True


# --------------------------------------------------------------------------- #
# (2) SIMULATION over >2 simulated hours + (3) independent recomputation.
# --------------------------------------------------------------------------- #


def simulate_fleet(
    seed: int, horizon_s: float = SIM_HORIZON_S
) -> tuple[SdmRateLimiter, list[tuple[float, str, str | None]]]:
    """Drive a realistic fleet on a simulated clock, greedily, and return the call log.

    Fleet: one continuous ``devices.list`` stream plus three cameras polled with
    ``devices.get``, every caller asking for a call the instant the limiter permits one.
    ``RESOURCE_EXHAUSTED`` responses are injected at :data:`PENALTY_EVENTS`. No wall
    clock, no sleeps: time only advances to the limiter's own next-allowed instant.
    """
    lim = SdmRateLimiter(rng=random.Random(seed))
    shapes: list[tuple[str, str | None]] = [(constants.METHOD_DEVICES_LIST, None)]
    shapes += [(constants.METHOD_DEVICES_GET, dev) for dev in CAMERAS]
    pending = list(PENALTY_EVENTS)
    log: list[tuple[float, str, str | None]] = []
    now = 0.0
    for _ in range(200_000):
        if now > horizon_s:
            break
        due = min(
            lim.next_allowed_at(
                method,
                device_id=dev,
                device_type=constants.TYPE_CAMERA if dev else None,
                now=now,
            )
            for method, dev in shapes
        )
        if pending and pending[0][0] <= due:
            at, attempt = pending.pop(0)
            now = max(now, at)
            lim.penalize(
                constants.METHOD_DEVICES_GET,
                device_id=CAMERAS[0],
                device_type=constants.TYPE_CAMERA,
                now=now,
                attempt=attempt,
            )
            continue
        now = due
        if now > horizon_s:
            break
        for method, dev in shapes:
            if lim.try_acquire(
                method,
                device_id=dev,
                device_type=constants.TYPE_CAMERA if dev else None,
                now=now,
            ):
                log.append((now, method, dev))
    else:  # pragma: no cover - guards a non-advancing scheduler
        pytest.fail("simulation did not reach the horizon: the limiter is not advancing")
    return lim, log


# 19. the simulated fleet never exceeds a documented quota, audited from the log alone
def test_simulated_fleet_never_exceeds_documented_quotas():
    _lim, log = simulate_fleet(seed=85)
    assert log and log[-1][0] > 2 * 3600.0, "simulation must cover more than two hours"

    # --- (3) INDEPENDENT RECOMPUTATION: only `log` is read from here down. ---
    list_times = [t for t, m, _ in log if m == constants.METHOD_DEVICES_LIST]
    get_times = [t for t, m, _ in log if m == constants.METHOD_DEVICES_GET]

    assert max_calls_in_window(list_times, 60.0) <= DOC_LIST_QPM
    assert max_calls_in_window(get_times, 60.0) <= DOC_GET_QPM

    for dev in CAMERAS:
        per_device = [t for t, _m, d in log if d == dev]
        assert per_device, f"camera {dev} was never polled"
        assert max_calls_in_window(per_device, 60.0) <= DOC_CAMERA_QPM
        assert max_calls_in_window(per_device, 3600.0) <= DOC_CAMERA_QPH
        # NB-2: consecutive calls of one shape never closer than the derived floor.
        assert min(spacings(per_device)) >= constants.DEFAULT_CAMERA_CADENCE_S - EPS

    assert min(spacings(list_times)) >= constants.DEFAULT_LIST_CADENCE_S - EPS

    # Every call in the log, replayed into fresh buckets, is also accepted as legal by a
    # limiter that has never seen it — the log is reproducible, not an artefact of state.
    replay = {
        "list": QuotaBucket("method:devices.list", DOC_LIST_QPM),
        "get": QuotaBucket("method:devices.get", DOC_GET_QPM),
    }
    for t in list_times:
        assert replay["list"].next_allowed_at(t) <= t + EPS
        replay["list"].record(t)
    for t in get_times:
        assert replay["get"].next_allowed_at(t) <= t + EPS
        replay["get"].record(t)


# 20. the fleet is CONTINUOUS, not bursty: the streams keep running for the whole run
def test_simulated_fleet_is_continuous_not_bursty():
    _lim, log = simulate_fleet(seed=85)
    horizon = log[-1][0]

    list_times = [t for t, m, _ in log if m == constants.METHOD_DEVICES_LIST]
    # 12.0 s floor over >2 h; allow slack for the boundary, never for a burst.
    assert len(list_times) >= int(horizon / constants.DEFAULT_LIST_CADENCE_S) - 2
    assert max(spacings(list_times)) <= constants.DEFAULT_LIST_CADENCE_S + EPS

    for dev in CAMERAS:
        per_device = [t for t, _m, d in log if d == dev]
        # Two hours at 36 s is 200 polls; the injected backoffs cost some of them.
        assert len(per_device) >= 150
        # The only gap longer than the floor is a backoff, which is capped.
        worst = max(spacings(per_device))
        assert worst <= constants.BACKOFF_MAX_S + constants.DEFAULT_CAMERA_CADENCE_S + EPS


# 21. NB-3 determinism: same seed, byte-identical call log
def test_simulation_is_deterministic_under_a_seeded_rng():
    _l1, log_a = simulate_fleet(seed=85)
    _l2, log_b = simulate_fleet(seed=85)
    assert log_a == log_b
    _l3, log_c = simulate_fleet(seed=86)
    assert log_c != log_a  # jitter differs, so the post-backoff phase differs
    assert all(math.isfinite(t) for t, _m, _d in log_a)


# --------------------------------------------------------------------------- #
# Telemetry surface — no site PII.
# --------------------------------------------------------------------------- #


# 22. negative control: no raw SDM device id ever reaches snapshot()
def test_snapshot_never_exposes_a_raw_device_id():
    lim, _log = simulate_fleet(seed=85, horizon_s=600.0)
    snap = lim.snapshot(600.0)
    blob = repr(snap)
    for dev in CAMERAS:
        assert dev not in blob, "raw SDM device id leaked into the health snapshot"
    assert f"method:{constants.METHOD_DEVICES_LIST}" in snap["buckets"]
    for key, entry in snap["buckets"].items():
        kind, _, ident = key.partition(":")
        if kind in ("device", "command"):
            assert len(ident) == 12 and all(c in "0123456789abcdef" for c in ident)
        assert set(entry) == {"qpm", "qph", "minIntervalS", "remaining", "nextAllowedAt", "held"}
    assert snap["listFloorS"] == constants.DEFAULT_LIST_CADENCE_S
    assert snap["cameraFloorS"] == constants.DEFAULT_CAMERA_CADENCE_S


# 23. bucket_ref is stable, hex, and does not pass an id through
def test_bucket_ref_hashes_only_device_identifiers():
    ref = bucket_ref("device:device-id")
    assert ref.startswith("device:") and "device-id" not in ref.partition(":")[2]
    assert ref == bucket_ref("device:device-id")
    assert bucket_ref("device:device-id-2") != ref
    assert bucket_ref("method:devices.list") == "method:devices.list"
    assert bucket_ref("weird") == "weird"


# 24. module stays stdlib-only and import-safe (no google-*, no numpy/scipy)
def test_module_is_stdlib_only():
    src = (
        PKG_ROOT / "iot_asp_autoroute" / "nest" / "rate_limit.py"
    ).read_text(encoding="utf-8")
    for banned in ("import numpy", "import scipy", "from google", "import google", "import requests"):
        assert banned not in src
    assert "time.sleep" not in src and "time.time" not in src and "time.monotonic" not in src
