"""Tests for packages/iot-asp-study (public-safe study helpers)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "packages" / "iot-asp-study"
sys.path.insert(0, str(PKG))

from iot_asp_study.paths import resolve_study_root  # noqa: E402
from iot_asp_study.schema import validate_sidecar  # noqa: E402
from iot_asp_study.scrub import find_pii_markers, scan_paths  # noqa: E402


def _valid(**overrides):
    base = {
        "ext_source": "outside",
        "site_code": "SITE",
        "node": "node1",
        "algo": "hop",
        "vib_channel": "none",
        "started_at_utc": "2026-09-08T00:00:00Z",
        "ended_at_utc": "2026-09-08T00:01:00Z",
    }
    base.update(overrides)
    return base


def test_example_sidecar_validates() -> None:
    payload = json.loads((PKG / "templates" / "sidecar.example.json").read_text(encoding="utf-8"))
    ok, msg = validate_sidecar(payload)
    assert ok, msg


def test_missing_key_fails() -> None:
    ok, msg = validate_sidecar({"node": "node1"})
    assert not ok
    assert "missing" in msg


def test_scrub_flags_street_like_short_number() -> None:
    text = "Site at 12 Main Street is private."
    assert "street_like_address" in find_pii_markers(text)


def test_scrub_flags_any_non_placeholder_gs_uri() -> None:
    text = "Upload to gs://some-other-bucket/node1/"
    assert "private_gs_uri" in find_pii_markers(text)
    assert find_pii_markers("gs://YOUR_PRIVATE_BUCKET/node1/") == []


def test_scan_paths_fail_closed_on_missing() -> None:
    missing = PKG / "templates" / "does-not-exist.md"
    hits = scan_paths([missing])
    assert str(missing) in hits
    assert hits[str(missing)] == ["missing_or_unreadable"]


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


def test_resolve_study_root_stops_at_git_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ancestor has study/, but first git root (tmp_path) does not — must return None.
    ancestor = tmp_path / "ancestor"
    ancestor.mkdir()
    (ancestor / "study").mkdir()
    repo = ancestor / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.delenv("IOT_ASP_STUDY_ROOT", raising=False)
    assert resolve_study_root(repo) is None


def test_timestamps_must_be_utc_aware_and_ordered() -> None:
    ok, msg = validate_sidecar(_valid(started_at_utc="yesterday"))
    assert not ok
    assert "ISO-8601" in msg or "timezone" in msg
    ok, msg = validate_sidecar(
        _valid(started_at_utc="2026-09-08T01:00:00Z", ended_at_utc="2026-09-08T00:00:00Z")
    )
    assert not ok
    assert "ended_at_utc" in msg


@pytest.mark.parametrize("bad_node", ["node0", "phone1", ""])
def test_bad_node(bad_node: str) -> None:
    ok, _ = validate_sidecar(_valid(node=bad_node))
    assert not ok


def test_doctor_exits_zero_offline() -> None:
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(PKG / "scripts" / "doctor.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "OK schema fixture" in proc.stdout
    assert "OK public package scrub" in proc.stdout
