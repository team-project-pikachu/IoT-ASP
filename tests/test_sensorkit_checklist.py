"""#148 entitlement checklist — no fake grants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/sensorkit-entitlement-checklist.md"


def test_unchecked():
    text = DOC.read_text(encoding="utf-8")
    assert "not approved" in text.lower()
    assert "- [ ] Apple Developer Program" in text
    assert "ASP_SENSORKIT_ENTITLED" in text
    assert "fake" not in text.lower() or "No fake" in text or "not invent" in text
    spec = (ROOT / "docs/specs/148-sensorkit-checklist.md").read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
