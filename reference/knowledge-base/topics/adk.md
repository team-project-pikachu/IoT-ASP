<!-- partial refresh via context7_stable -->

<!-- seed; refresh via scripts/kb_refresh.sh -->

# ADK Python (`/google/adk-python`)

Official overview: https://docs.cloud.google.com/agent-builder/agent-development-kit/overview

Patterns used in IoT-ASP:

- Package with `__init__.py` → `from . import agent` and `agent.py` exporting `root_agent`
- `LlmAgent(..., tools=[...])` with plain Python callables as tools
- Local: `adk web` / `adk run`
- Deploy: `adk deploy agent_engine` or `adk deploy cloud_run`

See `docs/adk-autoroute.md` and Firecrawl artifacts in `reference/knowledge/adk/`.

## Context7 snippet

WARN: ctx7 CLI docs empty; call MCP query-docs libraryId=/google/adk-python
