#!/usr/bin/env bash
# #26 Colab / GCS features — dry-run → fixture path (never invents credentials).
# Usage:
#   bash scripts/colab_gcs_fixture.sh            # regenerate under .autoroute-dry + print summary
#   bash scripts/colab_gcs_fixture.sh --check    # hermetic temp dry root; full golden compare
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX_DIR="${ROOT}/fixtures/colab_gcs"
MODE="${1:-run}"
export PYTHONPATH="${ROOT}/services/autoroute-adk${PYTHONPATH:+:$PYTHONPATH}"
export IOT_ASP_AUTOROUTE_DRY_RUN=1

if [[ "${LIVE_GCS:-0}" == "1" ]]; then
  echo "Refusing: this script is dry-run/fixture only. Use notebooks/iot_asp_colab_etl.md for LIVE_GCS=1 (owner)." >&2
  exit 2
fi

# --check must be hermetic: never reuse a polluted .autoroute-dry tree.
if [[ "$MODE" == "--check" ]]; then
  DRY_TMP="$(mktemp -d "${TMPDIR:-/tmp}/iot-asp-colab-gcs.XXXXXX")"
  trap 'rm -rf "$DRY_TMP"' EXIT
  export IOT_ASP_AUTOROUTE_DRY_ROOT="$DRY_TMP"
else
  export IOT_ASP_AUTOROUTE_DRY_ROOT="${IOT_ASP_AUTOROUTE_DRY_ROOT:-${ROOT}/.autoroute-dry}"
  mkdir -p "$IOT_ASP_AUTOROUTE_DRY_ROOT"
fi
mkdir -p "$FIX_DIR"

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
# Hermetic root ⇒ exactly one feature object from this seed run.
assert len(cands) == 1, f"expected 1 feature file in hermetic dry root, got {len(cands)}: {cands}"
got = json.loads(cands[0].read_text())
# Seeded record is deterministic — compare the complete parsed document
# (sensors, derived, telemetry, anomaly, shriekBias, …), not metadata alone.
assert got == golden, (
    "golden mismatch keys/diff",
    {k: (got.get(k), golden.get(k)) for k in sorted(set(got) | set(golden)) if got.get(k) != golden.get(k)},
)
print("OK fixture check vs fixtures/colab_gcs/features_node1_seed26.json (full document)")
PY
fi
