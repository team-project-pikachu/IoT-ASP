#!/usr/bin/env bash
# #26 Colab / GCS features — dry-run → fixture path (never invents credentials).
# Usage:
#   bash scripts/colab_gcs_fixture.sh            # regenerate under .autoroute-dry + print summary
#   bash scripts/colab_gcs_fixture.sh --check    # compare writer/sourceCount/sensorColumns to golden fixture
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX_DIR="${ROOT}/fixtures/colab_gcs"
MODE="${1:-run}"
export PYTHONPATH="${ROOT}/services/autoroute-adk${PYTHONPATH:+:$PYTHONPATH}"
export IOT_ASP_AUTOROUTE_DRY_RUN=1
export IOT_ASP_AUTOROUTE_DRY_ROOT="${IOT_ASP_AUTOROUTE_DRY_ROOT:-${ROOT}/.autoroute-dry}"
mkdir -p "$IOT_ASP_AUTOROUTE_DRY_ROOT" "$FIX_DIR"

if [[ "${LIVE_GCS:-0}" == "1" ]]; then
  echo "Refusing: this script is dry-run/fixture only. Use notebooks/iot_asp_colab_etl.md for LIVE_GCS=1 (owner)." >&2
  exit 2
fi

echo "# dry-run root: $IOT_ASP_AUTOROUTE_DRY_ROOT"
echo "# secret names only: LIVE_GCS IOT_ASP_GCS_BUCKET GCP_SA_JSON GOOGLE_CLOUD_PROJECT (values never printed)"
OUT="$(python3 -m iot_asp_autoroute.features_live --node node1 --limit 50 --seed-demo)"
echo "$OUT" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(json.dumps({k:r.get(k) for k in ("ok","sourceCount","written","live","node","error")}, sort_keys=True))'

if [[ "$MODE" == "--check" ]]; then
  export ROOT
  export DRY_ROOT="$IOT_ASP_AUTOROUTE_DRY_ROOT"
  python3 - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ["ROOT"])
dry = Path(os.environ["DRY_ROOT"]) / "meta/features/node1"
golden = json.loads((root / "fixtures/colab_gcs/features_node1_seed26.json").read_text())
cands = sorted(dry.glob("*.json"))
assert cands, f"no features under {dry}"
got = json.loads(cands[-1].read_text())
for key in ("writer", "schemaVersion", "kind", "micDiffAlpha", "sourceCount"):
    assert got.get(key) == golden.get(key), (key, got.get(key), golden.get(key))
assert got.get("sensorColumns") == golden.get("sensorColumns")
pol = got.get("credentialPolicy")
assert pol == golden.get("credentialPolicy"), pol
assert "userdata" in str(pol).lower() or "env" in str(pol).lower() or "name" in str(pol).lower()
print("OK fixture check vs fixtures/colab_gcs/features_node1_seed26.json")
PY
fi
