"""#25 native AEC honesty — issue stays open."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_false_flags():
    src = (ROOT / "native/IoTASP/Shared/Audio/NativeAECHonesty.swift").read_text(encoding="utf-8")
    assert "fullAEC = false" in src
    assert "lfMic = false" in src
    spec = (ROOT / "docs/specs/25-native-aec-honesty.md").read_text(encoding="utf-8")
    assert "do not close" in spec.lower()
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
