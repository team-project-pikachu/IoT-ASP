"""Offline E2E acceptance for glass shatter (#98).

Acceptance IDs GS-01 … GS-07 from docs/specs/98-glass-shatter-e2e.md and
docs/issues/ISSUE-98-glass-shatter-e2e.md.

Deterministic: uses nest.detector offline_classify + escalation_hint only.
No network, no credentials, no real device ids.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "services" / "autoroute-adk"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from iot_asp_autoroute.nest import detector as nd  # noqa: E402

SPEC = ROOT / "docs" / "specs" / "98-glass-shatter-e2e.md"
ISSUE_DOC = ROOT / "docs" / "issues" / "ISSUE-98-glass-shatter-e2e.md"

PREVIEW_SENTINEL = "https://preview-sentinel.invalid/DO-NOT-LEAK-CLIP"
TOKEN_SENTINEL = "Zx9-TOKEN-SENTINEL-9xZ"
RAW_ID_SENTINEL = "RAW-DEVICE-ID-DO-NOT-LEAK"


def _glass_evidence() -> nd.AcousticEvidence:
    """Nest acoustic + strong phone US-band corroboration → glass_shatter."""
    return nd.AcousticEvidence(
        nest_event="sound",
        nest_device_type="sdm.devices.types.CAMERA",
        nest_device_ref="abcd1234ef00",
        mic_diff_db=14.0,
        mic_energy_db=-30.0,
        band_energy_us_db=-40.0,
        band_burst="us",
        sound_burst=True,
        extreme_active=True,
        lag_s=2.0,
    )


def _weak_burst_evidence() -> nd.AcousticEvidence:
    """Nest acoustic + mild phone corroboration → sound_burst (not glass)."""
    return nd.AcousticEvidence(
        nest_event="sound",
        nest_device_ref="abcd1234ef00",
        mic_diff_db=7.0,
        band_burst="us",
        sound_burst=True,
        lag_s=1.0,
    )


def test_gs01_strong_corroboration_is_glass_shatter() -> None:
    cls = nd.offline_classify(_glass_evidence())
    assert cls.label == nd.LABEL_GLASS_SHATTER
    assert cls.corroborated is True
    assert cls.confidence >= 0.6


def test_gs02_weak_corroboration_stays_sound_burst() -> None:
    cls = nd.offline_classify(_weak_burst_evidence())
    assert cls.label == nd.LABEL_SOUND_BURST
    assert cls.label != nd.LABEL_GLASS_SHATTER


def test_gs03_glass_escalates_vol_blast() -> None:
    cls = nd.offline_classify(_glass_evidence())
    hint = nd.escalation_hint(cls, hold_manual=False)
    assert hint.get("alarmState") == "triggered"
    assert hint.get("volBlast") is True
    assert hint.get("trigger") == "nest_glass_shatter"


def test_gs04_hold_manual_blocks_escalation() -> None:
    cls = nd.offline_classify(_glass_evidence())
    assert nd.escalation_hint(cls, hold_manual=True) == {}


def test_gs05_wire_has_no_privacy_sentinels() -> None:
    cls = nd.offline_classify(_glass_evidence())
    wire = cls.as_wire()
    blob = repr(wire)
    assert PREVIEW_SENTINEL not in blob
    assert TOKEN_SENTINEL not in blob
    assert RAW_ID_SENTINEL not in blob
    assert "http://" not in blob and "https://" not in blob
    assert wire.get("nestBurstClass") == nd.LABEL_GLASS_SHATTER
    assert "nestBurstConfidence" in wire


def test_gs06_notify_documented_pending() -> None:
    text = ISSUE_DOC.read_text(encoding="utf-8")
    assert "pending" in text.lower()
    assert "Didn't" in text or "not claimed" in text.lower() or "pending" in text.lower()
    assert "notify" in text.lower()


def test_gs07_spec_and_issue_checklist_present() -> None:
    assert SPEC.is_file(), SPEC
    assert ISSUE_DOC.is_file(), ISSUE_DOC
    spec = SPEC.read_text(encoding="utf-8")
    for needle in ("GS-01", "GS-04", "holdManual", "glass_shatter", "notify"):
        assert needle in spec, needle
