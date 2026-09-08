#!/usr/bin/env bash
# Deterministic verification for issue #9 research ACs (no entitlement work).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

test -f docs/sensorkit-research-closeout.md
test -f docs/sensors-chrome-ios.md
test -f .vv/9/EVIDENCE.md
rg -q 'cannot use SensorKit|Web cannot' docs/sensorkit-research-closeout.md
rg -q '#14' docs/sensorkit-research-closeout.md
rg -q '#15' docs/sensorkit-research-closeout.md
rg -q '#18' docs/sensorkit-research-closeout.md
rg -q 'com\.apple\.developer\.sensorkit\.reader\.allow' docs/sensorkit-research-closeout.md
rg -q 'SensorKit' public/index.html
echo "V9 VERIFY OK"
