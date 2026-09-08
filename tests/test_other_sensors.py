"""#142 other sensors honesty."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_fake_lux():
    src = (ROOT / "native/IoTASP/Shared/Sensors/OtherSensorsGate.swift").read_text(encoding="utf-8")
    assert "ambientLux() -> Double? { nil }" in src
    doc = (ROOT / "docs/ios-sensor-availability.md").read_text(encoding="utf-8")
    assert "no fake lux" in doc.lower()
    spec = (ROOT / "docs/specs/142-other-sensors.md").read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
