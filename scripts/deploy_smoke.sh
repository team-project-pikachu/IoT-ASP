#!/usr/bin/env bash
# Remote smoke test for a deployed public/ build (Vercel dev preview or production).
# Usage: scripts/deploy_smoke.sh <url>
# Env:   BYPASS            optional Vercel protection-bypass secret (sent as x-vercel-protection-bypass)
#        SMOKE_PUBLIC_DIR  optional local public/ dir: every deployable file's ETag must equal the md5 (or
#                          sha1) of the local copy, i.e. the served build IS this checkout (build identity)
#        SMOKE_RETRIES     attempts per request (default 5)
#        SMOKE_SLEEP_S     seconds between attempts (default 6)
# Asserts the same C1 / Hold-Manual invariants as scripts/ci_static_gates.sh, but against the served site.
#
# Security notes:
#   * Redirects are NOT followed. curl forwards custom -H headers (unlike Authorization/Cookie) to any
#     redirect target, including other hosts, so with -L the BYPASS secret could leak off-host. A 3xx is a
#     failure; the Location query/fragment is redacted in CI output.
#   * BYPASS is only ever sent over https (loopback excepted, for offline tests).
#   * Digests use Python (hashlib) so macOS hosts without GNU md5sum/sha1sum still work.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ROOT

URL="${1:-}"
if [[ -z "$URL" ]]; then
  echo "usage: $0 <url>   [env: BYPASS, SMOKE_PUBLIC_DIR, SMOKE_RETRIES=5, SMOKE_SLEEP_S=6]" >&2
  exit 2
fi
URL="${URL%/}"
RETRIES="${SMOKE_RETRIES:-5}"
SLEEP_S="${SMOKE_SLEEP_S:-6}"
PUBLIC_DIR="${SMOKE_PUBLIC_DIR:-}"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "ok: $*"; }
# bash 3.2 (macOS /bin/bash) has no ${var,,}; keep Linux CI + Mac preflight on the same script.
lc() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }


scheme="${URL%%://*}"
hostport="${URL#*://}"; hostport="${hostport%%/*}"
if [[ "$hostport" == \[* ]]; then host="${hostport%%]*}]"; else host="${hostport%%:*}"; fi  # IPv6 [::1]:port safe
if [[ -n "${BYPASS:-}" && "$(lc "$scheme")" != "https" ]]; then
  case "$host" in
    127.0.0.1|localhost|\[::1\]) ;;  # loopback: offline tests only
    *) fail "refusing to send the protection-bypass secret over plaintext ${scheme} to ${host} (use https)" ;;
  esac
fi
if [[ -n "$PUBLIC_DIR" ]]; then
  [[ -d "$PUBLIC_DIR" ]] || fail "SMOKE_PUBLIC_DIR '${PUBLIC_DIR}' is not a directory"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# No -L: see security notes above. --max-redirs 0 makes the intent explicit even if -L is ever re-added.
CURL_ARGS=(-sS --max-redirs 0 --max-time 20)
if [[ -n "${BYPASS:-}" ]]; then
  # Vercel Deployment Protection bypass for automation; the value is never printed.
  CURL_ARGS+=(-H "x-vercel-protection-bypass: ${BYPASS}")
fi

# Case-insensitive header lookup; CR stripped. Prints nothing (exit 0) when the header is absent —
# `grep` alone would exit 1 and, under `set -eo pipefail`, abort the caller before its diagnostic.
header_value() {
  local hdr="$1" name="$2"
  { tr -d '\r' < "$hdr" | grep -i "^${name}:" || true; } | tail -n1 | sed -E "s/^[^:]+:[[:space:]]*//"
}

# Redact query/fragment from an untrusted Location before printing (redirects are terminal).
redact_location() {
  local loc="$1"
  case "$loc" in
    *\?**|*\#*) echo "${loc%%[?#]*}?[redacted]" ;;
    *) echo "$loc" ;;
  esac
}

# Digests via Python so macOS (no md5sum/sha1sum) and Linux CI agree.
file_digests() {
  python3 -c 'import hashlib,sys; b=open(sys.argv[1],"rb").read(); print(hashlib.md5(b).hexdigest()+" "+hashlib.sha1(b).hexdigest())' "$1"
}

# Build identity: served ETag (weak marker and quotes stripped) must equal md5 or sha1 of the local file.
# Vercel serves static files with ETag == md5(content) (observed 2026-09-08 on the prod URL, see docs/deploy.md).
# identity_check <path> <hdr-file> <local-file> → 0 on match; prints the mismatch reason on stderr otherwise.
identity_check() {
  local path="$1" hdr="$2" local_file="$3" etag md5 sha1 digests
  [[ -f "$local_file" ]] || { echo "identity: local file ${local_file} missing" >&2; return 1; }
  etag="$(header_value "$hdr" "ETag")"
  etag="${etag#W/}"; etag="${etag%\"}"; etag="${etag#\"}"
  digests="$(file_digests "$local_file")"
  md5="${digests%% *}"
  sha1="${digests##* }"
  if [[ -z "$etag" ]]; then
    echo "identity: ${path:-/} served without an ETag; cannot prove the build is this checkout" >&2
    return 1
  fi
  if [[ "$(lc "$etag")" == "$md5" || "$(lc "$etag")" == "$sha1" ]]; then
    return 0
  fi
  echo "identity: ${path:-/} ETag '${etag}' != local md5 ${md5} (sha1 ${sha1}) — served build is not this checkout (yet)" >&2
  return 1
}

# fetch <path> <hdr-file> <body-file> [<local-file>] → 0 on HTTP 200 (+ identity match when
# SMOKE_PUBLIC_DIR is set) after retries, else 1. Sets CODE. A 3xx is terminal (never followed).
fetch() {
  local path="$1" hdr="$2" body="$3" local_file="${4:-}" attempt code loc safe_loc
  CODE="000"
  for ((attempt = 1; attempt <= RETRIES; attempt++)); do
    code="$(curl "${CURL_ARGS[@]}" -D "$hdr" -o "$body" -w '%{http_code}' "${URL}${path}")" || true
    code="${code:-000}"
    CODE="$code"
    if [[ "$code" == 3?? ]]; then
      loc="$(header_value "$hdr" "Location")"
      safe_loc="$(redact_location "$loc")"
      echo "GET ${URL}${path} -> HTTP ${code}: redirect to '${safe_loc}' not followed (headers are never forwarded off-host)" >&2
      return 1
    fi
    if [[ "$code" == "200" ]]; then
      if [[ -z "$PUBLIC_DIR" ]] || identity_check "$path" "$hdr" "${PUBLIC_DIR}/${local_file}"; then
        return 0
      fi
      CODE="200 but build identity mismatch"
      echo "retry ${attempt}/${RETRIES}: GET ${URL}${path} -> ${CODE}" >&2
    else
      echo "retry ${attempt}/${RETRIES}: GET ${URL}${path} -> HTTP ${code}" >&2
    fi
    if (( attempt < RETRIES )); then
      sleep "$SLEEP_S"
    fi
  done
  return 1
}

# Map a path under PUBLIC_DIR to the URL path Vercel serves (cleanUrls: index.html → /).
public_url_path() {
  local rel="$1"
  case "$rel" in
    index.html) echo "" ;;
    *) echo "/${rel}" ;;
  esac
}

# 1. GET <url> → 200 (cleanUrls: "/" serves public/index.html)
fetch "" "$TMP/index.hdr" "$TMP/index.html" "index.html" || fail "GET ${URL} -> HTTP ${CODE} (expected 200)"
ok "GET ${URL} -> 200"

# 2. Hold / Manual + holdManual markers (same as ci_static_gates.sh)
grep -q 'Hold / Manual' "$TMP/index.html" || fail "body missing 'Hold / Manual' label"
grep -q 'holdManual' "$TMP/index.html" || fail "body missing 'holdManual' wire key"
ok "Hold / Manual + holdManual present"

# 3. Permissions-Policy header contains microphone
pp="$(header_value "$TMP/index.hdr" "Permissions-Policy")"
[[ "$(lc "$pp")" == *microphone* ]] || fail "Permissions-Policy header missing 'microphone' (got: '${pp}')"
ok "Permissions-Policy contains microphone"

# 4. /patch.json → 200 and schemaVersion == 1
fetch "/patch.json" "$TMP/patch.hdr" "$TMP/patch.json" "patch.json" || fail "GET ${URL}/patch.json -> HTTP ${CODE} (expected 200)"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("schemaVersion") == 1, d.get("schemaVersion")' "$TMP/patch.json" \
  || fail "patch.json schemaVersion != 1"
ok "patch.json schemaVersion == 1"

# 5. /manifest.webmanifest → 200 with Content-Type application/manifest+json
fetch "/manifest.webmanifest" "$TMP/manifest.hdr" "$TMP/manifest.json" "manifest.webmanifest" || fail "GET ${URL}/manifest.webmanifest -> HTTP ${CODE} (expected 200)"
ct="$(header_value "$TMP/manifest.hdr" "Content-Type")"
[[ "$(lc "$ct")" == application/manifest+json* ]] || fail "manifest Content-Type expected application/manifest+json (got: '${ct}')"
ok "manifest.webmanifest Content-Type application/manifest+json"

# 6. Build identity for EVERY deployable file under SMOKE_PUBLIC_DIR (not just the three smoke paths).
#    A deploy that changes only apple-touch-icon.png (or any future asset) must not go green on the old build.
if [[ -n "$PUBLIC_DIR" ]]; then
  checked=0
  while IFS= read -r -d '' f; do
    rel="${f#"${PUBLIC_DIR}/"}"
    # Skip hidden / VCS noise; everything else under public/ is deployable.
    case "$rel" in
      .*|*/.*|.git/*|*/.git/*) continue ;;
    esac
    path="$(public_url_path "$rel")"
    # Core three already fetched above; re-check is cheap and keeps one code path.
    fetch "$path" "$TMP/id.hdr" "$TMP/id.body" "$rel" \
      || fail "GET ${URL}${path:-/} -> HTTP ${CODE} (expected 200 + build identity for ${rel})"
    checked=$((checked + 1))
  done < <(find "$PUBLIC_DIR" -type f -print0 | sort -z)
  [[ "$checked" -gt 0 ]] || fail "SMOKE_PUBLIC_DIR '${PUBLIC_DIR}' has no deployable files"
  ok "build identity: ETags of ${checked} file(s) under ${PUBLIC_DIR} match this checkout"
fi

echo "OK deploy_smoke ${URL}"
