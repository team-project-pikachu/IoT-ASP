"""Material → vib channel selection (#6).

Verification matrix: table→physical, speaker(+no motion)→acoustic, handheld→both.
Also asserts JS mirror stays in parity with Python.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADK = ROOT / "services" / "autoroute-adk"
sys.path.insert(0, str(ADK))

from iot_asp_autoroute import vib_channel_select as vcs  # noqa: E402
from iot_asp_autoroute import priors as pr  # noqa: E402


def test_selection_matrix_physical_acoustic_both() -> None:
    table = vcs.select_channels("table")
    assert table.mode == "physical"
    assert table.arm_physical and not table.arm_acoustic
    assert table.prefer == "physical"

    handheld = vcs.select_channels("handheld")
    assert handheld.mode == "both"
    assert handheld.arm_physical and handheld.arm_acoustic
    assert handheld.prefer == "acoustic"

    # speaker prefers acoustic; BT radiate / motion denied → acoustic-only
    speaker = vcs.select_channels("speaker", physical_available=False)
    assert speaker.mode == "acoustic"
    assert not speaker.arm_physical and speaker.arm_acoustic
    assert speaker.prefer == "acoustic"
    assert speaker.fallback_reason and "physical_unavailable" in speaker.fallback_reason


def test_chair_physical_and_unknown_preset() -> None:
    chair = vcs.select_channels("chair")
    assert chair.mode == "physical"
    assert chair.arm_physical and not chair.arm_acoustic
    assert vcs.normalize_material_preset("granite") == "handheld"
    assert vcs.select_channels("granite").material_preset == "handheld"


def test_allows_vib_class_gates() -> None:
    sel = vcs.select_channels("table")
    assert sel.allows_vib_class("physical")
    assert sel.allows_vib_class("infra_felt")
    assert not sel.allows_vib_class("acoustic")
    assert sel.allows_vib_class("none")


def test_fallback_to_none_when_both_unavailable() -> None:
    sel = vcs.select_channels(
        "handheld", physical_available=False, acoustic_available=False
    )
    assert sel.mode == "none"
    assert not sel.arm_physical and not sel.arm_acoustic


def test_js_mirror_parity() -> None:
    js = (ROOT / "public" / "vib-channel-select.js").read_text(encoding="utf-8")
    for preset in vcs.MATERIAL_PRESETS:
        assert f"{preset}:" in js or f"{preset} :" in js
        py = vcs.MATERIAL_CHANNEL_SELECT[preset]
        # crude: armPhysical / armAcoustic literals must appear near preset
        assert "armPhysical" in js and "armAcoustic" in js
        assert str(py["armPhysical"]).lower() in js
        assert str(py["armAcoustic"]).lower() in js
    assert "selectChannels" in js
    assert "allowsVibClass" in js
    assert "IotAspVibChannelSelect" in js


def test_seismo_bundle_includes_select() -> None:
    bundle = pr.seismo_bundle()
    assert "materialChannelSelect" in bundle
    assert bundle["materialChannelSelect"]["presets"] == list(vcs.MATERIAL_PRESETS)


def test_public_html_emits_material_preset() -> None:
    html = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
    assert 'id="materialPreset"' in html
    for opt in ("handheld", "table", "chair", "speaker"):
        assert f'value="{opt}"' in html
    assert "vib-channel-select.js" in html
    assert "function refreshChannelArms()" in html
    assert "function setMaterialPreset(" in html
    assert re.search(r"materialPreset,?$", html, re.M) or "materialPreset," in html
    # Gate hooks for #4/#5
    assert "armPhysical" in html and "armAcoustic" in html
    assert "!armPhysical" in html and "!armAcoustic" in html
