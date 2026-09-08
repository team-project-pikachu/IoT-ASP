"""Behavioral twins of native vib / mic / policy (CLT + ubuntu). Mirrors IoTASPSmoke."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/native_telemetry.json"


def clamp_hz(hz: float) -> float:
    if hz != hz or math.isinf(hz):
        return 50.0
    return min(100.0, max(1.0, hz))


def mic_diff(mic: float, out: float, alpha: float = 0.85) -> float:
    return round(mic - alpha * out, 3)


def us_nyquist_ok(sr: float) -> bool:
    return sr / 2.0 >= 23000


class PhysicalVib:
    def __init__(self, thr=0.1, debounce_ms=300, shake_mult=3, window_ms=400, reseed_every=4):
        self.thr = thr
        self.debounce_ms = debounce_ms
        self.shake_thr = thr * shake_mult
        self.window_ms = window_ms
        self.reseed_every = reseed_every
        self.last_emit = None
        self.candidate = None
        self.shake_count = 0

    def observe(self, abs_a, now_s, armed=True):
        if not armed:
            return "none"
        if abs_a >= self.shake_thr:
            if self.candidate is not None and (now_s - self.candidate) * 1000 <= self.window_ms:
                self.candidate = None
                if self._debounce_ok(now_s):
                    self.shake_count += 1
                    self.last_emit = now_s
                    return "shakeReseed" if self.shake_count % self.reseed_every == 0 else "shakeHop"
            else:
                self.candidate = now_s
                return "none"
        if abs_a >= self.thr and self._debounce_ok(now_s):
            self.last_emit = now_s
            return "physical"
        return "none"

    def _debounce_ok(self, now_s):
        return self.last_emit is None or (now_s - self.last_emit) * 1000 >= self.debounce_ms


def median(xs):
    if not xs:
        return -120
    s = sorted(xs)
    m = len(s) // 2
    if len(s) % 2 == 0:
        return (s[m - 1] + s[m]) / 2
    return s[m]


def test_clamp_hz():
    assert clamp_hz(0.1) == 1.0
    assert clamp_hz(400) == 100.0


def test_mic_diff_and_nyquist():
    assert mic_diff(-20, -30) == 5.5
    assert us_nyquist_ok(48000)
    assert not us_nyquist_ok(44100)


def test_physical_shake_hop():
    ch = PhysicalVib()
    assert ch.observe(0.05, 0.0) == "none"
    assert ch.observe(0.15, 0.0) == "physical"
    assert ch.observe(0.15, 0.1) == "none"
    assert ch.observe(0.4, 0.4) == "none"
    assert ch.observe(0.4, 0.45) == "shakeHop"
    assert ch.observe(2.0, 3.0, armed=False) == "none"


def test_acoustic_burst_vs_median():
    window = [-60] * 5
    assert median([-10, -20, -30]) == -20
    assert (-20) - median(window) >= 12


def test_material_arming():
    table = {"physical": True, "acoustic": False}
    speaker = {"physical": True, "acoustic": True}
    handheld = {"physical": False, "acoustic": True}
    chair = {"physical": True, "acoustic": False}
    assert table["acoustic"] is False
    assert speaker["physical"] and speaker["acoustic"]
    assert handheld["acoustic"] and not handheld["physical"]
    assert chair == table


def test_telemetry_fixture():
    data = json.loads(FIX.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    for k in ("deviceId", "ts", "algo", "suddenFreq"):
        assert k in data
    assert data["band"] == "17-23k"
    assert data["power"] == "ac120"


def test_swift_sources_present():
    shared = ROOT / "native/IoTASP/Shared"
    for rel in [
        "Sensors/PhysicalVibChannel.swift",
        "Sensors/AcousticVibChannel.swift",
        "Sensors/VibChannelPolicy.swift",
        "Audio/UltrasonicMicMeter.swift",
        "Wire/TelemetryBridge.swift",
    ]:
        assert (shared / rel).is_file(), rel
