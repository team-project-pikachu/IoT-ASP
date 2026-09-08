#!/usr/bin/env bash
# Deterministic verification for issue #13 design sketch (no prod non-Gemini).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

test -f docs/multi-llm-registry.md
test -f .vv/13/EVIDENCE.md
rg -q 'LlmRegistry|LlmProvider' docs/multi-llm-registry.md
rg -q 'validate_patch' docs/multi-llm-registry.md
rg -q 'ALLOW_METERED_TIER' docs/multi-llm-registry.md
rg -q 'gemini-vertex|Gemini' docs/multi-llm-registry.md
! test -f services/autoroute-adk/iot_asp_autoroute/llm_registry.py
! test -f services/autoroute-adk/iot_asp_autoroute/providers.py
echo "V13 VERIFY OK"
