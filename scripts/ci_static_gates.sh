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

# 1Password access must offer the headless service-account path (locked rule:
# .cursor/rules/secrets-headless-op.mdc). `op signin` is allowed only as a labelled
# fallback, never as a script's only authentication route.
python3 - <<'PYGATE'
from pathlib import Path
import sys

bad = []
for path in sorted(Path("scripts").glob("*.sh")):
    text = path.read_text(encoding="utf-8", errors="replace")
    if "op signin" in text and "OP_SERVICE_ACCOUNT_TOKEN" not in text:
        bad.append(f"{path}: 'op signin' with no OP_SERVICE_ACCOUNT_TOKEN headless path")
if bad:
    print("FAIL: interactive-only 1Password auth", file=sys.stderr)
    for b in bad:
        print(" ", b, file=sys.stderr)
    sys.exit(1)
print("1Password headless service-account path present OK")
PYGATE

# Nest: no site-identifying resource names in tracked files. Google's own docs use the
# placeholders `project-id` / `device-id` / `structure-id`; a real opaque id or a Google
# Home app structure URL is site PII (CLAUDE.md invariant 7).
python3 - <<'PYGATE'
from pathlib import Path
import re
import subprocess
import sys

try:
    tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
except Exception:
    print("skip nest PII gate (no git)")
    raise SystemExit(0)

HOME_URL = re.compile(r"home\.google\.com/[^\s)\"']*home/[0-9a-f]{16,}", re.I)
SDM_REAL = re.compile(r"enterprises/(?!project-id)[A-Za-z0-9_-]{16,}/devices/(?!device-id)[A-Za-z0-9_-]{16,}")
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".ico", ".webp", ".pdf"}

hits = set()
for rel in tracked:
    path = Path(rel)
    if not path.is_file() or path.suffix.lower() in SKIP_SUFFIX:
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    if HOME_URL.search(text):
        hits.add(f"{rel}: Google Home structure URL")
    if SDM_REAL.search(text):
        hits.add(f"{rel}: real-looking SDM resource name")
if hits:
    print("FAIL: site-identifying Nest resource in tracked files", file=sys.stderr)
    for h in sorted(hits):
        print(" ", h, file=sys.stderr)
    sys.exit(1)
print("no site-identifying Nest ids in tracked files OK")
PYGATE

# Nest quota constants must equal the documented numbers. If Google changes a quota this
# fails loudly, rather than the continuous poller silently pacing wrong for an hour.
python3 - <<'PYGATE'
import sys
from pathlib import Path

sys.path.insert(0, str(Path("services/autoroute-adk")))
from iot_asp_autoroute.nest import constants as c

assert c.METHOD_QUOTAS[c.METHOD_DEVICES_LIST] == (5, None), c.METHOD_QUOTAS
assert c.METHOD_QUOTAS[c.METHOD_DEVICES_GET] == (10, None), c.METHOD_QUOTAS
assert c.DEVICE_QUOTAS[c.TYPE_CAMERA] == (30, 100), c.DEVICE_QUOTAS
assert c.DEFAULT_LIST_CADENCE_S == 12.0, c.DEFAULT_LIST_CADENCE_S
assert c.DEFAULT_CAMERA_CADENCE_S == 36.0, c.DEFAULT_CAMERA_CADENCE_S
assert c.max_cameras_at_cadence(36.0) == 6
print(f"nest quotas list={c.DEFAULT_LIST_CADENCE_S}s camera={c.DEFAULT_CAMERA_CADENCE_S}s maxCameras=6 OK")
PYGATE

echo "OK ci_static_gates"
