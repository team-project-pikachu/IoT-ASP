"""Tests for packages/iot-asp-study (public-safe study helpers)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "packages" / "iot-asp-study"
sys.path.insert(0, str(PKG))

from iot_asp_study.schema import validate_sidecar  # noqa: E402
from iot_asp_study.scrub import find_pii_markers  # noqa: E402


def test_example_sidecar_validates() -> None:
    payload = json.loads((PKG / "templates" / "sidecar.example.json").read_text(encoding="utf-8"))
    ok, msg = validate_sidecar(payload)
    assert ok, msg


def test_missing_key_fails() -> None:
    ok, msg = validate_sidecar({"node": "node1"})
    assert not ok
    assert "missing" in msg


def test_scrub_flags_street_like() -> None:
    text = "Site at 1234 Example Court is private."
    assert "street_like_address" in find_pii_markers(text)


def test_scrub_flags_private_bucket_uri() -> None:
    text = "Upload to gs://iot-asp-recordings-example-bucket/node1/"
    assert "private_recordings_bucket_uri" in find_pii_markers(text)


def test_public_templates_clean() -> None:
    for rel in (
        "README.md",
        "PROVENANCE.md",
        "templates/PROTOCOL.template.md",
        "templates/sidecar.example.json",
        "scripts/upload_recordings.sh",
    ):
        text = (PKG / rel).read_text(encoding="utf-8")
        assert find_pii_markers(text) == [], rel


@pytest.mark.parametrize("bad_node", ["node0", "phone1", ""])
def test_bad_node(bad_node: str) -> None:
    payload = {
        "ext_source": "outside",
        "site_code": "SITE",
        "node": bad_node,
        "algo": "hop",
        "vib_channel": "none",
        "started_at_utc": "2026-09-08T00:00:00Z",
        "ended_at_utc": "2026-09-08T00:01:00Z",
    }
    ok, _ = validate_sidecar(payload)
    assert not ok
