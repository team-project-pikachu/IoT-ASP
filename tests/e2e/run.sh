#!/usr/bin/env bash
# Playwright smoke for the public blaster. Serves ../../public on 127.0.0.1:8765 and runs the spec.
# Browsers come from PLAYWRIGHT_BROWSERS_PATH (default /opt/pw-browsers); never runs `playwright install`
# locally (CI may, see docs/specs/01-m0-public-blaster.md → CI gate).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}"
# @playwright/test@1.56.1 needs chromium / chromium_headless_shell build 1194 under that path.
# Local Mac: PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" make e2e
# If headless_shell-1194 is missing, tests/e2e/playwright.config.mjs falls back to full Chromium 1194.
PORT="${E2E_PORT:-8765}"
cd "$ROOT/tests/e2e"

npm ci --no-audit --no-fund 2>/dev/null || npm i --no-audit --no-fund

python3 -m http.server "$PORT" --directory ../../public --bind 127.0.0.1 >.server.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 20); do
  if curl -sf "http://127.0.0.1:$PORT/index.html" >/dev/null; then break; fi
  sleep 0.25
done
curl -sf "http://127.0.0.1:$PORT/index.html" >/dev/null || { echo "FAIL: http.server did not come up on $PORT" >&2; exit 1; }

set +e
E2E_PORT="$PORT" npx playwright test "$@"
RC=$?
set -e
if [[ $RC -eq 0 ]]; then echo "OK e2e"; fi
exit $RC
