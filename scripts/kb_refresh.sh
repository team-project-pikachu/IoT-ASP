#!/usr/bin/env bash
# Refresh IoT-ASP knowledge base via context7-cli-stable. Fails closed on empty.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STABLE="${CONTEXT7_STABLE:-$HOME/.cursor/plugins/local/research-cli-kit/scripts/context7_stable.sh}"
SOURCES="$ROOT/reference/knowledge-base/sources.json"
TOPICS="$ROOT/reference/knowledge-base/topics"
mkdir -p "$TOPICS" "$ROOT/.context7"

if [[ ! -x "$STABLE" && ! -f "$STABLE" ]]; then
  echo "ERROR: context7_stable.sh not found at $STABLE" >&2
  exit 1
fi

DATE_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
python3 - "$SOURCES" "$TOPICS" "$STABLE" "$DATE_UTC" "$ROOT" <<'PY'
import json, os, subprocess, sys
from pathlib import Path

sources_path, topics_dir, stable, date_utc, root = sys.argv[1:6]
cfg = json.loads(Path(sources_path).read_text())
topics = Path(topics_dir)
root = Path(root)
used = []
by_topic: dict[str, list[str]] = {}

def run(args):
    p = subprocess.run(args, cwd=str(root), capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        print(out, file=sys.stderr)
        raise SystemExit(f"context7 failed: {' '.join(args)}")
    return out

for lib in cfg.get("libraries", []):
    lid = lib["id"]
    topic = lib.get("topic") or "misc"
    optional = bool(lib.get("optional"))
    chunks = []
    for q in lib.get("queries", []):
        print(f"docs {lid} :: {q[:60]}...", flush=True)
        out = run(["bash", stable, "docs", lid, q])
        if len(out.strip()) < 40:
            if optional:
                print(f"WARN optional empty: {lid} {q}", file=sys.stderr)
                continue
            raise SystemExit(f"FAIL empty docs for {lid}: {q}")
        chunks.append(f"## Query\n\n`{q}`\n\n### Context7 output\n\n{out.strip()}\n")
    if not chunks and optional:
        continue
    if not chunks:
        raise SystemExit(f"FAIL no chunks for {lid}")
    by_topic.setdefault(topic, []).append(
        f"# {lib.get('name', lid)}\n\nLibrary ID: `{lid}`\nRefresh: `{date_utc}`\n\n"
        + "\n".join(chunks)
    )
    used.append({"id": lid, "topic": topic, "queries": lib.get("queries", [])})

for topic, parts in by_topic.items():
    dest = topics / f"{topic}.md"
    body = f"<!-- auto-refreshed {date_utc} via scripts/kb_refresh.sh -->\n\n" + "\n---\n\n".join(parts)
    dest.write_text(body)
    print("wrote", dest)

meta = {
    "refreshedAt": date_utc,
    "libraries": used,
    "firecrawl_portals": cfg.get("firecrawl_portals", []),
}
Path(root / "reference/knowledge-base/last_refresh.json").write_text(json.dumps(meta, indent=2) + "\n")
print("OK kb_refresh", date_utc)
PY
