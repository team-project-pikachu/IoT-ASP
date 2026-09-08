"""#149 device matrix honesty."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/ios-device-capability-matrix.md"


def test_unknown_cells():
    text = DOC.read_text(encoding="utf-8")
    assert "unknown" in text
    assert "SensorKit entitled build" in text
    assert "**no**" in text
    spec = (ROOT / "docs/specs/149-device-matrix.md").read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
