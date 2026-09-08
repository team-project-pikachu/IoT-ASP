"""#143 SensorKit reader map."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_map():
    src = (ROOT / "native/IoTASP/Shared/Sensors/SensorKitReaderMap.swift").read_text(encoding="utf-8")
    assert "com.apple.developer.sensorkit.reader.allow" in src
    assert "SRSensorAccelerometer" in src
    assert "requiresAppleGrant: true" in src
    spec = (ROOT / "docs/specs/143-sensorkit-readers.md").read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
