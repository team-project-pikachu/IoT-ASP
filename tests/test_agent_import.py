"""Parked #24: document root_agent tool names; skip live import without google-adk.

CI `tests` job installs requirements-dev.txt only (no google-adk). The live
agent assertion is skipped there; the AST parse of agent.py always runs.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "services" / "autoroute-adk"
AGENT_PY = PKG_DIR / "iot_asp_autoroute" / "agent.py"
REQUIREMENTS = PKG_DIR / "requirements.txt"
EXAMPLE_ADK2 = PKG_DIR / "requirements-adk2.example.txt"
SPEC = ROOT / "docs" / "specs" / "24-adk-2x-migration.md"

if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

# Order matches services/autoroute-adk/iot_asp_autoroute/agent.py tools=[...].
EXPECTED_ROOT_AGENT_TOOL_NAMES = (
    "read_telemetry",
    "write_patch",
    "list_safety_clamps",
    "seismo_acoustic_priors",
    "colab_handoff_note",
    "ingest_telemetry",
    "process_sudden_freq",
    "fleet_log_summary",
    "live_features",
    "hw_limits_report",
    "nest_fleet_status",
    "nest_classify_burst",
)


def _declared_tool_names() -> list[str]:
    tree = ast.parse(AGENT_PY.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != "LlmAgent":
            continue
        for kw in node.keywords:
            if kw.arg != "tools" or not isinstance(kw.value, ast.List):
                continue
            names: list[str] = []
            for elt in kw.value.elts:
                if not isinstance(elt, ast.Name):
                    raise AssertionError(f"non-name tool entry: {ast.dump(elt)}")
                names.append(elt.id)
            return names
    raise AssertionError("LlmAgent(tools=[...]) not found in agent.py")


def _requirement_lines(path: Path, package: str) -> list[str]:
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(package):
            out.append(line)
    return out


def _tool_name(tool: object) -> str:
    name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
    if isinstance(name, str) and name:
        return name
    fn = getattr(tool, "func", None) or getattr(tool, "function", None)
    fn_name = getattr(fn, "__name__", None)
    if isinstance(fn_name, str) and fn_name:
        return fn_name
    raise AssertionError(f"cannot read tool name from {type(tool)!r}")


def test_declared_tool_names_match_expected():
    assert _declared_tool_names() == list(EXPECTED_ROOT_AGENT_TOOL_NAMES)


def test_expected_tools_are_callables_in_tools_module():
    from iot_asp_autoroute import tools as tools_mod

    for name in EXPECTED_ROOT_AGENT_TOOL_NAMES:
        assert callable(getattr(tools_mod, name)), name


def test_parked_google_adk_pin_stays_major_1():
    adk = _requirement_lines(REQUIREMENTS, "google-adk")
    genai = _requirement_lines(REQUIREMENTS, "google-genai")
    assert adk == ["google-adk>=1.39.1,<2"]
    assert genai == ["google-genai>=2.22.0,<3"]
    example = EXAMPLE_ADK2.read_text(encoding="utf-8")
    assert re.search(r"^google-adk>=2\.8\.0,<3\s*$", example, re.M)
    assert re.search(r"^google-genai>=2\.22\.0,<3\s*$", example, re.M)


def test_spec_lists_expected_tool_names():
    spec = SPEC.read_text(encoding="utf-8")
    goal = spec.split("## Goal", 1)[1].split("## Prior art", 1)[0]
    expected = ", ".join(f"`{name}`" for name in EXPECTED_ROOT_AGENT_TOOL_NAMES) + "."
    assert expected in {line.strip() for line in goal.splitlines()}
    assert "len(root_agent.tools) == 7" not in spec
    assert "seven tools" not in spec


def test_root_agent_tool_names_when_adk_installed():
    pytest.importorskip("google.adk")
    from iot_asp_autoroute.agent import root_agent

    names = [_tool_name(t) for t in root_agent.tools]
    assert names == list(EXPECTED_ROOT_AGENT_TOOL_NAMES)
    assert root_agent.name == "iot_asp_autoroute"
