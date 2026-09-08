"""#4 native physical vib channel."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native/IoTASP/Shared/Sensors/PhysicalVibChannel.swift"
SPEC = ROOT / "docs/specs/04-physical-vib-native.md"


def test_files():
    assert SWIFT.is_file() and SPEC.is_file()
    src = SWIFT.read_text(encoding="utf-8")
    assert "debounceMs: Double = 300" in src
    assert "shakeMultiple: Double = 3" in src
    assert "reseedEvery: Int = 4" in src
    assert "armed" in src
    text = SPEC.read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in text, h
