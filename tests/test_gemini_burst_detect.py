"""Deterministic tests for services/gemini-burst-detect/detect.py (M8 / #96 wire contract)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DETECT_PATH = ROOT / "services" / "gemini-burst-detect" / "detect.py"


def _load():
    spec = importlib.util.spec_from_file_location("gemini_burst_detect", DETECT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def detect_mod():
    return _load()


def test_cold_below_threshold(detect_mod):
    r = detect_mod.detect({"energyDeltaDb": 3, "riseMs": 20, "eventClassHint": "glass_shatter"})
    d = r.as_dict()
    assert d["burst"] is False
    assert d["eventClass"] == "unknown"
    assert d["escalateDb"] == 0.0
    assert set(d) == {"burst", "eventClass", "confidence", "escalateDb"}


def test_sound_burst_class(detect_mod):
    r = detect_mod.detect({"energyDeltaDb": 12, "riseMs": 150, "eventClassHint": "sound_burst"})
    d = r.as_dict()
    assert d["burst"] is True
    assert d["eventClass"] == "sound_burst"
    assert d["escalateDb"] == 2.0


def test_glass_shatter_class(detect_mod):
    r = detect_mod.detect({"energyDeltaDb": 14, "riseMs": 40, "eventClassHint": "glass_shatter"})
    d = r.as_dict()
    assert d["burst"] is True
    assert d["eventClass"] == "glass_shatter"
    assert d["escalateDb"] == 4.0


def test_boundary_rise_ms_glass_vs_burst(detect_mod):
    glass = detect_mod.detect({"energyDeltaDb": 14, "riseMs": 80, "eventClassHint": "glass_shatter"}).as_dict()
    burst = detect_mod.detect({"energyDeltaDb": 14, "riseMs": 81, "eventClassHint": "glass_shatter"}).as_dict()
    assert glass["eventClass"] == "glass_shatter"
    assert burst["eventClass"] == "sound_burst"


def test_snake_case_aliases(detect_mod):
    r = detect_mod.detect(
        {"energy_delta_db": 14, "rise_ms": 40, "event_class_hint": "glass_shatter"}
    ).as_dict()
    assert r["burst"] is True
    assert r["eventClass"] == "glass_shatter"


def test_zero_rise_ms_is_not_missing(detect_mod):
    # riseMs: 0 must not fall through to default 999 (which would misclassify as sound_burst).
    r = detect_mod.detect({"energyDeltaDb": 14, "riseMs": 0, "eventClassHint": "glass_shatter"}).as_dict()
    assert r["eventClass"] == "glass_shatter"


def test_zero_energy_stays_cold(detect_mod):
    r = detect_mod.detect({"energyDeltaDb": 0, "riseMs": 10}).as_dict()
    assert r["burst"] is False
    assert r["eventClass"] == "unknown"
