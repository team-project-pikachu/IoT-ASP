"""Nest sound burst → reactive patch (#88 #96 #103 #45).

Covers the bridge that closes the loop from a Nest acoustic event to a louder alarm
the PWA hot-applies within one patch poll. Negative controls are the point of this
file: Hold/Manual, clamp enforcement after escalation, single-witness restraint, and
that nothing here writes meta/patches/ on its own.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "autoroute-adk"))

from iot_asp_autoroute.clamps import CLAMPS, SCHEMA_VERSION, validate_patch  # noqa: E402
from iot_asp_autoroute.nest import detector as nd  # noqa: E402
from iot_asp_autoroute.nest import reactive as nr  # noqa: E402


def corroborated_tel(**over):
    """Nest sound event AND a strong phone-side onset — two witnesses."""
    tel = {
        "schemaVersion": 1,
        "deviceId": "node1",
        "nestEvent": "sound",
        "nestDeviceType": "sdm.devices.types.CAMERA",
        "nestDeviceRef": "274bc121c3df",
        "soundBurst": True,
        "extremeActive": True,
        "micDiff": 15.0,
        "bandBurst": "us",
        "nestLagS": 1.0,
        "algo": "hop",
        "vol": 60,
    }
    tel.update(over)
    return tel


# ── RE-01 the happy path escalates ───────────────────────────────────────────


def test_re01_corroborated_burst_escalates_and_blasts():
    ok, msg, patch = nr.author_nest_burst_patch(corroborated_tel())
    assert ok, msg
    assert patch["alarmState"] == "triggered"
    assert patch["volBlast"] is True
    assert patch["algo"] == "shriek_chirp", "a burst must bias toward the shriek algo"
    assert patch["vol"] == 100.0
    assert patch["nestBurstCorroborated"] is True
    assert patch["schemaVersion"] == SCHEMA_VERSION


# ── RE-02 Hold / Manual wins, at BOTH gates ──────────────────────────────────


def test_re02_hold_manual_refuses_authoring():
    ok, msg, patch = nr.author_nest_burst_patch(corroborated_tel(holdManual=True))
    assert ok is False
    assert "holdManual" in msg
    assert patch == {}


def test_re02b_hold_manual_blocks_escalation_hint_independently():
    """Even a maximal classification yields no hint under Hold — defence in depth."""
    cls = nd.BurstClassification(nd.LABEL_GLASS_SHATTER, 0.99, "x", nd.SOURCE_OFFLINE, corroborated=True)
    assert nd.escalation_hint(cls, hold_manual=True) == {}
    assert nd.escalation_hint(cls, hold_manual=False)["volBlast"] is True


def test_re02c_react_does_not_write_under_hold():
    calls = []

    def writer(node, payload):  # pragma: no cover - must never run
        calls.append((node, payload))
        return {"ok": True}

    out = nr.react(corroborated_tel(holdManual=True), writer=writer)
    assert out["ok"] is False
    assert out["written"] is False
    assert calls == [], "no write may be attempted while Hold/Manual is set"


# ── RE-03 restraint: one witness escalates, but must not blast ───────────────


def test_re03_single_witness_triggers_without_blast():
    """A Nest sound with no phone corroboration is one witness, not two."""
    tel = {"schemaVersion": 1, "deviceId": "node1", "nestEvent": "sound", "algo": "hop"}
    cls = nr.classify(tel)
    assert cls.corroborated is False
    hint = nd.escalation_hint(cls)
    assert hint == {}, "an uncorroborated low-confidence witness must not escalate at all"


def test_re03b_non_acoustic_event_never_escalates():
    for event in ("motion", "person", "clip_preview", None):
        ok, msg, patch = nr.author_nest_burst_patch(
            {"schemaVersion": 1, "deviceId": "node1", "nestEvent": event}
        )
        assert ok is False, f"{event} must not escalate an alarm"
        assert patch == {}


# ── RE-04 clamps are enforced AFTER escalation, never bypassed ───────────────


def test_re04_escalated_patch_passes_clamps():
    ok, _msg, patch = nr.author_nest_burst_patch(corroborated_tel())
    assert ok
    valid, why, _ = validate_patch(patch)
    assert valid, why


def test_re04b_escalation_cannot_exceed_vol_hard_max():
    ok, _msg, patch = nr.author_nest_burst_patch(corroborated_tel(vol=100))
    assert ok
    assert patch["vol"] <= CLAMPS["vol_hard_max"] == 100.0
    assert CLAMPS["shriekMs"][0] <= patch["shriekMs"] <= CLAMPS["shriekMs"][1]


def test_re04c_out_of_band_seed_is_refused_not_rewritten():
    """A nonsense fMin must be refused by the clamp path, not silently corrected."""
    ok, msg, _patch = nr.author_nest_burst_patch(corroborated_tel(fMin=50, fMax=60, band="17-23k"))
    assert ok is False
    assert "clamp" in msg.lower() or "refused" in msg.lower() or "outside" in msg.lower()


# ── RE-05 react() delegates the write; it never touches meta/patches itself ──


def test_re05_react_writes_through_injected_writer():
    seen = {}

    def writer(node, payload):
        seen["node"] = node
        seen["patch"] = json.loads(payload)
        return {"ok": True, "uri": "file:///dry/meta/patches/node1.json", "patch": seen["patch"]}

    out = nr.react(corroborated_tel(), writer=writer)
    assert out["ok"] is True and out["written"] is True
    assert seen["node"] == "node1"
    assert seen["patch"]["alarmState"] == "triggered"


def test_re05b_reactive_module_never_names_the_patch_path():
    """Authoring must go through tools.write_patch, which owns the Hold re-check.

    Checked over the AST with docstrings removed, not over raw text: the module
    docstring legitimately *describes* where write_patch puts the object, and a naive
    substring scan would flag that prose. What must not exist is a string LITERAL in
    executable code that builds a patch object path.
    """
    import ast

    src = (
        ROOT / "services" / "autoroute-adk" / "iot_asp_autoroute" / "nest" / "reactive.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(src)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                docstrings.add(doc)
    literals = [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value not in docstrings
    ]
    offenders = [lit for lit in literals if "meta/patches" in lit]
    assert not offenders, f"reactive.py must not construct a patch object path: {offenders}"


# ── RE-06 no PII reaches the patch ───────────────────────────────────────────


def test_re06_patch_carries_no_preview_url_or_raw_device_id():
    tel = corroborated_tel(
        nestPreviewUrl="https://SENTINELHOST/clip/SENTINELTOKEN",
        nestRawName="enterprises/SENTINELPROJ/devices/SENTINELDEVICE",
    )
    ok, _msg, patch = nr.author_nest_burst_patch(tel)
    assert ok
    blob = json.dumps(patch)
    for sentinel in ("SENTINELHOST", "SENTINELTOKEN", "SENTINELPROJ", "SENTINELDEVICE"):
        assert sentinel not in blob, f"{sentinel} leaked into the patch"


# ── RE-07 determinism ────────────────────────────────────────────────────────


def test_re07_offline_authoring_is_deterministic():
    a = nr.author_nest_burst_patch(corroborated_tel())[2]
    b = nr.author_nest_burst_patch(corroborated_tel())[2]
    a.pop("authoredAt", None)
    a.pop("createdAt", None)
    b.pop("authoredAt", None)
    b.pop("createdAt", None)
    assert a == b


# ── RE-08 the detector degrades rather than breaking the loop ────────────────


def test_re08_detector_failure_falls_back_offline():
    class Boom(nd.GeminiEnterpriseDetector):
        def classify_strict(self, ev):  # noqa: D102
            raise RuntimeError("engine unreachable")

    cls = nr.classify(corroborated_tel(), detector=Boom(project="p"))
    assert cls.source == nd.SOURCE_OFFLINE
    assert cls.label in nd.LABELS


@pytest.mark.parametrize("event", ["sound", "chime"])
def test_re09_both_acoustic_event_classes_reach_the_burst_path(event):
    ok, msg, patch = nr.author_nest_burst_patch(corroborated_tel(nestEvent=event))
    assert ok, msg
    assert patch["alarmState"] == "triggered"
