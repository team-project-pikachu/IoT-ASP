#!/usr/bin/env bash
# Lightweight breaking-change gates for public HTML + patch wire (no network).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

HTML="public/index.html"
PATCH="public/patch.json"

fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -f "$HTML" ]] || fail "missing $HTML"
[[ -f "$PATCH" ]] || fail "missing $PATCH"

# Hold / Manual must remain the human freeze control surface.
grep -q 'Hold / Manual' "$HTML" || fail "public/index.html missing Hold / Manual UI label"
grep -q 'holdManual' "$HTML" || fail "public/index.html missing holdManual wire field"
grep -q 'holdPatchBtn' "$HTML" || fail "public/index.html missing holdPatchBtn"

# No obvious API / Gemini / Vertex secrets embedded in public HTML.
python3 - <<'PY'
from pathlib import Path
import re
import sys

html = Path("public/index.html").read_text(encoding="utf-8", errors="replace")
patterns = [
    r"AIza[0-9A-Za-z_-]{20,}",
    r"sk-[A-Za-z0-9]{20,}",
    r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY",
    r"GOOGLE_API_KEY\s*[:=]\s*['\"][^'\"]+['\"]",
    r"GEMINI_API_KEY\s*[:=]\s*['\"][^'\"]+['\"]",
    r"VERTEX_API_KEY\s*[:=]\s*['\"][^'\"]+['\"]",
    r"apiKey\s*[:=]\s*['\"][A-Za-z0-9_-]{16,}['\"]",
]
hits = []
for pat in patterns:
    for m in re.finditer(pat, html, flags=re.I):
        hits.append(f"{pat}: {m.group(0)[:40]}…")
if hits:
    print("FAIL: possible API key / secret pattern in public/index.html", file=sys.stderr)
    for h in hits:
        print(" ", h, file=sys.stderr)
    sys.exit(1)
print("no API key patterns in public/index.html OK")
PY

# patch.json must be schemaVersion 1 wire.
python3 - <<'PY'
import json
from pathlib import Path
p = Path("public/patch.json")
data = json.loads(p.read_text(encoding="utf-8"))
sv = data.get("schemaVersion")
if sv != 1:
    raise SystemExit(f"FAIL: public/patch.json schemaVersion expected 1, got {sv!r}")
print(f"patch.json schemaVersion={sv} OK")
PY

# Clamp constant must stay aligned with UI percent hard max (C4).
python3 - <<'PY'
import sys
from pathlib import Path
root = Path("services/autoroute-adk")
sys.path.insert(0, str(root))
from iot_asp_autoroute.clamps import CLAMPS, SCHEMA_VERSION
assert SCHEMA_VERSION == 1, SCHEMA_VERSION
assert CLAMPS["vol_hard_max"] == 100.0, CLAMPS
assert CLAMPS["vol_soft_max"] == 100.0, CLAMPS
print(f"clamps SCHEMA_VERSION={SCHEMA_VERSION} vol_hard_max={CLAMPS['vol_hard_max']} OK")
PY

echo "OK ci_static_gates"
