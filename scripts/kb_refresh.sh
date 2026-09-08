#!/usr/bin/env bash
# Refresh IoT-ASP knowledge-base via context7-cli-stable (+ optional firecrawl).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STABLE="${CONTEXT7_STABLE:-$HOME/.cursor/plugins/local/research-cli-kit/scripts/context7_stable.sh}"
FC="${FIRECRAWL_STABLE:-$HOME/.cursor/plugins/local/research-cli-kit/scripts/firecrawl_stable.sh}"
SOURCES="$ROOT/reference/knowledge-base/sources.json"
OUT="$ROOT/reference/knowledge-base"
mkdir -p "$OUT/topics" "$OUT/raw" "$ROOT/.context7"

if [[ ! -f "$STABLE" ]]; then
  echo "WARN: context7_stable.sh not found at $STABLE" >&2
else
  python3 -c "import json; from pathlib import Path; s=json.loads(Path('$SOURCES').read_text());
[print(lib['id']) for lib in s.get('libraries',[])]" | while read -r id; do
    [[ -z "$id" ]] && continue
    safe=$(echo "$id" | tr '/ ' '__')
    echo "== docs $id =="
    bash "$STABLE" docs "$id" "IoT-ASP autoroute ADK Gemini install get started" \
      > "$OUT/topics/${safe}.md" 2>"$OUT/raw/c7-${safe}.log" || true
  done
fi

if [[ -f "$FC" ]]; then
  python3 -c "import json; from pathlib import Path; s=json.loads(Path('$SOURCES').read_text());
[print(p['url']) for p in s.get('firecrawl_portals',[])]" | while read -r url; do
    [[ -z "$url" ]] && continue
    base=$(echo "$url" | sed 's#[^a-zA-Z0-9]#-#g' | cut -c1-80)
    echo "== firecrawl scrape $url =="
    bash "$FC" scrape "$url" -o "$OUT/raw/${base}.md" || true
  done
fi

echo "KB refresh done → $OUT"
