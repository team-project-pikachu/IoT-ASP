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
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  python3 -c "import json; from pathlib import Path; s=json.loads(Path('$SOURCES').read_text());
[print(lib['id'], lib['topic'], str(bool(lib.get('optional'))).lower(), query, sep='\t')
 for lib in s.get('libraries', []) for query in lib.get('queries', [])]" |
  while IFS=$'\t' read -r id topic optional query; do
    [[ -z "$id" || -z "$topic" || -z "$query" ]] && continue
    safe_id=$(echo "$id" | tr '/ ' '__')
    safe_topic=$(echo "$topic" | tr '/ ' '__')
    query_num=$(find "$TMP" -name "${safe_id}-*.md" | wc -l | tr -d ' ')
    result="$TMP/${safe_id}-${query_num}.md"
    log="$OUT/raw/c7-${safe_id}-${query_num}.log"
    echo "== docs $id [$topic]: $query =="
    if bash "$STABLE" docs "$id" "$query" > "$result" 2> "$log"; then
      {
        printf '\n<!-- source: %s; query: %s -->\n\n' "$id" "$query"
        cat "$result"
      } >> "$TMP/topic-${safe_topic}.md"
    elif [[ "$optional" == "true" ]]; then
      echo "WARN: optional Context7 query failed for $id: $query" >&2
    else
      echo "ERROR: required Context7 query failed for $id: $query" >&2
      exit 1
    fi
  done
  for topic_file in "$TMP"/topic-*.md; do
    [[ -e "$topic_file" ]] || continue
    topic_name="${topic_file##*/topic-}"
    mv "$topic_file" "$OUT/topics/$topic_name"
  done
fi

if [[ -f "$FC" ]]; then
  python3 -c "import json; from pathlib import Path; s=json.loads(Path('$SOURCES').read_text());
[print(p['url'], str(bool(p.get('optional'))).lower(), sep='\t') for p in s.get('firecrawl_portals', [])]" |
  while IFS=$'\t' read -r url optional; do
    [[ -z "$url" ]] && continue
    base=$(echo "$url" | sed 's#[^a-zA-Z0-9]#-#g' | cut -c1-80)
    echo "== firecrawl scrape $url =="
    if ! bash "$FC" scrape "$url" -o "$OUT/raw/${base}.md"; then
      if [[ "$optional" == "true" ]]; then
        echo "WARN: optional Firecrawl portal failed: $url" >&2
      else
        echo "ERROR: required Firecrawl portal failed: $url" >&2
        exit 1
      fi
    fi
  done
fi

echo "KB refresh done → $OUT"
