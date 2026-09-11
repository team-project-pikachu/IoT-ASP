"""Compatibility shim for layouts that expect a top-level ``adk_agent`` package.

Canonical agent lives at ``services/autoroute-adk/iot_asp_autoroute/agent.py``.
This module re-exports ``root_agent`` so Agent Engine / adk CLI entrypoints that
resolve ``adk_agent`` do not hit an empty directory.

Importing ``root_agent`` still requires ``google-adk`` (same as the canonical module).
Dry-run and tool paths remain under ``services/autoroute-adk/`` and do not need this shim.
"""

from __future__ import annotations

try:
    from iot_asp_autoroute.agent import root_agent
except ImportError:
    # Allow package presence without installing the full ADK path on PYTHONPATH.
    # Callers that need the agent must install services/autoroute-adk requirements
    # and ensure that package is importable (pip install -e services/autoroute-adk).
    root_agent = None  # type: ignore[assignment]

__all__ = ["root_agent"]
