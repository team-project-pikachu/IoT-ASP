"""#141 near-ultrasonic mic contract — source/spec gates."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METER = ROOT / "native/IoTASP/Shared/Audio/UltrasonicMicMeter.swift"
CAP = ROOT / "native/IoTASP/Shared/Audio/UltrasonicMicCapture.swift"
PKG = ROOT / "native/IoTASP/Package.swift"
SPEC = ROOT / "docs/specs/141-ultrasonic-mic.md"

HEADINGS = [
    "Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
    "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
    "Risks / HW limits", "Sources",
]


def test_files():
    assert METER.is_file() and CAP.is_file() and SPEC.is_file()


def test_meter_constants():
    src = METER.read_text(encoding="utf-8")
    assert "preferredSampleRate: Double = 48_000" in src
    assert "17_000" in src and "23_000" in src
    assert "micDiffAlpha: Double = 0.85" in src
    assert "preferEchoCancellationOff = true" in src
    assert "CFD" not in src


def test_capture_measurement_mode_and_remove_tap():
    src = CAP.read_text(encoding="utf-8")
    assert ".measurement" in src
    assert "removeTap" in src
    assert "setPreferredSampleRate" in src
    assert "mode: .measurement" in src
    assert ".voiceChat" not in src.replace("not use .voiceChat", "")


def test_spm_excludes_capture():
    assert "UltrasonicMicCapture.swift" in PKG.read_text(encoding="utf-8")


def test_spec():
    text = SPEC.read_text(encoding="utf-8")
    for h in HEADINGS:
        assert f"## {h}" in text, h
    assert "48000" in text or "48 kHz" in text
    assert "https://developer.apple.com/documentation/avfaudio/avaudioengine" in text
