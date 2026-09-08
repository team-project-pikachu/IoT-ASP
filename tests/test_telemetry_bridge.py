"""#147 native telemetry/patch bridge."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/native_telemetry.json"
SWIFT = ROOT / "native/IoTASP/Shared/Wire/TelemetryBridge.swift"
SPEC = ROOT / "docs/specs/147-telemetry-bridge.md"


def test_fixture_required_fields():
    data = json.loads(FIX.read_text(encoding="utf-8"))
    for k in ["schemaVersion", "deviceId", "ts", "algo", "suddenFreq"]:
        assert k in data
    assert data["schemaVersion"] == 1
    assert data["band"] == "17-23k"
    assert data["power"] == "ac120"


def test_bridge_no_secrets():
    src = SWIFT.read_text(encoding="utf-8")
    assert "GEMINI" not in src and "VERTEX" not in src and "API_KEY" not in src
    assert "shouldPost" in src
    text = SPEC.read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in text, h
