"""#18 native LF accel felt proxy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native/IoTASP/Shared/Sensors/LfAccelProxy.swift"
SPEC = ROOT / "docs/specs/18-chair-lf-native.md"


def test_files():
    src = SWIFT.read_text(encoding="utf-8")
    assert "infra_felt" in src
    assert "felt proxy" in src
    assert "CFD" not in src
    text = SPEC.read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in text, h
