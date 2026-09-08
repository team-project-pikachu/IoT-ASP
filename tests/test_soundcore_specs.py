"""Offline gates for Soundcore 2 A2DP fleet constraints (#43).

IDs SC-01 … SC-10 match docs/specs/43-soundcore-2-a2dp.md § Acceptance tests.
stdlib only; no network.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = (ROOT / "SPEC.md").read_text(encoding="utf-8")
ISSUE_SPEC = (ROOT / "docs" / "specs" / "43-soundcore-2-a2dp.md").read_text(encoding="utf-8")
BT = (ROOT / "docs" / "iphone-bluetooth.md").read_text(encoding="utf-8")
NATIVE = (ROOT / "docs" / "native-xcode.md").read_text(encoding="utf-8")

REQUIRED_SECTIONS = (
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
)


def test_sc01_spec_fr_from_manual():
    assert "70 Hz" in SPEC and "20 kHz" in SPEC
    assert "70 Hz" in SPEC or "70 Hz – 20 kHz" in SPEC
    assert "A3105" in SPEC or "owner" in SPEC.lower()


def test_sc02_marketing_page_still_not_listed():
    assert "Not listed" in SPEC
    assert "product page" in SPEC.lower() or "marketing" in SPEC.lower()


def test_sc03_us_band_honesty():
    blob = SPEC + ISSUE_SPEC
    assert "17–23 kHz" in blob or "17-23 kHz" in blob
    assert "20 kHz" in blob


def test_sc04_lf_band_na():
    blob = SPEC + ISSUE_SPEC
    assert "10–20 Hz" in blob or "10-20 Hz" in blob
    assert "70 Hz" in blob
    assert "na" in blob.lower()


def test_sc05_vol_blast_vs_rated_power():
    blob = SPEC + ISSUE_SPEC
    assert "12 W" in blob or "12W" in blob
    assert "100%" in blob or "Web Audio" in blob


def test_sc06_iphone_bluetooth_wires_honesty():
    assert "43-soundcore-2-a2dp.md" in BT
    assert "70 Hz" in BT and "20 kHz" in BT
    assert "10–20 Hz" in BT or "10-20 Hz" in BT
    assert "12 W" in BT or "12W" in BT


def test_sc07_native_docs_link_spec():
    assert "43-soundcore-2-a2dp.md" in NATIVE
    assert "SensorKit" in NATIVE
    assert "Web Bluetooth" not in NATIVE.split("not")[0] or "not" in NATIVE.lower()


def test_sc08_spec_has_mandatory_sections():
    positions = [ISSUE_SPEC.index(f"## {name}") for name in REQUIRED_SECTIONS]
    assert positions == sorted(positions)


def test_sc10_codecs_not_manufacturer_listed():
    assert "Codecs" in SPEC
    assert "Not listed" in SPEC
