"""Watch target must not share iOS PBXBuildFile IDs (Xcode duplicate-produce)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBX = ROOT / "native/IoTASP/IoTASP.xcodeproj/project.pbxproj"
WATCH_PLIST = ROOT / "native/IoTASP/IoTASPWatch/Info.plist"

PHASE_RE = re.compile(
    r"A4000000000000000000000(?P<n>[12]) /\* Sources \*/ = \{.*?"
    r"files = \(\s*(?P<body>.*?)\s*\);",
    re.S,
)
ID_RE = re.compile(r"^\s*([A-F0-9]{24}) ", re.M)


def _phase_ids() -> dict[str, set[str]]:
    text = PBX.read_text(encoding="utf-8")
    found = {m.group("n"): set(ID_RE.findall(m.group("body"))) for m in PHASE_RE.finditer(text)}
    assert found.keys() >= {"1", "2"}, found.keys()
    return found


def test_watch_is_modern_application_not_watchapp2():
    text = PBX.read_text(encoding="utf-8")
    assert "com.apple.product-type.application.watchapp2" not in text
    assert 'productType = "com.apple.product-type.application"' in text
    plist = WATCH_PLIST.read_text(encoding="utf-8")
    assert "<key>WKApplication</key>" in plist
    assert "<true/>" in plist


def test_watch_sources_do_not_reuse_ios_build_file_ids():
    phases = _phase_ids()
    ios, watch = phases["1"], phases["2"]
    assert ios, "iOS Compile Sources empty"
    assert watch, "Watch Compile Sources empty"
    overlap = ios & watch
    assert not overlap, f"shared PBXBuildFile IDs {sorted(overlap)}"


def test_watch_sources_are_watch_ui_plus_alarm_only():
    text = PBX.read_text(encoding="utf-8")
    # Second match is Watch (A400…02).
    matches = list(PHASE_RE.finditer(text))
    body = matches[1].group("body")
    assert "IoTASPWatchApp.swift" in body
    assert "WatchContentView.swift" in body
    assert "WatchSessionModel.swift" in body
    assert "B80000000000000000000030" in body
    assert "B80000000000000000000055" in body
    assert "A80000000000000000000030" not in body
    assert "A80000000000000000000055" not in body
    for name in ("HopTabView.swift", "ASPAudioSession.swift", "IoTASPCommandApp.swift"):
        assert name not in body, name


def test_distinct_module_names():
    text = PBX.read_text(encoding="utf-8")
    assert "PRODUCT_MODULE_NAME = IoTASPApp;" in text
    assert "PRODUCT_MODULE_NAME = IoTASPWatch;" in text
    assert "PRODUCT_MODULE_NAME = IoTASPCommand;" in text
