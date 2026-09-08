#!/usr/bin/env bash
# Remote smoke test for a deployed public/ build (Vercel dev preview or production).
# Usage: scripts/deploy_smoke.sh <url>
# Env:   BYPASS         optional Vercel protection-bypass secret (sent as x-vercel-protection-bypass)
#        SMOKE_RETRIES  attempts per request (default 5)
#        SMOKE_SLEEP_S  seconds between attempts (default 6)
# Asserts the same C1 / Hold-Manual invariants as scripts/ci_static_gates.sh, but against the served site.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ROOT

URL="${1:-}"
if [[ -z "$URL" ]]; then
  echo "usage: $0 <url>   [env: BYPASS, SMOKE_RETRIES=5, SMOKE_SLEEP_S=6]" >&2
  exit 2
fi
URL="${URL%/}"
RETRIES="${SMOKE_RETRIES:-5}"
SLEEP_S="${SMOKE_SLEEP_S:-6}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

CURL_ARGS=(-sS -L --max-time 20)
if [[ -n "${BYPASS:-}" ]]; then
  # Vercel Deployment Protection bypass for automation; the value is never printed.
  CURL_ARGS+=(-H "x-vercel-protection-bypass: ${BYPASS}")
fi

fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "ok: $*"; }

# fetch <path> <hdr-file> <body-file> → 0 on HTTP 200 (after retries), else 1. Sets CODE.
fetch() {
  local path="$1" hdr="$2" body="$3" attempt code
  CODE="000"
  for ((attempt = 1; attempt <= RETRIES; attempt++)); do
    code="$(curl "${CURL_ARGS[@]}" -D "$hdr" -o "$body" -w '%{http_code}' "${URL}${path}")" || true
    code="${code:-000}"
    CODE="$code"
    if [[ "$code" == "200" ]]; then
      return 0
    fi
    echo "retry ${attempt}/${RETRIES}: GET ${URL}${path} -> HTTP ${code}" >&2
    if (( attempt < RETRIES )); then
      sleep "$SLEEP_S"
    fi
  done
  return 1
}

# Case-insensitive header lookup on the LAST response block (after redirects); CR stripped.
header_value() {
  local hdr="$1" name="$2"
  tr -d '\r' < "$hdr" | grep -i "^${name}:" | tail -n1 | sed -E "s/^[^:]+:[[:space:]]*//"
}

# 1. GET <url> → 200
fetch "" "$TMP/index.hdr" "$TMP/index.html" || fail "GET ${URL} -> HTTP ${CODE} (expected 200)"
ok "GET ${URL} -> 200"

# 2. Hold / Manual + holdManual markers (same as ci_static_gates.sh)
grep -q 'Hold / Manual' "$TMP/index.html" || fail "body missing 'Hold / Manual' label"
grep -q 'holdManual' "$TMP/index.html" || fail "body missing 'holdManual' wire key"
ok "Hold / Manual + holdManual present"

# 3. Permissions-Policy header contains microphone
pp="$(header_value "$TMP/index.hdr" "Permissions-Policy")"
[[ "${pp,,}" == *microphone* ]] || fail "Permissions-Policy header missing 'microphone' (got: '${pp}')"
ok "Permissions-Policy contains microphone"

# 4. /patch.json → 200 and schemaVersion == 1
fetch "/patch.json" "$TMP/patch.hdr" "$TMP/patch.json" || fail "GET ${URL}/patch.json -> HTTP ${CODE} (expected 200)"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("schemaVersion") == 1, d.get("schemaVersion")' "$TMP/patch.json" \
  || fail "patch.json schemaVersion != 1"
ok "patch.json schemaVersion == 1"

# 5. /manifest.webmanifest → 200 with Content-Type application/manifest+json
fetch "/manifest.webmanifest" "$TMP/manifest.hdr" "$TMP/manifest.json" || fail "GET ${URL}/manifest.webmanifest -> HTTP ${CODE} (expected 200)"
ct="$(header_value "$TMP/manifest.hdr" "Content-Type")"
[[ "${ct,,}" == application/manifest+json* ]] || fail "manifest Content-Type expected application/manifest+json (got: '${ct}')"
ok "manifest.webmanifest Content-Type application/manifest+json"

echo "OK deploy_smoke ${URL}"
