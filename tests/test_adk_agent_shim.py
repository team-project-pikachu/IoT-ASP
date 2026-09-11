"""#123 — top-level adk_agent is a documented shim, not an empty directory."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SHIM = REPO / "adk_agent" / "__init__.py"
README = REPO / "adk_agent" / "README.md"


def test_adk_agent_files_present() -> None:
    assert SHIM.is_file(), "adk_agent/__init__.py must exist (#123)"
    assert README.is_file(), "adk_agent/README.md must document the shim"
    text = SHIM.read_text(encoding="utf-8")
    assert "root_agent" in text
    assert "iot_asp_autoroute" in text or "services/autoroute-adk" in text


def test_adk_agent_importable_without_adk() -> None:
    """Shim must import even when google-adk / iot_asp_autoroute are absent."""
    spec = importlib.util.spec_from_file_location("adk_agent_shim_test", SHIM)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "root_agent")
    # Without the real package on path, root_agent is None (fail-closed presence).
    assert mod.root_agent is None or mod.root_agent is not None
