"""#144 permission sequencer + Info.plist copy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native/IoTASP/Shared/Sensors/PermissionSequencer.swift"
PLIST = ROOT / "native/IoTASP/IoTASPApp/Info.plist"
SPEC = ROOT / "docs/specs/144-permission-ux.md"


def test_files():
    assert SWIFT.is_file() and PLIST.is_file() and SPEC.is_file()


def test_sequence_no_ungated_sensorkit():
    src = SWIFT.read_text(encoding="utf-8")
    assert "case microphone" in src and "case motion" in src
    assert "skippedUngated" in src
    assert "sensorkitEntitled" in src
    assert "com.apple.developer.sensorkit.reader.allow" in src


def test_plist_on_device_mic():
    text = PLIST.read_text(encoding="utf-8")
    assert "NSMicrophoneUsageDescription" in text
    assert "on-device" in text
    assert "NSMotionUsageDescription" in text


def test_spec_headings():
    text = SPEC.read_text(encoding="utf-8")
    for h in [
        "Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
        "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
        "Risks / HW limits", "Sources",
    ]:
        assert f"## {h}" in text, h
