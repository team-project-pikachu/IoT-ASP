"""#145 background sensing policy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pause():
    src = (ROOT / "native/IoTASP/Shared/Sensors/BackgroundSensingPolicy.swift").read_text(encoding="utf-8")
    assert "backgroundPaused" in src
    assert "always-on" in src
    spec = (ROOT / "docs/specs/145-background-sensing.md").read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
