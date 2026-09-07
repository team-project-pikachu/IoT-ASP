# Knowledge Base — IoT-ASP

Deterministic, refreshable docs digests via **context7-cli-stable**.

Wrapper: `~/.cursor/plugins/local/research-cli-kit/scripts/context7_stable.sh`

## Refresh

```bash
cd /Users/machine/apps/IoT-ASP
bash scripts/kb_refresh.sh
```

Fails closed if any resolve/docs call returns empty. Writes:

- `.context7/` — raw CLI caches (gitignored)
- `reference/knowledge-base/topics/*.md` — curated digests (committed)
- `reference/knowledge-base/last_refresh.json` — timestamp + library IDs used

## Sources

Pinned Context7 library IDs: [`sources.json`](sources.json)

Primary ADK Cloud doc (also Firecrawl-ingested):  
https://docs.cloud.google.com/agent-builder/agent-development-kit/overview

Firecrawl portal artifacts: `reference/knowledge/adk/` + update in `reference/knowledge/INGEST.md`.

## Topics

| Digest | Focus |
|--------|--------|
| [topics/adk.md](topics/adk.md) | Agent Development Kit |
| [topics/gemini-enterprise.md](topics/gemini-enterprise.md) | Gemini Enterprise / Agent Platform |
| [topics/autoroute.md](topics/autoroute.md) | Autoroute design notes tied to ADK tools |

## Policy

No site PII. No API keys. Prefer official library IDs (`/google/adk-python`, Vertex/Gemini websites).
