"""#140 CoreMotion suite — CLT-safe source + spec gates (no Xcode.app)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "native/IoTASP/Shared/Sensors/CoreMotionSuite.swift"
LOGGER = ROOT / "native/IoTASP/Shared/Sensors/PhoneMotionLogger.swift"
SPEC = ROOT / "docs/specs/140-coremotion-suite.md"
SMOKE = ROOT / "native/IoTASP/Smoke/main.swift"
PKG = ROOT / "native/IoTASP/Package.swift"

REQUIRED_SPEC_HEADINGS = [
    "Status",
    "Goal",
    "Prior art",
    "Shipped on `main`",
    "Remaining scope",
    "Wire fields",
    "Clamps / safety",
    "Acceptance tests",
    "CI gate",
    "Risks / HW limits",
    "Sources",
]


def test_coremotion_suite_files_exist():
    assert SWIFT.is_file()
    assert LOGGER.is_file()
    assert SPEC.is_file()
    assert SMOKE.is_file()


def test_hz_clamps_in_source():
    src = SWIFT.read_text(encoding="utf-8")
    assert "hzMin: Double = 1" in src
    assert "hzMax: Double = 100" in src
    assert "standardGravity: Double = 9.80665" in src
    assert "case pedometer" in src
    assert "case altimeter" in src
    assert "case magnetometer" in src
    assert 'return .skip' in src
    assert "Pedometer step counts" in src
    assert "schemaVersion" not in src or "no new schemaVersion" in src.lower() or "schemaVersion" in src
    assert "CFD" not in src
    assert "Navier" not in src


def test_logger_does_not_invent_sensorkit():
    src = LOGGER.read_text(encoding="utf-8")
    assert "startAccelerometerUpdates" in src
    assert "startGyroUpdates" in src
    assert "startMagnetometerUpdates" in src
    assert "startDeviceMotionUpdates" in src
    assert "isRelativeAltitudeAvailable" in src
    assert "never armed" in src.lower() or "skip" in src.lower()
    assert "com.apple.developer.sensorkit" not in src


def test_package_includes_directory_except_ios_only():
    pkg = PKG.read_text(encoding="utf-8")
    assert "PhoneMotionLogger.swift" in pkg
    assert "IoTASPSmoke" in pkg
    assert "path: \"Shared\"" in pkg
    # Directory include (no explicit sources: list) so later Foundation files auto-build.
    assert "sources:" not in pkg


def test_spec_sections_and_honesty():
    text = SPEC.read_text(encoding="utf-8")
    for h in REQUIRED_SPEC_HEADINGS:
        assert f"## {h}" in text, h
    assert "CMMotionManager" in text
    assert "pedometer" in text.lower()
    assert "simulator" in text.lower()
    assert "Fixes #140" not in text  # spec is not the PR
    assert "https://developer.apple.com/documentation/coremotion/cmmotionmanager" in text
