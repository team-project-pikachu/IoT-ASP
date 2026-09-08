"""Command center is Vercel (or the macOS WKWebView of that URL). iPhone is a node."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "native/IoTASP/Shared/Product/NativeAppShell.swift"
HOP = ROOT / "native/IoTASP/IoTASPApp/Views/HopTabView.swift"
MAC_APP = ROOT / "native/IoTASP/IoTASPCommand/IoTASPCommandApp.swift"
MAC_WEB = ROOT / "native/IoTASP/IoTASPCommand/CommandCenterWebView.swift"
PBX = ROOT / "native/IoTASP/IoTASP.xcodeproj/project.pbxproj"
PROD = "https://hop-ultrasonic-1digital-design.vercel.app/"


def test_canonical_command_center_url():
    src = SHELL.read_text(encoding="utf-8")
    assert PROD in src
    assert "statusLine" in src


def test_macos_wraps_vercel_not_a_second_plane():
    assert MAC_APP.is_file()
    web = MAC_WEB.read_text(encoding="utf-8")
    assert "WKWebView" in web
    app = MAC_APP.read_text(encoding="utf-8")
    assert "CommandCenterWebView" in app
    assert "NativeAppShell.commandCenterURL" in app
    pbx = PBX.read_text(encoding="utf-8")
    assert "SDKROOT = macosx" in pbx
    assert "PRODUCT_MODULE_NAME = IoTASPCommand;" in pbx
    assert "C80000000000000000000055" in pbx
    assert pbx.count("C80000000000000000000055") >= 2


def test_phone_ui_hides_diagnostics():
    hop = HOP.read_text(encoding="utf-8")
    for leak in (
        "vibClass",
        "bandEnergyUs",
        "schemaVersion",
        "SensorKit",
        "telemetry URL",
        "Simulate impulse",
        "materialPreset",
        "|a|",
    ):
        assert leak not in hop, leak
