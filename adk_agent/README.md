# `adk_agent/` compatibility shim

**Canonical agent:** `services/autoroute-adk/iot_asp_autoroute/agent.py` (`root_agent`).

This top-level package exists so deploy layouts / ADK CLI entrypoints that resolve
`adk_agent` do not land on an empty directory (see issue #123).

## Usage

```bash
# Preferred — install the real package
pip install -r services/autoroute-adk/requirements.txt
# ensure services/autoroute-adk is on PYTHONPATH or install editable

# Optional shim import (re-exports root_agent when iot_asp_autoroute is importable)
python -c "import adk_agent; print(adk_agent.root_agent)"
```

If `iot_asp_autoroute` is not on `PYTHONPATH`, `adk_agent.root_agent` is `None`
and callers should import the canonical module instead.

## Non-goals

- Does not duplicate tools, clamps, or agent instruction text.
- Does not change dry-run (`scripts/autoroute_dev.sh`) or Vercel paths.
- No secrets; no schemaVersion bump.
