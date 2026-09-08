"""#6 native material channel policy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native/IoTASP/Shared/Sensors/VibChannelPolicy.swift"
SPEC = ROOT / "docs/specs/06-material-channel-native.md"


def test_files():
    src = SWIFT.read_text(encoding="utf-8")
    assert "case handheld" in src and "case table" in src and "case chair" in src and "case speaker" in src
    text = SPEC.read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in text, h
