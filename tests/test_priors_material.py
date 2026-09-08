"""Material-channel bias + suddenFreq patch (#4/#6 acceptance).

stdlib + package imports only; no network.
Spec: docs/specs/04-06-vibration-channels.md acceptance 6–8.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADK = ROOT / "services" / "autoroute-adk"
sys.path.insert(0, str(ADK))

from iot_asp_autoroute import priors as pr  # noqa: E402
from iot_asp_autoroute import sudden_freq as sf  # noqa: E402


def test_vib_algo_weights_chair_and_unknown_preset() -> None:
    chair = pr.vib_algo_weights("physical", "chair")
    assert abs(chair["burst"] - 0.40 * 1.3) < 1e-9
    granite = pr.vib_algo_weights("physical", "granite")
    assert granite == pr.VIB_ALGO_WEIGHTS["physical"]


def test_preferred_and_next_algo_speaker_acoustic() -> None:
    pref = pr.preferred_algos("acoustic", "speaker")
    assert pref[0] == "am_gate"
    assert "hop" in pref
    hop_i = pref.index("hop")
    assert pr.next_algo_weighted("hop", "acoustic", "speaker") == pref[(hop_i + 1) % len(pref)]
    assert pr.next_algo_weighted("am_gate", "acoustic", "speaker") == pref[1]


def test_author_sudden_freq_echoes_material_and_hold() -> None:
    ok, msg, patch = sf.author_sudden_freq_patch(
        {
            "deviceId": "node1",
            "materialPreset": "table",
            "vibClass": "physical",
            "suddenFreq": True,
            "algo": "hop",
            "vol": 100,
        }
    )
    assert ok, msg
    assert patch.get("materialPreset") == "table"
    ok_h, msg_h, patch_h = sf.author_sudden_freq_patch(
        {
            "deviceId": "node1",
            "holdManual": True,
            "materialPreset": "table",
            "vibClass": "physical",
            "suddenFreq": True,
        }
    )
    assert not ok_h
    assert "holdManual" in msg_h
    assert patch_h == {}
