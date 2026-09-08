"""Tests for acoustic vib hop-band energy burst (#5).

Parity with public/acoustic-vib-energy.js and docs/specs/04-06-vibration-channels.md
§ Remaining scope item 3. Offline / deterministic.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "services" / "autoroute-adk"
sys.path.insert(0, str(PKG_DIR))

from iot_asp_autoroute import acoustic_vib_energy as ave  # noqa: E402

HTML_PATH = ROOT / "public" / "index.html"
JS_PATH = ROOT / "public" / "acoustic-vib-energy.js"


def test_constants_parity_js_py():
    js = JS_PATH.read_text(encoding="utf-8")
    assert "WINDOW_MS = 1000" in js or "var WINDOW_MS = 1000" in js
    assert "MARGIN_DB = 12" in js or "var MARGIN_DB = 12" in js
    assert ave.WINDOW_MS == 1000
    assert ave.MARGIN_DB == 12.0
    assert ave.SILENCE_DB == -90.0


def test_median_of_odd_even():
    assert ave.median_of([-60, -50, -40]) == -50.0
    assert ave.median_of([-60, -50]) == -55.0
    assert ave.median_of([]) == -120.0


def test_prefer_energy_prefers_mic_diff():
    assert ave.prefer_energy(-40.0, -30.0) == -30.0
    assert ave.prefer_energy(-40.0, -120.0) == -40.0
    assert ave.prefer_energy(-40.0, None) == -40.0
    assert ave.prefer_energy(float("nan"), None) == -120.0


def test_burst_rising_edge_12db():
    tr = ave.create_tracker()
    # Fill 1 s window with quiet baseline
    for i in range(20):
        out = tr.push(-70.0, i * 50)
        assert out["burst"] is False
    # Spike ≥ 12 dB above median
    out = tr.push(-55.0, 1100)  # delta 15 vs -70
    assert out["rising"] is True
    assert out["burst"] is True
    assert out["delta"] >= 12.0


def test_silence_clears_burst():
    tr = ave.create_tracker()
    for i in range(10):
        tr.push(-70.0, i * 50)
    tr.push(-50.0, 600)  # burst
    assert tr.snapshot()["burst"] is True
    # Hold deep silence
    out = None
    for i in range(20):
        out = tr.push(-100.0, 700 + i * 50)
    assert out is not None
    assert out["silence"] is True
    assert out["burst"] is False


def test_html_wires_module_and_banner():
    html = HTML_PATH.read_text(encoding="utf-8")
    assert 'src="/acoustic-vib-energy.js"' in html
    assert "// ══ vib channels (#5)" in html
    assert "tickAcousticVibEnergy" in html
    assert "forceHopFromAcousticBurst" in html
    assert "resetAcousticVibEnergy" in html
    assert "acousticEnergy > -55" not in html  # absolute rule replaced by burst detector
    assert "acousticBurst ? \"acoustic\"" in html or 'acousticBurst ? "acoustic"' in html
    assert html.count("function updateVibClass(cls){") == 1
    body = html[html.index("function updateVibClass(cls){") :]
    body = body[: body.index("\n  }\n")]
    assert 'cls === "acoustic" && !armAcoustic' in body


def test_html_mic_teardown_resets_tracker():
    html = HTML_PATH.read_text(encoding="utf-8")
    assert 'resetAcousticVibEnergy("micStop")' in html
    assert 'resetAcousticVibEnergy("micFail")' in html
    assert re.search(r"echoCancellation\s*:\s*false", html)
    assert "never routed onward" in html or "never routed" in html
