"""Offline gates for issue #62 field checklist + Playwright MVP hooks."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUE = ROOT / "docs" / "issues" / "ISSUE-62-mvp-field-acceptance-e2e.md"
CHECKLIST = ROOT / "docs" / "field-acceptance-m0.md"
SPEC = ROOT / "docs" / "specs" / "62-mvp-field-acceptance-e2e.md"
HTML = ROOT / "public" / "index.html"
E2E = ROOT / "tests" / "e2e" / "public_smoke.spec.mjs"
VV_SOFT = ROOT / ".vv" / "62" / "SOFTWARE-E2E.md"
VV_FIELD = ROOT / ".vv" / "62" / "FIELD-PASS.md"
CI = ROOT / "docs" / "ci.md"


def test_issue_62_checklist_covers_acceptance_topics() -> None:
    text = ISSUE.read_text(encoding="utf-8")
    for needle in (
        "A2DP",
        "Hold / Manual",
        "suddenFreq",
        "night",
        "Soundcore",
        "fleet_log",
        "Informative",
        "#63",
        "make e2e",
    ):
        assert needle in text, needle
    assert "Web Bluetooth" in text


def test_issue_62_spec_and_evidence_exist() -> None:
    assert SPEC.is_file()
    assert CHECKLIST.is_file()
    checklist = CHECKLIST.read_text(encoding="utf-8")
    for needle in ("FA-01", "FA-07", "FA-11", "C1", "Soundcore", "informative"):
        assert needle in checklist, needle
    assert VV_SOFT.is_file()
    assert VV_FIELD.is_file()
    soft = VV_SOFT.read_text(encoding="utf-8")
    assert "make e2e" in soft
    assert "informative" in soft.lower()
    field = VV_FIELD.read_text(encoding="utf-8")
    assert "Soundcore" in field and "owner" in field.lower()


def test_public_html_exposes_mvp_e2e_hooks() -> None:
    html = HTML.read_text(encoding="utf-8")
    for tok in (
        "setTestNowMs",
        "forceSuddenRotate",
        "fleetLogKeys",
        "getNight",
        "clockNow",
        "__testNowMs",
    ):
        assert tok in html, tok


def test_e2e_spec_has_mvp_field_acceptance_suite() -> None:
    spec = E2E.read_text(encoding="utf-8")
    assert 'MVP field acceptance (#62)' in spec
    assert "forceSuddenRotate" in spec
    assert "setTestNowMs" in spec
    assert "RECORD_KEYS" in spec
    assert "Soundcore 2 ultrasonic warning" in spec


def test_ci_docs_state_informative_waiver() -> None:
    ci = CI.read_text(encoding="utf-8")
    assert "MVP field acceptance (#62)" in ci or "ISSUE-62" in ci
    assert "informative" in ci.lower()
    assert "#63" in ci
