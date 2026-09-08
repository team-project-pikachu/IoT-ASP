"""Native iOS app chrome — tabs, Arm sensors, background pause."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "native/IoTASP/Shared/Product/NativeAppShell.swift"
CONTENT = ROOT / "native/IoTASP/IoTASPApp/Views/ContentView.swift"
HOP = ROOT / "native/IoTASP/IoTASPApp/Views/HopTabView.swift"
APP = ROOT / "native/IoTASP/IoTASPApp/IoTASPApp.swift"
SESSION = ROOT / "native/IoTASP/IoTASPApp/Services/ASPSessionModel.swift"


def test_files():
    for p in (SHELL, CONTENT, HOP, APP, SESSION):
        assert p.is_file(), p


def test_four_tabs():
    src = SHELL.read_text(encoding="utf-8")
    for name in ("hop", "nestAlarm", "glassShatter", "systems"):
        assert f"case {name}" in src
    ui = CONTENT.read_text(encoding="utf-8")
    assert "TabView" in ui
    assert "HopTabView" in ui
    assert "NestAlarmTabView" in ui
    assert "GlassShatterTabView" in ui
    assert "SystemsCheckView" in ui


def test_arm_sensors_and_background():
    sess = SESSION.read_text(encoding="utf-8")
    assert "func armSensors()" in sess
    assert "func disarmSensors()" in sess
    assert "handleScenePhaseActive" in sess
    assert "emitHeartbeat" in sess
    assert "shouldPost" in sess
    hop = HOP.read_text(encoding="utf-8")
    assert "Arm sensors" in hop
    assert "Hold / Manual" in hop


def test_scene_phase_wired():
    app = APP.read_text(encoding="utf-8")
    assert "scenePhase" in app
    assert "handleScenePhaseActive" in app


def test_no_nest_tokens():
    nest = (ROOT / "native/IoTASP/IoTASPApp/Views/NestAlarmTabView.swift").read_text(encoding="utf-8")
    assert "parked" in nest.lower()
    assert "client ID" in nest or "tokens" in nest.lower()
