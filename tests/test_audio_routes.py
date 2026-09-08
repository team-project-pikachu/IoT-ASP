"""#146 audio route matrix."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native/IoTASP/Shared/Audio/AudioRouteMatrix.swift"
SPEC = ROOT / "docs/specs/146-audio-routes.md"


def test_files():
    src = SWIFT.read_text(encoding="utf-8")
    assert "allowBluetoothA2DP" in src
    assert "HFP" in src
    assert "longFormAudio" in src
    text = SPEC.read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in text, h
