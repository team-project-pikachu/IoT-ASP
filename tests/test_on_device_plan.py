"""#151 on-device verification plan exists."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/ios-on-device-verification.md"


def test_plan():
    text = DOC.read_text(encoding="utf-8")
    for needle in ["48 kHz", "CoreMotion", "Soundcore", "schemaVersion 1", "Backgrounding", "SensorKit"]:
        assert needle in text, needle
    spec = (ROOT / "docs/specs/151-on-device-verification.md").read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
