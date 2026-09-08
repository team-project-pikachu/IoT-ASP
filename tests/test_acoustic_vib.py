"""#5 native acoustic vib channel."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native/IoTASP/Shared/Sensors/AcousticVibChannel.swift"
SPEC = ROOT / "docs/specs/05-acoustic-vib-native.md"


def test_files():
    src = SWIFT.read_text(encoding="utf-8")
    assert "burstMarginDb: Double = 12" in src
    assert "micDiffDb" in src
    text = SPEC.read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in text, h
