"""#150 product tab hooks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_parked():
    src = (ROOT / "native/IoTASP/Shared/Product/ProductTabHooks.swift").read_text(encoding="utf-8")
    assert "nestOAuthParked = true" in src
    assert "sound_burst" in src
    spec = (ROOT / "docs/specs/150-product-tabs.md").read_text(encoding="utf-8")
    for h in ["Status", "Goal", "Prior art", "Shipped on `main`", "Remaining scope",
              "Wire fields", "Clamps / safety", "Acceptance tests", "CI gate",
              "Risks / HW limits", "Sources"]:
        assert f"## {h}" in spec, h
